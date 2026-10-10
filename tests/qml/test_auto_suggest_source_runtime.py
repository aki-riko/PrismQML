# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AutoSuggestBox async source, query submission and text write-back contracts.

AutoSuggestBox 异步建议源、查询提交与文本回填合同。
"""

from pathlib import Path

from PySide6.QtCore import (
    Q_ARG,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QKeyEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "auto-suggest-source.qml")
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 640
    height: 480
    visible: true

    property var issuedQueries: []
    property var pending: []
    property var submitted: []
    property var selected: []
    property string diag: ""

    function asyncSource(query, callback) {
        issuedQueries = issuedQueries.concat([query])
        pending = pending.concat([callback])
    }

    function resolveFirst(results) {
        var callbacks = pending
        var callback = callbacks[0]
        pending = callbacks.slice(1)
        try {
            callback(results)
        } catch (error) {
            diag = String(error) + " | " + (error.stack ? error.stack : "")
        }
    }

    function resolveLast(results) {
        var callbacks = pending
        var callback = callbacks[callbacks.length - 1]
        pending = callbacks.slice(0, callbacks.length - 1)
        try {
            callback(results)
        } catch (error) {
            diag = String(error) + " | " + (error.stack ? error.stack : "")
        }
    }

    LocalSearchBar {
        id: search
        objectName: "search"
        x: 80
        y: 60
        width: 320
        suggestionsSource: root.asyncSource
        updateTextOnSelect: true
        onQuerySubmitted: (args) => root.submitted = root.submitted.concat([args])
        onEntrySelected: (entry) => root.selected = root.selected.concat([entry])
    }

    LocalSearchBar {
        id: local
        objectName: "local"
        x: 80
        y: 160
        width: 320
        entries: [
            { "title": "Build", "subtitle": "Compile project" },
            { "title": "Settings", "subtitle": "Configure project" }
        ]
    }
}
"""

BUILD = {"title": "Build", "subtitle": "Compile project"}
SETTINGS = {"title": "Settings", "subtitle": "Configure project"}


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
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
    _pump(80)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    for name in ("search", "local"):
        item = window.findChild(QQuickItem, name)
        if item is not None:
            QMetaObject.invokeMethod(item, "dismiss")
    _pump(40)
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _item(window, name) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _entries(item) -> list:
    return list(_variant(item.property("_activeEntries")))


def _visual_descendants(root: QQuickItem) -> list:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _text_input(search: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(search)
        if item.metaObject().className().startswith("QQuickTextInput")
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _set_query(search: QQuickItem, text: str) -> None:
    assert QMetaObject.invokeMethod(search, "setQuery", Q_ARG("QVariant", text))
    _pump(40)


def _resolve_first(window, results: list) -> None:
    assert QMetaObject.invokeMethod(
        window, "resolveFirst", Q_ARG("QVariant", results)
    )
    _pump(40)


def _resolve_last(window, results: list) -> None:
    assert QMetaObject.invokeMethod(window, "resolveLast", Q_ARG("QVariant", results))
    _pump(40)


def test_defaults_keep_the_local_entries_path(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        local = _item(window, "local")
        assert local.property("suggestionsSource") is None
        assert local.property("updateTextOnSelect") is False
        assert local.property("textMemberPath") == "title"
        assert [entry["title"] for entry in _entries(local)] == [
            "Build",
            "Settings",
        ]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_async_source_is_incremental_and_drops_stale_responses(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        search = _item(window, "search")
        assert _entries(search) == []

        _set_query(search, "b")
        _set_query(search, "bu")
        assert list(_variant(window.property("issuedQueries"))) == ["b", "bu"]
        assert len(_variant(window.property("pending"))) == 2

        # A late response for the first query must be ignored 第一次查询的迟到响应必须被丢弃
        _resolve_first(window, [SETTINGS])
        assert _entries(search) == []

        _resolve_last(window, [BUILD])
        assert [entry["title"] for entry in _entries(search)] == ["Build"], window.property(
            "diag"
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_free_text_submission_reports_the_query(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        search = _item(window, "search")
        _set_query(search, "project")

        editor = _text_input(search)
        editor.forceActiveFocus()
        assert _wait_for(editor.hasActiveFocus)
        QTest.keyClick(window, Qt.Key.Key_Return)
        _pump(80)

        submitted = list(_variant(window.property("submitted")))
        assert len(submitted) == 1
        assert submitted[0]["chosenSuggestion"] is None
        assert submitted[0]["queryText"] == "project"
        assert search.property("query") == "project"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_choosing_a_suggestion_writes_the_text_back(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        search = _item(window, "search")
        _set_query(search, "b")
        _resolve_last(window, [BUILD, SETTINGS])

        result_list = search.property("_resultList")
        assert result_list is not None
        assert result_list.property("hitCount") == 1
        assert QMetaObject.invokeMethod(result_list, "reset")
        assert QMetaObject.invokeMethod(result_list, "selectCurrent")
        _pump(60)

        selected = list(_variant(window.property("selected")))
        assert len(selected) == 1
        assert selected[0]["title"] == "Build"
        # UpdateTextOnSelect writes the member back 回填写入指定字段
        assert search.property("query") == "Build"
        submitted = list(_variant(window.property("submitted")))
        assert len(submitted) == 1
        assert submitted[0]["chosenSuggestion"]["title"] == "Build"
        assert submitted[0]["queryText"] == "Build"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_default_selection_still_clears_the_query(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        search = _item(window, "search")
        assert search.setProperty("updateTextOnSelect", False)
        _set_query(search, "b")
        _resolve_last(window, [BUILD])

        result_list = search.property("_resultList")
        assert result_list is not None
        assert result_list.property("hitCount") == 1
        assert QMetaObject.invokeMethod(result_list, "reset")
        assert QMetaObject.invokeMethod(result_list, "selectCurrent")
        _pump(60)

        assert search.property("query") == ""
        submitted = list(_variant(window.property("submitted")))
        assert len(submitted) == 1
        assert submitted[0]["chosenSuggestion"]["title"] == "Build"
        assert submitted[0]["queryText"] == ""
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
