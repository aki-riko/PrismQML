# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window close-animation prewarm regressions. 窗口关闭动画预热回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
ANIMATION_HELPER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowAnimationHelper.qml"
)
DISSOLVE_EFFECT_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowCloseDissolve.qml"
)
CAPTION_BUTTON_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "CaptionButton.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "window-close-animation-prewarm.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/_internal" as Internal

Window {
    id: window
    property int closeCallbacks: 0
    property int hoverPrewarmCalls: 0

    width: 320
    height: 200
    visible: false

    QtObject {
        id: hoverTarget
        function prewarmCloseAnimation() { window.hoverPrewarmCalls += 1 }
    }

    Rectangle {
        id: frame
        anchors.fill: parent
        color: Enums.cardColor
        radius: Enums.radius.large
    }

    Internal.WindowAnimationHelper {
        id: animationHelper
        objectName: "animationHelper"
        targetWindow: window
        targetItem: frame
        closeCornerRadius: frame.radius
        onCloseCallback: function() { window.closeCallbacks += 1 }
    }

    Internal.CaptionButton {
        objectName: "closeCaptionButton"
        targetWindow: hoverTarget
        iconType: "close"
    }
}
"""


class _FakeNativeTransition(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.succeed = True
        self.maximize_calls = 0
        self.restore_calls = 0

    @Slot(QObject, result=bool)
    def requestMaximize(self, _window):
        self.maximize_calls += 1
        return self.succeed

    @Slot(QObject, result=bool)
    def requestRestore(self, _window):
        self.restore_calls += 1
        return self.succeed


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _class_count(root: QObject, prefix: str) -> int:
    return sum(
        child.metaObject().className().startswith(prefix)
        for child in root.findChildren(QObject)
    )


def _visual_items(root: QQuickItem):
    for child in root.childItems():
        yield child
        yield from _visual_items(child)


def _visual_class_count(root: QQuickItem, prefix: str) -> int:
    return sum(
        child.metaObject().className().startswith(prefix)
        for child in _visual_items(root)
    )


@pytest.fixture
def close_animation_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    native_transition = _FakeNativeTransition(engine)
    engine.rootContext().setContextProperty(
        "NativeWindow", native_transition
    )
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    try:
        yield window, warnings, native_transition
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()


def test_close_animation_is_absent_at_startup_and_programmatic_close_loads_it(
    close_animation_scene,
):
    window, warnings, _native_transition = close_animation_scene
    helper = window.findChild(QQuickItem, "animationHelper")
    assert helper is not None
    window.show()
    assert _wait_for(lambda: helper.width() == pytest.approx(window.width()))
    assert _class_count(helper, "QQuickSequentialAnimation") == 0

    window.setOpacity(1)
    helper.setProperty("animScale", 1)
    helper.setProperty("animOpacity", 1)
    assert QMetaObject.invokeMethod(
        helper, "animatedClose", Qt.ConnectionType.DirectConnection
    )
    assert _class_count(helper, "QQuickSequentialAnimation") > 1
    dissolve = helper.findChild(QQuickItem, "windowCloseDissolve")
    assert dissolve is not None
    overlay = dissolve.findChild(QQuickWindow, "windowCloseOverlayWindow")
    assert overlay is not None
    frozen_frame = overlay.findChild(QQuickItem, "windowCloseFrozenFrame")
    assert frozen_frame is not None
    assert _visual_class_count(helper, "QQuickShaderEffectSource") == 0
    grid_cells = {
        child.objectName(): child
        for child in _visual_items(overlay.contentItem())
        if child.objectName().startswith("windowCloseGridCell_")
    }
    assert len(grid_cells) == dissolve.property("_cellCount")
    columns = dissolve.property("_columns")
    rows = dissolve.property("_rows")
    center_index = (rows // 2) * columns + columns // 2
    center_cell = grid_cells[f"windowCloseGridCell_{center_index}"]
    corner_cell = grid_cells["windowCloseGridCell_0"]
    assert _wait_for(lambda: helper.property("animOpacity") == 0)
    assert overlay.isVisible()
    assert window.opacity() == pytest.approx(0)
    _pump(120)
    assert frozen_frame.opacity() < 1
    assert center_cell.opacity() < corner_cell.opacity()
    assert window.property("closeCallbacks") == 0
    assert _wait_for(lambda: window.property("closeCallbacks") == 1)
    assert window.opacity() == pytest.approx(0)
    assert not overlay.isVisible()
    assert helper.property("animScale") == pytest.approx(1)
    assert helper.property("animOpacity") == pytest.approx(0)
    assert warnings == []


def test_close_dissolve_can_be_cancelled_and_restarted(close_animation_scene):
    window, warnings, _native_transition = close_animation_scene
    helper = window.findChild(QQuickItem, "animationHelper")
    assert helper is not None
    window.show()
    assert _wait_for(lambda: helper.width() == pytest.approx(window.width()))
    window.setOpacity(1)
    helper.setProperty("animScale", 1)
    helper.setProperty("animOpacity", 1)

    assert QMetaObject.invokeMethod(
        helper, "animatedClose", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(lambda: helper.property("animOpacity") == 0)
    assert QMetaObject.invokeMethod(
        helper, "restoreVisibleState", Qt.ConnectionType.DirectConnection
    )
    assert window.property("closeCallbacks") == 0
    assert window.opacity() == pytest.approx(1)
    assert helper.property("animScale") == pytest.approx(1)
    assert helper.property("animOpacity") == pytest.approx(1)
    dissolve = helper.findChild(QQuickItem, "windowCloseDissolve")
    overlay = dissolve.findChild(QQuickWindow, "windowCloseOverlayWindow")
    assert not overlay.isVisible()

    assert QMetaObject.invokeMethod(
        helper, "animatedClose", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(lambda: window.property("closeCallbacks") == 1)
    assert window.opacity() == pytest.approx(0)
    assert warnings == []


def test_close_caption_entered_prewarms_without_clicking(close_animation_scene):
    window, warnings, _native_transition = close_animation_scene
    caption = window.findChild(QQuickItem, "closeCaptionButton")
    assert caption is not None
    mouse_areas = [
        child
        for child in caption.findChildren(QObject)
        if child.metaObject().className().startswith("QQuickMouseArea")
    ]
    assert len(mouse_areas) == 1
    assert window.property("hoverPrewarmCalls") == 0
    assert QMetaObject.invokeMethod(
        mouse_areas[0], "entered", Qt.ConnectionType.DirectConnection
    )
    assert window.property("hoverPrewarmCalls") == 1
    assert window.property("closeCallbacks") == 0
    assert warnings == []


def test_close_animation_source_uses_splash_grid_dissolve():
    animation_source = ANIMATION_HELPER_PATH.read_text(encoding="utf-8")
    dissolve_source = DISSOLVE_EFFECT_PATH.read_text(encoding="utf-8")
    caption_source = CAPTION_BUTTON_PATH.read_text(encoding="utf-8")
    assert "active: false" in animation_source
    assert "sourceComponent: WindowCloseDissolve" in animation_source
    assert "targetItem: helper.targetItem" in animation_source
    assert "cornerRadius: helper.closeCornerRadius" in animation_source
    assert "helper.animOpacity = Enums.opacityLevel.invisible" in animation_source
    assert 'objectName: "windowCloseOverlayWindow"' in dissolve_source
    assert "transientParent: null" in dissolve_source
    assert "overlayWindow.requestUpdate()" in dissolve_source
    assert "AcrylicHelper.grabWindowFrame" in dissolve_source
    assert "targetItem.grabToImage" in dissolve_source
    assert "Repeater {" in dissolve_source
    assert "delegate: Item" in dissolve_source
    assert "delegate: ShaderEffectSource" not in dissolve_source
    assert "ShaderEffectSource {" not in dissolve_source
    assert 'objectName: "windowCloseFrozenFrame"' in dissolve_source
    assert 'objectName: "windowCloseGridCell_" + index' in dissolve_source
    assert "x: -gridCell.x" in dissolve_source
    assert "sourceClipRect:" not in dissolve_source
    assert "targetWindow.opacity = Enums.opacityLevel.invisible" in dissolve_source
    assert "Enums.duration.splashGridContentFade" in dissolve_source
    assert "Enums.duration.splashGridDelayStep" in dissolve_source
    assert "Enums.duration.splashGridCellFade" in dissolve_source
    assert "Enums.duration.splashExitDissolve" in dissolve_source
    assert "Enums.splashScreenMetrics.exitContentEndScale" in dissolve_source
    assert "Enums.splashScreenMetrics.exitGridColumns" in dissolve_source
    assert "Enums.splashScreenMetrics.exitGridRows" in dissolve_source
    assert "onCloseCallback()" in dissolve_source
    assert (
        "if (captionBtn.isClose) "
        "captionBtn.targetWindow.prewarmCloseAnimation()"
    ) in caption_source


def test_maximize_and_restore_prefer_native_dwm_transition(
    close_animation_scene,
):
    window, warnings, native_transition = close_animation_scene
    helper = window.findChild(QQuickItem, "animationHelper")
    assert helper is not None

    assert QMetaObject.invokeMethod(
        helper, "animatedMaximize", Qt.ConnectionType.DirectConnection
    )
    assert QMetaObject.invokeMethod(
        helper, "animatedRestore", Qt.ConnectionType.DirectConnection
    )

    assert native_transition.maximize_calls == 1
    assert native_transition.restore_calls == 1
    assert window.visibility() == QQuickWindow.Visibility.Hidden
    assert warnings == []


def test_maximize_and_restore_keep_qt_fallback(close_animation_scene):
    window, warnings, native_transition = close_animation_scene
    helper = window.findChild(QQuickItem, "animationHelper")
    assert helper is not None
    native_transition.succeed = False

    assert QMetaObject.invokeMethod(
        helper, "animatedMaximize", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(
        lambda: window.visibility() == QQuickWindow.Visibility.Maximized
    )
    assert QMetaObject.invokeMethod(
        helper, "animatedRestore", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(
        lambda: window.visibility() == QQuickWindow.Visibility.Windowed
    )

    assert native_transition.maximize_calls == 1
    assert native_transition.restore_calls == 1
    assert warnings == []
