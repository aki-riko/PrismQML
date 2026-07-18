# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Normal line-edit parent-chain regressions. 普通输入框父链回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "LineEdit"
    / "LineEditNormal.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "line-edit-normal-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int normalEcho: TextInput.Normal
    readonly property int passwordEcho: TextInput.Password
    readonly property int expectedClearButtonSize: Enums.controlSize.lineEditClearButtonSize

    width: 560
    height: 260
    visible: true

    LineEdit {
        objectName: "normalInput"
        x: 40
        y: 30
        width: 260
        inputType: Enums.input.type_normal
        text: "Alpha"
    }

    LineEdit {
        objectName: "passwordInput"
        x: 40
        y: 100
        width: 260
        inputType: Enums.input.type_password
        text: "secret"
    }

    LineEdit {
        objectName: "searchInput"
        x: 40
        y: 170
        inputType: Enums.input.type_search
        collapsible: true
        collapsedWidth: 32
        expandedWidth: 220
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


def _descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _normal_module(line_edit: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _descendants(line_edit)
        if isinstance(child, QQuickItem)
        and child.metaObject().indexOfProperty("_actualEchoMode") >= 0
        and child.metaObject().indexOfProperty("_isCollapsedSearch") >= 0
        and child.metaObject().indexOfMethod("clear()") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _clear_button(normal_module: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _descendants(normal_module)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("CloseButton")
        and child.metaObject().indexOfProperty("iconSizeValue") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _action_button(normal_module: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _descendants(normal_module)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("InputActionButton")
        and child.metaObject().indexOfProperty("collapsedSize") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, item),
    )


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
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    inputs = {
        name: window.findChild(QQuickItem, name)
        for name in ("normalInput", "passwordInput", "searchInput")
    }
    assert all(inputs.values())
    return engine, component, window, inputs, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_line_edit_normal_password_search_parent_chains(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, inputs, warnings = _create_scene()
    try:
        normal = _normal_module(inputs["normalInput"])
        clear_button = _clear_button(normal)
        cleared = []
        inputs["normalInput"].cleared.connect(lambda: cleared.append(True))
        assert clear_button.property("size") == window.property("expectedClearButtonSize")
        assert clear_button.property("visible")
        _click(window, clear_button)
        _pump()
        assert inputs["normalInput"].property("text") == ""
        assert cleared == [True]
        assert not clear_button.property("visible")

        password = _normal_module(inputs["passwordInput"])
        password_action = _action_button(password)
        assert password.property("_actualEchoMode") == window.property("passwordEcho")
        _click(window, password_action)
        _pump()
        assert password.property("_actualEchoMode") == window.property("normalEcho")
        _click(window, password_action)
        _pump()
        assert password.property("_actualEchoMode") == window.property("passwordEcho")

        search = _normal_module(inputs["searchInput"])
        search_action = _action_button(search)
        searched = []
        inputs["searchInput"].searched.connect(searched.append)
        assert not search.property("expanded")
        assert search_action.property("collapsed")
        _click(window, search_action)
        assert _wait_for(lambda: search.property("expanded"))
        inputs["searchInput"].setProperty("text", "needle")
        _pump()
        _click(window, search_action)
        _pump()
        assert searched == ["needle"]
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_collapsible_search_animates_width_and_keeps_action_height(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, inputs, warnings = _create_scene()
    search_control = inputs["searchInput"]
    search_module = _normal_module(search_control)
    search_action = _action_button(search_module)
    try:
        collapsed_width = search_control.width()
        expanded_width = search_control.property("expandedWidth")
        assert collapsed_width < expanded_width
        assert search_action.height() == pytest.approx(search_control.height())

        _click(window, search_action)
        _pump(50)

        animated_width = search_control.width()
        assert collapsed_width < animated_width < expanded_width
        assert _wait_for(lambda: search_control.width() == pytest.approx(expanded_width))
        assert search_action.height() == pytest.approx(search_control.height())
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_normal_source_conventions_and_clear_button_token():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "size: Enums.controlSize.lineEditClearButtonSize" in source
    assert "size: 20" not in source
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int lineEditClearButtonSize: 20" in metrics
