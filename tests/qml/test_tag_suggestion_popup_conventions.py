# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tag suggestion popup regressions. 标签建议弹窗回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
POPUP_SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "LineEdit"
    / "_internal"
    / "TagSuggestionPopup.qml"
)
TAG_LINE_EDIT_SOURCE_PATH = POPUP_SOURCE_PATH.parent.parent / "TagLineEdit.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "tag-suggestion-popup-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property real expectedInputHeight: Enums.controlSize.inputHeight
    readonly property real expectedSpacingM: Enums.spacing.m

    width: 480
    height: 240
    visible: true

    LineEdit {
        id: tagInput
        objectName: "tagInput"
        x: 60
        y: 60
        width: 320
        inputType: Enums.input.type_tag
        suggestions: ["Alpha", "Beta", "Gamma"]
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


def _popup_core(tag_input: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _descendants(tag_input)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("PopupWindowCore")
        and child.metaObject().indexOfProperty("listModel") >= 0
        and child.metaObject().indexOfProperty("isOpen") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _tag_line_edit(tag_input: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _descendants(tag_input)
        if isinstance(child, QQuickItem)
        and child.metaObject().indexOfMethod("addTag(QVariant,QVariant)") >= 0
        and child.metaObject().indexOfMethod("clearTags()") >= 0
        and child.metaObject().indexOfProperty("_countText") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


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
    tag_input = window.findChild(QQuickItem, "tagInput")
    assert tag_input is not None
    assert _wait_for(lambda: tag_input.property("textInput") is not None)
    return engine, component, window, tag_input, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_tag_suggestion_popup_open_resize_and_close_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, tag_input, warnings = _create_scene()
    try:
        popup = _popup_core(tag_input)
        text_input = tag_input.property("textInput")
        assert isinstance(text_input, QQuickItem)
        text_input.forceActiveFocus()
        assert _wait_for(lambda: text_input.property("activeFocus"))

        text_input.setProperty("text", "a")
        assert _wait_for(lambda: popup.property("isOpen"))
        assert popup.property("popupWidth") == tag_input.property("width")
        assert popup.property("popupHeight") == (
            3 * window.property("expectedInputHeight")
            + window.property("expectedSpacingM")
        )
        assert _wait_for(lambda: len(_new_visible_windows(windows_before, window)) == 1)

        text_input.setProperty("text", "Al")
        assert _wait_for(
            lambda: popup.property("popupHeight")
            == window.property("expectedInputHeight") + window.property("expectedSpacingM")
        )

        text_input.setProperty("text", "")
        assert _wait_for(lambda: not popup.property("isOpen"))
        assert _wait_for(lambda: not popup.property("isClosing"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_tag_line_edit_command_and_signal_parent_chain(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, tag_input, warnings = _create_scene()
    try:
        tag_edit = _tag_line_edit(tag_input)
        added = []
        modified = []
        tag_input.tagAdded.connect(added.append)
        tag_input.tagsModified.connect(lambda value: modified.append(_variant(value)))

        tag_edit.addTag(" Alpha ", None)
        _pump()
        assert _variant(tag_input.property("tags")) == ["Alpha"]
        assert added == ["Alpha"]
        assert modified == [["Alpha"]]

        tag_edit.addTag("Alpha", None)
        tag_input.setProperty("maxTags", 2)
        tag_input.setProperty("extraSeparators", [","])
        assert tag_edit._addSplit("Beta,Gamma")
        _pump()
        assert _variant(tag_input.property("tags")) == ["Alpha", "Beta"]
        assert added == ["Alpha", "Beta"]
        assert tag_edit.property("_countText") == "2/2"

        tag_edit.clearTags()
        tag_input.setProperty("allowCustomTags", False)
        tag_edit.addTag("Delta", None)
        tag_edit.addTag("Gamma", None)
        _pump()
        assert _variant(tag_input.property("tags")) == ["Gamma"]
        assert added == ["Alpha", "Beta", "Gamma"]
        assert tag_edit.property("_countText") == "1/2"
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_tag_suggestion_popup_source_conventions():
    source = POPUP_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(POPUP_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert (
        "readonly property bool needsScroll: "
        "suggestionList.contentHeight > suggestionList.height"
    ) in source
    assert "interactive: false" in source
    assert (
        "PopupSmoothScroll { flickable: suggestionList; "
        "enabled: popup.needsScroll }"
    ) in source
    assert "sourceComponent: ScrollBarEntry" in source
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_tag_line_edit_source_conventions():
    source = TAG_LINE_EDIT_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(TAG_LINE_EDIT_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
