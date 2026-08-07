# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public Flickable and TextEdit smooth-wheel contracts. 公开 Flickable 与 TextEdit 平滑滚轮合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPoint, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Flickable.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "TextEdit"
    / "TextEditCore.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "public-smooth-scroll-surfaces.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers" as Containers

Window {
    width: 560
    height: 260
    visible: true

    Containers.Flickable {
        id: basicFlickable
        objectName: "basicFlickable"
        x: 30
        y: 30
        width: 220
        height: 180
        contentWidth: width
        contentHeight: basicContent.height

        Item {
            id: basicContent
            width: basicFlickable.width
            height: 720
        }
    }

    TextEdit {
        id: textEdit
        objectName: "textEdit"
        x: 310
        y: 30
        width: 220
        height: 180
        text: "line 01\\nline 02\\nline 03\\nline 04\\nline 05\\nline 06\\nline 07\\nline 08\\nline 09\\nline 10\\nline 11\\nline 12\\nline 13\\nline 14\\nline 15\\nline 16\\nline 17\\nline 18\\nline 19\\nline 20"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _smooth_scroll_helper(control):
    matches = [
        child
        for child in _descendants(control)
        if "SmoothScrollHelper" in child.metaObject().className()
    ]
    assert len(matches) == 1
    return matches[0]


def _text_flickable(control):
    matches = [
        child
        for child in control.childItems()
        if child.metaObject().indexOfProperty("contentY") >= 0
        and child.metaObject().indexOfProperty("boundsBehavior") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _send_wheel(window: QQuickWindow, item: QQuickItem, delta: int) -> QWheelEvent:
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    global_position = QPointF(window.x() + position.x(), window.y() + position.y())
    event = QWheelEvent(
        position,
        global_position,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene():
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
    _pump()
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in ("basicFlickable", "textEdit")
    }
    assert all(controls.values())
    return engine, component, window, controls, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _assert_real_wheel_animation(window, control, viewport) -> None:
    helper = _smooth_scroll_helper(control)
    assert helper.property("enabled")
    assert viewport.property("contentHeight") > viewport.height()
    viewport.setProperty("contentY", 0)
    assert QCoreApplication.processEvents() is None
    event = _send_wheel(window, viewport, -120)
    assert event.isAccepted()
    target = helper.property("targetPos")
    assert target > 0
    assert 0 <= viewport.property("contentY") < target
    assert _wait_for(lambda: viewport.property("contentY") == pytest.approx(target))


@pytest.mark.parametrize("surface", ["basicFlickable", "textEdit"])
def test_public_scroll_surfaces_animate_real_wheel_input(qapp, surface):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        control = controls[surface]
        viewport = control if surface == "basicFlickable" else _text_flickable(control)
        _assert_real_wheel_animation(window, control, viewport)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_public_scroll_surface_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = [
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        ]
        assert violations == []
