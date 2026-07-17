# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SearchPopup parent-chain regressions. SearchPopup 公开父链回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Search"
    / "_internal"
    / "SearchPopup.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "search-popup-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 480
    visible: true

    LocalSearchBar {
        objectName: "search"
        x: 80
        y: 60
        width: 320
        entries: [
            { "title": "Build", "subtitle": "Compile project" },
            { "title": "Settings", "subtitle": "Configure project" },
            { "title": "Search", "subtitle": "Find files" }
        ]
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1800) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(20)
        elapsed += 20
    return predicate()


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
    search = window.findChild(QQuickItem, "search")
    assert search is not None
    return engine, component, window, search, warnings


def _dispose_scene(engine, component, window, search) -> None:
    if search.property("isOpen"):
        assert QMetaObject.invokeMethod(search, "dismiss")
        _wait_for(lambda: not search.property("isOpen"))
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = [root]
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _search_popup(search: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(search)
        if item.metaObject().className().startswith("SearchPopup")
    ]
    assert len(matches) == 1
    return matches[0]


def _popup_core(search_popup: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(search_popup)
        if item.metaObject().className().startswith("PopupWindowCore")
        and item.metaObject().indexOfProperty("popupWidth") >= 0
        and item.metaObject().indexOfProperty("isClosing") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _text_input(search: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(search)
        if item.metaObject().className().startswith("QQuickTextInput")
    ]
    assert len(matches) == 1
    return matches[0]


def _visible_popup_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if isinstance(window, QQuickWindow)
        and window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def _type_text(text_input: QQuickItem, text: str) -> None:
    event = QInputMethodEvent()
    event.setCommitString(text)
    QCoreApplication.sendEvent(text_input, event)
    _pump(20)


def test_search_popup_preserves_sizing_and_idempotent_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, search, warnings = _create_scene()
    try:
        popup = _search_popup(search)
        popup_core = _popup_core(popup)
        text_input = _text_input(search)
        opened = []
        dismissed = []
        search.opened.connect(lambda: opened.append(True))
        search.dismissed.connect(lambda: dismissed.append(True))

        assert search.property("query") == ""
        assert not search.property("isOpen")
        assert popup.property("_resolvedWidth") == 320
        assert _wait_for(lambda: popup.property("_resolvedHeight") == 156)

        search.setWidth(180)
        assert _wait_for(lambda: popup.property("_resolvedWidth") == 240)
        search.setWidth(320)
        assert _wait_for(lambda: popup.property("_resolvedWidth") == 320)

        text_input.forceActiveFocus()
        assert _wait_for(text_input.hasActiveFocus)
        _type_text(text_input, "build")
        assert _wait_for(lambda: search.property("query") == "build")
        assert _wait_for(lambda: search.property("isOpen")), (
            search.property("popupMode"),
            popup_core.property("isOpen"),
            popup_core.property("isClosing"),
            warnings,
        )
        assert _wait_for(lambda: popup_core.property("isOpen"))
        assert _wait_for(lambda: len(_visible_popup_windows(windows_before, window)) == 1)
        popup_window = _visible_popup_windows(windows_before, window)[0]
        assert popup_core.property("popupWidth") == 320
        assert _wait_for(lambda: popup_core.property("popupHeight") == 56)
        assert opened == [True]

        _type_text(text_input, " ")
        assert _wait_for(lambda: search.property("query") == "build ")
        _pump(40)
        assert opened == [True]
        assert popup_window.isVisible()

        assert QMetaObject.invokeMethod(text_input, "selectAll")
        _type_text(text_input, "missing")
        assert _wait_for(lambda: search.property("query") == "missing")
        assert _wait_for(lambda: popup.property("_resolvedHeight") == 60)
        assert _wait_for(lambda: popup_core.property("popupHeight") == 60)

        assert QMetaObject.invokeMethod(search, "dismiss")
        assert _wait_for(lambda: not search.property("isOpen"))
        assert _wait_for(lambda: not popup_core.property("isClosing"))
        assert _wait_for(lambda: not popup_window.isVisible())
        assert dismissed == [True]

        assert QMetaObject.invokeMethod(search, "dismiss")
        _pump(40)
        assert dismissed == [True]
        assert warnings == []
        assert _visible_popup_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, search)


def test_search_popup_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []
