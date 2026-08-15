# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""LineEditCore public method contracts. 单行输入核心公共方法合同。"""

from pathlib import Path, PurePosixPath

import pytest
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
    / "LineEditCore.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "line-edit-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int normalType: Enums.input.type_normal
    readonly property int labelType: Enums.input.type_label
    readonly property int searchType: Enums.input.type_search
    readonly property int tagType: Enums.input.type_tag
    readonly property int defaultInputWidth: Enums.controlSize.inputDefaultWidth
    readonly property int labelInputWidth: Enums.controlSize.lineEditLabelWidth
    readonly property int tagInputWidth: Enums.controlSize.lineEditTagWidth
    readonly property int controlAlignment: control.textInput
        ? control.textInput.horizontalAlignment : -1

    width: 760
    height: 360
    visible: true

    LineEdit {
        id: control
        objectName: "control"
        x: 60
        y: 50
        text: "Alpha"
        placeholderText: "Input"
    }

    LineEdit {
        objectName: "labelControl"
        x: 60
        y: 130
        inputType: Enums.input.type_label
        label: "Account"
        text: "Label text"
    }

    LineEdit {
        objectName: "tagControl"
        x: 60
        y: 220
        inputType: Enums.input.type_tag
        tags: ["one"]
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


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _text_input(control: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(control)
        if item.metaObject().className().startswith("QQuickTextInput")
        and item.metaObject().indexOfProperty("horizontalAlignment") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _visible_descendant(control: QQuickItem, class_prefix: str) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(control)
        if item.metaObject().className().startswith(class_prefix) and item.isVisible()
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


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


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


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
    window.requestActivate()
    assert _wait_for(window.isActive)
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in ("control", "labelControl", "tagControl")
    }
    assert all(controls.values())
    assert _wait_for(lambda: all(item.property("textInput") for item in controls.values()))
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


def test_line_edit_core_focus_selection_alignment_and_edit_sync(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    control = controls["control"]
    text_input = _text_input(control)
    edited = []
    control.textEdited.connect(edited.append)
    try:
        control.setText("Beta")
        assert _wait_for(lambda: text_input.property("text") == "Beta")
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=_point_for(window, text_input))
        assert _wait_for(lambda: bool(text_input.property("activeFocus")))
        control.selectAll()
        assert control.property("selectedText") == "Beta"
        control.setAlignment(int(Qt.AlignmentFlag.AlignRight))
        assert window.property("controlAlignment") == Qt.AlignmentFlag.AlignRight
        assert control.inputHasFocus()
        assert control.property("focused")

        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(window, Qt.Key.Key_Z)
        assert _wait_for(lambda: control.property("text") == "z")
        assert edited[-1] == "z"
        control.undo()
        assert _wait_for(lambda: control.property("text") == "Beta")
        control.redo()
        assert _wait_for(lambda: control.property("text") == "z")
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_core_type_switch_preserves_text_and_generic_methods(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    control = controls["control"]
    try:
        assert control.property("expandedWidth") == window.property("defaultInputWidth")
        previous_input = _text_input(control)
        control.setProperty("inputType", window.property("labelType"))
        assert _wait_for(lambda: control.property("textInput") != previous_input)
        label_input = _text_input(control)
        assert label_input.property("text") == "Alpha"
        control.forceActiveFocus()
        assert _wait_for(lambda: bool(label_input.property("activeFocus")))
        assert control.inputHasFocus()
        assert control.property("focused")
        control.selectAll()
        assert control.property("selectedText") == "Alpha"
        control.setAlignment(int(Qt.AlignmentFlag.AlignHCenter))
        assert window.property("controlAlignment") == Qt.AlignmentFlag.AlignHCenter

        control.setProperty("inputType", window.property("searchType"))
        assert _wait_for(lambda: control.property("textInput") is not None)
        assert _text_input(control).property("text") == "Alpha"
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_core_default_variant_geometry(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        default_width = window.property("defaultInputWidth")
        assert controls["control"].property("contentWidth") == default_width
        assert controls["labelControl"].property("contentWidth") == window.property(
            "labelInputWidth"
        )
        assert controls["tagControl"].property("contentWidth") == window.property(
            "tagInputWidth"
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_core_tag_buttons_accept_real_mouse_click(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    tag_control = controls["tagControl"]
    removed = []
    searched = []
    tag_control.tagRemoved.connect(lambda index, tag: removed.append((index, tag)))
    tag_control.searched.connect(searched.append)
    try:
        close_button = _visible_descendant(tag_control, "CloseButton")
        search_button = _visible_descendant(tag_control, "SearchButton")
        _click(window, close_button)
        assert _wait_for(lambda: removed == [(0, "one")])
        assert _variant(tag_control.property("tags")) == []
        _click(window, search_button)
        assert _wait_for(lambda: searched == [""])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_core_tag_backspace_deletion(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    tag_control = controls["tagControl"]
    text_input = tag_control.property("textInput")
    removed = []
    tag_control.tagRemoved.connect(lambda index, tag: removed.append((index, tag)))
    try:
        tag_control.setProperty("tags", ["one", "two"])
        text_input.forceActiveFocus()
        assert _wait_for(lambda: bool(text_input.property("activeFocus")))

        QTest.keyClick(window, Qt.Key.Key_Backspace)
        assert _wait_for(lambda: _variant(tag_control.property("tags")) == ["one"])
        assert removed == [(1, "two")]

        text_input.setProperty("text", "x")
        QTest.keyClick(window, Qt.Key.Key_Backspace)
        assert text_input.property("text") == ""
        assert _variant(tag_control.property("tags")) == ["one"]
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_core_tag_select_all_visual_and_clear(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    tag_control = controls["tagControl"]
    text_input = tag_control.property("textInput")
    modified = []
    tag_control.tagsModified.connect(lambda tags: modified.append(_variant(tags)))
    try:
        tag_control.setProperty("tags", ["one", "two"])
        text_input.forceActiveFocus()
        assert _wait_for(lambda: bool(text_input.property("activeFocus")))

        _pump()
        tokens = [
            item
            for item in _visual_descendants(tag_control)
            if item.metaObject().indexOfProperty("tokenIndex") >= 0
            and item.metaObject().indexOfProperty("selected") >= 0
        ]
        assert len(tokens) == 2
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: all(item.property("selected") for item in tokens))
        QTest.keyClick(window, Qt.Key.Key_Backspace)
        assert _wait_for(lambda: _variant(tag_control.property("tags")) == [])
        assert modified[-1] == []
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_line_edit_core_source_conventions_and_width_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "expandedWidth: Enums.controlSize.inputDefaultWidth" in source
    assert "Enums.controlSize.lineEditLabelWidth" in source
    assert "Enums.controlSize.lineEditTagWidth" in source
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int lineEditLabelWidth: 250" in metrics
    assert "readonly property int lineEditTagWidth: 300" in metrics
