# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Input core runtime contracts. 输入核心运行时合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "InputCore.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "input-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int expectedWidth: Enums.controlSize.inputDefaultWidth
    readonly property int expectedHeight: Enums.controlSize.inputHeight
    readonly property real inputBorderWidth: input.border.width
    readonly property color expectedDefaultColor: Enums.stateColor.controlBg
    readonly property color expectedDisabledColor: Enums.stateColor.controlBgDisabled
    readonly property color expectedDisabledText: Enums.textColor.disabled
    readonly property color expectedTransparent: Enums.transparent

    width: 440
    height: 260
    visible: true

    MouseArea {
        anchors.fill: parent
        onClicked: editor.focus = false
    }

    InputCore {
        id: input
        objectName: "input"
        x: 60
        y: 70
        focusTarget: editor
        focused: editor.activeFocus

        TextInput {
            id: editor
            objectName: "editor"
            x: input.paddingLeft
            y: input.paddingTop
            width: input.width - input.paddingLeft - input.paddingRight
            height: input.height - input.paddingTop - input.paddingBottom
            activeFocusOnTab: true
            text: "Prism"
        }
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


def _rgba(value) -> tuple[int, int, int, int]:
    color = QColor(value)
    return color.red(), color.green(), color.blue(), color.alpha()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _focus_line(control: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _visual_descendants(control)
        if child.metaObject().indexOfProperty("showLine") >= 0
        and child.metaObject().indexOfProperty("parentRadius") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _local_point(window: QQuickWindow, item: QQuickItem, x: float, y: float) -> QPoint:
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


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
    control = window.findChild(QQuickItem, "input")
    editor = window.findChild(QQuickItem, "editor")
    assert control is not None
    assert editor is not None
    return engine, component, window, control, editor, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _assert_size_and_style(window, control) -> None:
    assert control.property("contentWidth") == window.property("expectedWidth")
    assert control.property("contentHeight") == window.property("expectedHeight")
    assert control.width() == window.property("expectedWidth")
    assert control.height() == window.property("expectedHeight")
    assert control.property("paddingLeft") == 12
    assert control.property("paddingRight") == 8
    assert control.property("paddingTop") == 6
    assert control.property("paddingBottom") == 6
    assert _rgba(control.property("color")) == _rgba(window.property("expectedDefaultColor"))
    control.setProperty("preferredWidth", 280)
    control.setProperty("preferredHeight", 50)
    assert _wait_for(lambda: control.width() == 280 and control.height() == 50)


def _assert_focus_and_padding_click(window, control, editor) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, editor),
    )
    assert _wait_for(lambda: editor.property("activeFocus"))
    assert control.property("focused")
    assert _focus_line(control).property("showLine")
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _local_point(window, control, 2, control.height() / 2),
    )
    assert editor.property("activeFocus")
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(410, 230))
    assert _wait_for(lambda: not editor.property("activeFocus"))


def _assert_disabled_and_transparent(window, control) -> None:
    control.setProperty("enabled", False)
    assert _rgba(control.property("color")) == _rgba(window.property("expectedDisabledColor"))
    assert _rgba(control.property("inputTextColor")) == _rgba(
        window.property("expectedDisabledText")
    )
    control.setProperty("enabled", True)
    control.setProperty("transparentBackground", True)
    assert _rgba(control.property("color")) == _rgba(window.property("expectedTransparent"))
    assert window.property("inputBorderWidth") == 0


def _assert_edit_action_contract(control, editor) -> None:
    clipboard = QGuiApplication.clipboard()
    previous_clipboard = clipboard.text()
    try:
        control.selectAll()
        assert editor.property("selectedText") == "Prism"
        control.copy()
        assert clipboard.text() == "Prism"
        control.cut()
        assert editor.property("text") == ""
        control.undo()
        assert editor.property("text") == "Prism"
        control.redo()
        assert editor.property("text") == ""
        clipboard.setText("PrismQML")
        control.paste()
        assert editor.property("text") == "PrismQML"
        control.clear()
        assert editor.property("text") == ""
    finally:
        clipboard.setText(previous_clipboard)


def test_input_core_size_focus_padding_and_visual_states(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, control, editor, warnings = _create_scene()
    try:
        _assert_size_and_style(window, control)
        _assert_focus_and_padding_click(window, control, editor)
        _assert_disabled_and_transparent(window, control)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_input_core_edit_action_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, control, editor, warnings = _create_scene()
    try:
        _assert_edit_action_contract(control, editor)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_input_core_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
