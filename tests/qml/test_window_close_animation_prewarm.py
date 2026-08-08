# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window close-animation prewarm regressions. 窗口关闭动画预热回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QEventLoop, QMetaObject, QObject, Qt, QTimer, QUrl
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
        yield window, warnings
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
    window, warnings = close_animation_scene
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
    ripple_mask_content = overlay.findChild(
        QQuickItem, "windowCloseRippleMaskContent"
    )
    ripple_mask = overlay.findChild(QQuickItem, "windowCloseRippleMask")
    ripple_mask_texture = overlay.findChild(
        QQuickItem, "windowCloseRippleMaskTexture"
    )
    dissolve_frame = overlay.findChild(QQuickItem, "windowCloseDissolveFrame")
    assert ripple_mask_content is not None
    assert ripple_mask is not None
    assert ripple_mask_texture is not None
    assert dissolve_frame is not None
    assert _visual_class_count(overlay.contentItem(), "QQuickImage") == 2
    assert _visual_class_count(ripple_mask_content, "QQuickShape") == 1
    assert _class_count(ripple_mask, "QQuickPathAngleArc") == 7
    assert _visual_class_count(overlay.contentItem(), "QQuickShaderEffectSource") == 1
    assert ripple_mask.width() == pytest.approx(overlay.width())
    assert ripple_mask.height() == pytest.approx(overlay.height())
    assert _wait_for(lambda: helper.property("animOpacity") == 0)
    assert overlay.isVisible()
    assert window.opacity() == pytest.approx(0)
    assert not frozen_frame.isVisible()
    _pump(120)
    assert frozen_frame.opacity() == pytest.approx(1)
    assert frozen_frame.scale() == pytest.approx(1)
    assert 0 < dissolve.property("_dissolveProgress") < 1
    assert dissolve.property("_rippleFrontRadius") == pytest.approx(
        dissolve.property("_rippleMaskDiameter")
        * dissolve.property("_dissolveProgress")
        / 2
    )
    assert dissolve.property("_ripplePeriod") > 0
    ripple_radii = [ripple_mask.property(f"_radius{index}") for index in range(7)]
    assert ripple_radii == sorted(ripple_radii, reverse=True)
    assert ripple_radii[-1] >= 0
    assert window.property("closeCallbacks") == 0
    assert _wait_for(lambda: window.property("closeCallbacks") == 1)
    assert window.opacity() == pytest.approx(0)
    assert not overlay.isVisible()
    assert helper.property("animScale") == pytest.approx(1)
    assert helper.property("animOpacity") == pytest.approx(0)
    assert warnings == []


def test_close_dissolve_can_be_cancelled_and_restarted(close_animation_scene):
    window, warnings = close_animation_scene
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
    window, warnings = close_animation_scene
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


def test_close_animation_source_uses_ripple_mask():
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
    assert "MultiEffect {" in dissolve_source
    assert "import QtQuick.Shapes" in dissolve_source
    assert 'objectName: "windowCloseRippleMaskContent"' in dissolve_source
    assert 'objectName: "windowCloseRippleMask"' in dissolve_source
    assert 'objectName: "windowCloseRippleMaskTexture"' in dissolve_source
    assert 'objectName: "windowCloseDissolveFrame"' in dissolve_source
    assert "Shape {" in dissolve_source
    assert "ShapePath {" in dissolve_source
    assert "fillRule: ShapePath.OddEvenFill" in dissolve_source
    assert dissolve_source.count("PathAngleArc {") == 7
    assert "Math.sin(Math.PI * _dissolveProgress)" in dissolve_source
    assert "Repeater {" not in dissolve_source
    assert "delegate: ShaderEffectSource" not in dissolve_source
    assert dissolve_source.count("ShaderEffectSource {") == 1
    assert "hideSource: true" in dissolve_source
    assert "live: true" in dissolve_source
    assert "maskInverted" not in dissolve_source
    assert "maskThresholdMin: Enums.mask.thresholdMin" in dissolve_source
    assert "maskSpreadAtMin: Enums.mask.spreadFull" in dissolve_source
    assert 'objectName: "windowCloseFrozenFrame"' in dissolve_source
    assert "sourceClipRect:" not in dissolve_source
    assert "color: Enums.transparent" in dissolve_source
    assert "targetWindow.opacity = Enums.opacityLevel.invisible" in dissolve_source
    assert "Enums.duration.splashExitDissolve" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleDiameterOvershoot" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleDropRadius" in dissolve_source
    assert "Enums.windowCloseMetrics.ripplePeriodRatio" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleGapRatio" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleFullCircleSweep" in dissolve_source
    assert dissolve_source.count("Image {") == 2
    assert "Easing.OutQuad" in dissolve_source
    assert "onCloseCallback()" in dissolve_source
    assert (
        "if (captionBtn.isClose) "
        "captionBtn.targetWindow.prewarmCloseAnimation()"
    ) in caption_source
