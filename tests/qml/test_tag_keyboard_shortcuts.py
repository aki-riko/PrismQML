# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TagLineEdit keyboard shortcut regressions. 标签输入框快捷键回归。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "tag-keyboard-shortcuts.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 180
    visible: true

    LineEdit {
        id: tagControl
        objectName: "tagControl"
        x: 40
        y: 60
        width: 560
        inputType: Enums.input.type_tag
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


def _tag_tokens(control: QQuickItem) -> list[QQuickItem]:
    return sorted(
        [
            item
            for item in _visual_descendants(control)
            if item.metaObject().indexOfProperty("tokenIndex") >= 0
            and item.metaObject().indexOfProperty("selected") >= 0
        ],
        key=lambda item: item.property("tokenIndex"),
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
    control = window.findChild(QQuickItem, "tagControl")
    assert control is not None
    assert _wait_for(lambda: control.property("textInput") is not None)
    return engine, component, window, control, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_tag_range_navigation_delete_and_escape(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, control, warnings = _create_scene()
    text_input = control.property("textInput")
    removed = []
    control.tagRemoved.connect(lambda index, tag: removed.append((index, tag)))
    try:
        control.setProperty("tags", ["one", "two", "three"])
        text_input.forceActiveFocus()
        assert _wait_for(lambda: bool(text_input.property("activeFocus")))
        assert _wait_for(lambda: len(_tag_tokens(control)) == 3)

        QTest.keyClick(window, Qt.Key.Key_Left)
        assert [item.property("selected") for item in _tag_tokens(control)] == [
            False,
            False,
            True,
        ]
        QTest.keyClick(window, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)
        assert [item.property("selected") for item in _tag_tokens(control)] == [
            False,
            True,
            True,
        ]

        QTest.keyClick(window, Qt.Key.Key_Delete)
        assert _wait_for(lambda: _variant(control.property("tags")) == ["one"])
        assert removed == [(2, "three"), (1, "two")]
        assert _wait_for(lambda: len(_tag_tokens(control)) == 1)

        QTest.keyClick(window, Qt.Key.Key_Home)
        assert _tag_tokens(control)[0].property("selected")
        QTest.keyClick(window, Qt.Key.Key_End)
        assert not _tag_tokens(control)[0].property("selected")
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        assert _tag_tokens(control)[0].property("selected")
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert not _tag_tokens(control)[0].property("selected")
        assert _variant(control.property("tags")) == ["one"]
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_tag_clipboard_history_and_text_shortcuts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, control, warnings = _create_scene()
    text_input = control.property("textInput")
    clipboard = QGuiApplication.clipboard()
    previous_clipboard = clipboard.text()
    try:
        control.setProperty("tags", ["one", "two"])
        control.setProperty("extraSeparators", [","])
        text_input.forceActiveFocus()
        assert _wait_for(lambda: bool(text_input.property("activeFocus")))

        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        assert clipboard.text() == "one two"
        QTest.keyClick(window, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: _variant(control.property("tags")) == [])

        QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert _variant(control.property("tags")) == ["one", "two"]
        QTest.keyClick(
            window,
            Qt.Key.Key_Z,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        assert _variant(control.property("tags")) == []
        QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert _variant(control.property("tags")) == ["one", "two"]

        clipboard.setText("three,four")
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(window, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(
            lambda: _variant(control.property("tags")) == ["three", "four"]
        )
        QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert _variant(control.property("tags")) == ["one", "two"]
        QTest.keyClick(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        assert _variant(control.property("tags")) == ["three", "four"]

        control.setProperty("allowCustomTags", False)
        clipboard.setText("invalid")
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(window, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        assert _variant(control.property("tags")) == ["three", "four"]
        assert all(item.property("selected") for item in _tag_tokens(control))
        control.setProperty("allowCustomTags", True)
        QTest.keyClick(window, Qt.Key.Key_Escape)

        text_input.setProperty("text", "draft")
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        assert text_input.property("selectedText") == "draft"
        assert not any(item.property("selected") for item in _tag_tokens(control))
        QTest.keyClick(window, Qt.Key.Key_Delete)
        assert text_input.property("text") == ""
        assert _variant(control.property("tags")) == ["three", "four"]
        QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert text_input.property("text") == "draft"
        assert _variant(control.property("tags")) == ["three", "four"]
        QTest.keyClick(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        assert text_input.property("text") == ""
        assert _variant(control.property("tags")) == ["three", "four"]
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        clipboard.setText(previous_clipboard)
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
