# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TextEditCore runtime contracts. TextEditCore 运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
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
TEST_URL = "prismtest://textedit/link"
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "TextEdit"
    / "TextEditCore.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "text-edit-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int plainFormat: TextEdit.PlainText
    readonly property int richFormat: TextEdit.RichText
    readonly property int arrowCursor: Qt.ArrowCursor
    readonly property int iBeamCursor: Qt.IBeamCursor
    readonly property int indicatorWidth: Enums.controlSize.progressBarHeight
    readonly property int thumbMinHeight: Enums.controlSize.textEditScrollThumbMinHeight

    width: 620
    height: 320
    visible: true

    Item {
        id: background
        objectName: "background"
        anchors.fill: parent
        focus: true

        MouseArea {
            anchors.fill: parent
            onClicked: background.forceActiveFocus()
        }
    }

    TextEdit {
        id: plain
        objectName: "plain"
        x: 40
        y: 40
        width: 240
        height: 100
        text: "alpha"
        placeholderText: "Type here"
    }

    TextEdit {
        id: browser
        objectName: "browser"
        x: 320
        y: 40
        width: 240
        height: 100
        multilineType: Enums.input.multiline_browser
        text: "<p><b>Bold</b> <a href='prismtest://textedit/link'>Link</a></p>"
    }

    TextEdit {
        id: scroll
        objectName: "scroll"
        x: 40
        y: 180
        width: 240
        height: 90
        showScrollIndicator: true
        text: "line 01\\nline 02\\nline 03\\nline 04\\nline 05\\nline 06\\nline 07\\nline 08\\nline 09\\nline 10\\nline 11\\nline 12"
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
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in ("background", "plain", "browser", "scroll")
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


def _native_editor(control):
    matches = [
        child
        for child in _descendants(control)
        if child.metaObject().className().startswith("QQuickTextEdit")
        and child.metaObject().indexOfProperty("textFormat") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _flickable(control):
    matches = [
        child
        for child in control.childItems()
        if child.metaObject().indexOfProperty("contentY") >= 0
        and child.metaObject().indexOfProperty("boundsBehavior") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _scroll_indicator(window, control):
    matches = [
        child
        for child in control.childItems()
        if child.metaObject().className().startswith("QQuickRectangle")
        and child.width() == window.property("indicatorWidth")
        and child.isVisible()
    ]
    assert len(matches) == 1
    return matches[0]


def _click(window, item, point=None) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point or _point_for(window, item),
    )
    _pump()


def _type_beta(window) -> None:
    for key in (Qt.Key.Key_B, Qt.Key.Key_E, Qt.Key.Key_T, Qt.Key.Key_A):
        QTest.keyClick(window, key)


def _assert_plain_methods_and_signals(window, plain, background) -> None:
    editor = _native_editor(plain)
    edited = []
    finished = []
    selections = []
    cursors = []
    plain.textEdited.connect(lambda: edited.append(plain.getText()))
    plain.editingFinished.connect(lambda: finished.append(plain.getText()))
    plain.selectionChanged.connect(lambda: selections.append(editor.property("selectedText")))
    plain.cursorPositionChanged.connect(lambda: cursors.append(editor.property("cursorPosition")))
    assert (plain.getText(), plain.toPlainText()) == ("alpha", "alpha")
    assert plain.property("textContentHeight") == pytest.approx(
        editor.property("contentHeight")
    )
    plain.append(" beta")
    assert plain.getText() == "alpha beta"
    assert plain.property("textContentHeight") == pytest.approx(
        editor.property("contentHeight")
    )
    assert edited == []
    plain.selectAll()
    assert editor.property("selectedText") == "alpha beta"
    assert QMetaObject.invokeMethod(plain, "setFocus")
    assert _wait_for(lambda: editor.property("activeFocus"))
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _type_beta(window)
    assert plain.getText() == "beta"
    assert edited == ["b", "be", "bet", "beta"]
    _click(window, background)
    assert _wait_for(lambda: finished == ["beta"])
    assert selections
    assert cursors


def _assert_browser_characterization(window, browser) -> None:
    editor = _native_editor(browser)
    links = []
    browser.linkActivated.connect(links.append)
    assert browser.property("readOnly")
    assert editor.property("readOnly")
    assert browser.property("textFormat") == window.property("richFormat")
    assert not editor.property("selectByMouse")
    assert browser.property("cursorShape") == window.property("arrowCursor")
    click_point = _local_point(window, browser, browser.width() - 8, browser.height() - 8)
    _click(window, browser, click_point)
    assert not editor.property("activeFocus")

    browser.setProperty("openExternalLinks", False)
    editor.linkActivated.emit(TEST_URL + "/off")
    browser.setProperty("openExternalLinks", True)
    _pump()
    assert links == [TEST_URL + "/off"]


def _assert_scroll_geometry(window, scroll) -> None:
    flickable = _flickable(scroll)
    assert _wait_for(lambda: flickable.property("contentHeight") > flickable.height())
    assert flickable.property("interactive")
    indicator = _scroll_indicator(window, scroll)
    thumbs = [
        child
        for child in indicator.childItems()
        if child.metaObject().className().startswith("QQuickRectangle")
    ]
    assert len(thumbs) == 1
    thumb = thumbs[0]
    assert thumb.height() >= window.property("thumbMinHeight")
    maximum = flickable.property("contentHeight") - flickable.height()
    flickable.setProperty("contentY", maximum / 2)
    _pump()
    assert thumb.y() == pytest.approx((indicator.height() - thumb.height()) / 2)


def test_text_edit_plain_methods_user_and_programmatic_signals(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_plain_methods_and_signals(
            window, controls["plain"], controls["background"]
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_text_edit_browser_focus_and_external_link_characterization(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_browser_characterization(window, controls["browser"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_text_edit_scroll_indicator_geometry(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_scroll_geometry(window, controls["scroll"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_text_edit_external_link_uses_public_gate():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "property bool openExternalLinks: true" in source
    assert "if (control.openExternalLinks) Qt.openUrlExternally(link)" in source


def test_text_edit_core_source_conventions_and_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "focusTarget: _isBrowser ? null : textEdit" in source
    assert "onTextEdited: control.textEdited()" in source
    assert "Enums.controlSize.textEditScrollThumbMinHeight" in source
    assert "readonly property int textEditScrollThumbMinHeight: 20" in metrics
