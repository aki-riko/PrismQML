# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Expander and GroupBox runtime contracts. Expander 与 GroupBox 运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Expander"
    / "ExpanderCore.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Expander"
    / "GroupBox.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "expander-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property bool expanderState: expander.isExpanded()
    readonly property bool groupState: groupBox.isChecked()
    readonly property string groupTitle: groupBox.getTitle()
    readonly property real disabledOpacity: Enums.opacityLevel.disabled

    function resetGroup() {
        groupBox.setChecked(true)
    }

    width: 720
    height: 420
    visible: true

    Expander {
        id: expander
        objectName: "expander"
        x: 20
        y: 20
        width: 320
        title: "Details"
        content: "Description"

        Rectangle {
            objectName: "expandedChild"
            width: 120
            height: 40
        }
    }

    GroupBox {
        id: groupBox
        objectName: "groupBox"
        x: 380
        y: 20
        width: 260
        height: 150
        title: "Options"
        checkable: true
        checked: true

        Rectangle {
            objectName: "groupChild"
            width: 100
            height: 40
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
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
    assert isinstance(window, QQuickWindow)
    expander = window.findChild(QQuickItem, "expander")
    group_box = window.findChild(QQuickItem, "groupBox")
    _pump()
    return engine, component, window, expander, group_box, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def expander_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_expander_methods_animation_and_header_click(expander_scene):
    window, expander, _group_box, warnings, windows_before = expander_scene
    toggled = []
    expander.toggled.connect(toggled.append)
    collapsed_height = expander.height()
    assert not window.property("expanderState")

    assert QMetaObject.invokeMethod(expander, "toggle")
    assert _wait_for(lambda: window.property("expanderState"))
    assert _wait_for(lambda: expander.height() > collapsed_height)
    assert toggled == [True]

    assert QMetaObject.invokeMethod(expander, "collapse")
    assert _wait_for(lambda: not window.property("expanderState"))
    assert _wait_for(lambda: expander.height() == pytest.approx(collapsed_height))
    assert toggled == [True]

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(120, 50))
    assert _wait_for(lambda: window.property("expanderState"))
    assert toggled == [True, True]
    expander.setProperty("disabled", True)
    assert QMetaObject.invokeMethod(expander, "collapse")
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(120, 50))
    _pump()
    assert not window.property("expanderState")
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_group_box_checkbox_controls_content(expander_scene):
    window, _expander, group_box, warnings, windows_before = expander_scene
    content_area = group_box.findChild(QQuickItem, "contentArea")
    toggled = []
    clicked = []
    group_box.toggled.connect(toggled.append)
    group_box.clicked.connect(clicked.append)
    assert window.property("groupState")
    assert window.property("groupTitle") == "Options"
    assert content_area.isEnabled()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(group_box.x() + 24, group_box.y() + 10),
    )
    assert _wait_for(lambda: not window.property("groupState"))
    assert not window.property("groupState")
    assert not content_area.isEnabled()
    assert content_area.opacity() == pytest.approx(window.property("disabledOpacity"))
    assert toggled == [False]
    assert clicked == [False]
    assert QMetaObject.invokeMethod(window, "resetGroup")
    _pump()
    assert window.property("groupState")
    assert content_area.isEnabled()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_expander_sources_follow_conventions():
    violations = []
    for source_path in SOURCE_PATHS:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
