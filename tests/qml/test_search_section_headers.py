# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""LocalSearchBar section header regressions. LocalSearchBar 分组标题回归。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    Q_ARG,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SEARCH_DIR = ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "Search"
RESULT_LIST_SOURCE_PATH = SEARCH_DIR / "_internal" / "SearchResultList.qml"
LOCAL_SEARCH_SOURCE_PATH = SEARCH_DIR / "LocalSearchBar.qml"
METRICS_SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"

# Mirrors Enums.searchMetrics / Enums.spacing 对应 Enums.searchMetrics / Enums.spacing
ITEM_HEIGHT = 48
HEADER_HEIGHT = 32
ROW_SPACING = 2
LIST_MARGIN = 4

SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "search-section-headers-runtime.qml")
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
            { "title": "Mica Effect", "subtitle": "Appearance", "section": "Appearance" },
            { "title": "Accent Color", "subtitle": "Appearance", "section": "Appearance" },
            { "title": "Reset Cache", "subtitle": "Storage", "section": "Storage" },
            { "title": "Export Logs", "subtitle": "Storage", "section": "Storage" }
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


def _plain(value):
    """Convert QJSValue payloads to plain Python containers. QJSValue 转普通容器。"""
    if hasattr(value, "toVariant"):
        return _plain(value.toVariant())
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


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


def _visible_popup_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if isinstance(window, QQuickWindow)
        and window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def _result_list(popup_window: QQuickWindow) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().className().startswith("SearchResultList")
    ]
    assert len(matches) == 1
    return matches[0]


def _results_list_view(popup_window: QQuickWindow) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().className().startswith("QQuickListView")
    ]
    assert len(matches) == 1
    return matches[0]


def _row_loaders(popup_window: QQuickWindow) -> list[QQuickItem]:
    loaders = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().className().startswith("QQuickLoader")
        and item.metaObject().indexOfProperty("rowData") >= 0
    ]
    return sorted(loaders, key=lambda item: item.y())


def _rendered_rows(popup_window: QQuickWindow) -> list[dict]:
    rows = []
    for loader in _row_loaders(popup_window):
        row = _plain(loader.property("rowData"))
        rows.append({"row": row, "height": loader.height()})
    return rows


def _selected_result_indices(popup_window: QQuickWindow) -> list[int]:
    return [
        item.property("itemIndex")
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().className().startswith("SearchResultItem")
        and item.property("selected")
    ]


def _rows_of(result_list: QQuickItem) -> list[dict]:
    return _plain(result_list.property("_rows"))


def test_section_headers_group_ranked_results(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, search, warnings = _create_scene()
    try:
        assert QMetaObject.invokeMethod(search, "setQuery", Q_ARG("QVariant", "e"))
        assert _wait_for(lambda: search.property("isOpen"))
        assert _wait_for(lambda: len(_visible_popup_windows(windows_before, window)) == 1)
        popup_window = _visible_popup_windows(windows_before, window)[0]
        result_list = _result_list(popup_window)
        assert _wait_for(lambda: result_list.property("hitCount") == 4)

        rows = _rows_of(result_list)
        assert [row["kind"] for row in rows] == [
            "header",
            "item",
            "item",
            "header",
            "item",
            "item",
        ]

        # Group order follows each section's first appearance in the ranked hits
        # 分组顺序取各 section 在排名结果中首次出现的顺序
        hits = _plain(result_list.property("_hits"))
        expected_sections = []
        for hit in hits:
            section = hit["entry"].get("section") or ""
            if section not in expected_sections:
                expected_sections.append(section)
        assert [row["title"] for row in rows if row["kind"] == "header"] == [
            section for section in expected_sections if section
        ]

        # Each section appears once and keeps the ranked order inside the group
        # 每个分组只出现一次,组内保持排名顺序
        seen_sections = []
        for row in rows:
            if row["kind"] == "header":
                assert row["title"] not in seen_sections
                seen_sections.append(row["title"])

        item_rows = [row for row in rows if row["kind"] == "item"]
        assert [row["itemOrdinal"] for row in item_rows] == list(range(len(hits)))
        for section in expected_sections:
            ranked_in_group = [
                hit["entry"]["title"]
                for hit in hits
                if (hit["entry"].get("section") or "") == section
            ]
            displayed_in_group = [
                row["hit"]["entry"]["title"]
                for row in item_rows
                if row["key"] == section
            ]
            assert displayed_in_group == ranked_in_group
        for row in item_rows:
            assert row["key"] == row["hit"]["entry"]["section"]
            assert set(row) == {"kind", "key", "hit", "itemOrdinal"}

        rendered = _rendered_rows(popup_window)
        assert [item["row"]["kind"] for item in rendered] == [
            row["kind"] for row in rows
        ]
        assert [item["height"] for item in rendered] == [
            HEADER_HEIGHT,
            ITEM_HEIGHT,
            ITEM_HEIGHT,
            HEADER_HEIGHT,
            ITEM_HEIGHT,
            ITEM_HEIGHT,
        ]
        rendered_titles = [
            item["row"]["title"] for item in rendered if item["row"]["kind"] == "header"
        ]
        assert rendered_titles == [
            row["title"] for row in rows if row["kind"] == "header"
        ]

        expected_height = (
            4 * ITEM_HEIGHT
            + 2 * HEADER_HEIGHT
            + (6 - 1) * ROW_SPACING
            + 2 * LIST_MARGIN
        )
        assert result_list.property("implicitHeight") == expected_height

        assert search.setProperty("sectionHeaders", False)
        assert _wait_for(
            lambda: [row["kind"] for row in _rows_of(result_list)]
            == ["item", "item", "item", "item"]
        )
        assert result_list.property("implicitHeight") == (
            4 * ITEM_HEIGHT + 3 * ROW_SPACING + 2 * LIST_MARGIN
        )
        assert [
            item["row"]["kind"] for item in _rendered_rows(popup_window)
        ] == ["item", "item", "item", "item"]

        assert search.setProperty("sectionHeaders", True)
        # Entries without a section keep the flat legacy layout 无 section 的 entry 保持扁平旧布局
        assert search.setProperty(
            "entries", [{"title": "Element"}, {"title": "Event"}]
        )
        assert _wait_for(lambda: result_list.property("hitCount") == 2)
        assert [row["kind"] for row in _rows_of(result_list)] == ["item", "item"]
        assert result_list.property("implicitHeight") == (
            2 * ITEM_HEIGHT + 1 * ROW_SPACING + 2 * LIST_MARGIN
        )

        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, search)


def test_section_headers_keyboard_navigation_skips_headers(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, search, warnings = _create_scene()
    selected_entries = []
    search.entrySelected.connect(selected_entries.append)
    try:
        assert QMetaObject.invokeMethod(search, "setQuery", Q_ARG("QVariant", "e"))
        assert _wait_for(lambda: search.property("isOpen"))
        assert _wait_for(lambda: len(_visible_popup_windows(windows_before, window)) == 1)
        popup_window = _visible_popup_windows(windows_before, window)[0]
        result_list = _result_list(popup_window)
        list_view = _results_list_view(popup_window)
        assert _wait_for(lambda: result_list.property("hitCount") == 4)
        rows = _rows_of(result_list)
        assert [row["kind"] for row in rows] == [
            "header",
            "item",
            "item",
            "header",
            "item",
            "item",
        ]

        assert _wait_for(lambda: result_list.property("_itemCursor") == 0)
        assert list_view.property("currentIndex") == 1
        assert _selected_result_indices(popup_window) == [0]

        # Header rows are never a cursor target 标题行不会成为光标目标
        item_row_indices = [
            index for index, row in enumerate(rows) if row["kind"] == "item"
        ]
        assert len(item_row_indices) == 4
        for ordinal in (1, 2, 3, 0):
            assert QMetaObject.invokeMethod(result_list, "moveDown")
            assert _wait_for(
                lambda ordinal=ordinal: result_list.property("_itemCursor") == ordinal
            )
            row_index = list_view.property("currentIndex")
            assert rows[row_index]["kind"] == "item"
            assert row_index in item_row_indices
            assert _selected_result_indices(popup_window) == [ordinal]

        # moveUp wraps to the last result row, which is not the last row 向上 wrap 到最后一条结果行
        assert QMetaObject.invokeMethod(result_list, "moveUp")
        assert _wait_for(lambda: result_list.property("_itemCursor") == 3)
        assert list_view.property("currentIndex") == item_row_indices[3]
        assert _selected_result_indices(popup_window) == [3]

        assert QMetaObject.invokeMethod(result_list, "moveUp")
        assert _wait_for(lambda: result_list.property("_itemCursor") == 2)
        assert list_view.property("currentIndex") == item_row_indices[2]
        assert _selected_result_indices(popup_window) == [2]

        expected_title = rows[item_row_indices[2]]["hit"]["entry"]["title"]
        assert QMetaObject.invokeMethod(result_list, "selectCurrent")
        assert _wait_for(lambda: len(selected_entries) == 1)
        assert _plain(selected_entries[0])["title"] == expected_title
        assert _wait_for(lambda: search.property("query") == "")
        assert _wait_for(lambda: not search.property("isOpen"))
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, search)


def test_section_headers_reset_follows_result_replacement(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, search, warnings = _create_scene()
    try:
        assert QMetaObject.invokeMethod(search, "setQuery", Q_ARG("QVariant", "e"))
        assert _wait_for(lambda: search.property("isOpen"))
        assert _wait_for(lambda: len(_visible_popup_windows(windows_before, window)) == 1)
        popup_window = _visible_popup_windows(windows_before, window)[0]
        result_list = _result_list(popup_window)
        list_view = _results_list_view(popup_window)
        assert _wait_for(lambda: result_list.property("hitCount") == 4)
        assert QMetaObject.invokeMethod(result_list, "moveDown")
        assert _wait_for(lambda: result_list.property("_itemCursor") == 1)

        assert search.setProperty(
            "entries",
            [
                {"title": "Storage Deck", "subtitle": "Storage", "section": "Storage"},
                {"title": "Storage Pool", "subtitle": "Storage", "section": "Storage"},
            ],
        )
        assert _wait_for(lambda: result_list.property("hitCount") == 2)
        assert _wait_for(lambda: result_list.property("_itemCursor") == 0)
        assert list_view.property("currentIndex") == 1
        assert _selected_result_indices(popup_window) == [0]
        assert [row["kind"] for row in _rows_of(result_list)] == [
            "header",
            "item",
            "item",
        ]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, search)


def test_search_surface_source_conventions():
    for path in (RESULT_LIST_SOURCE_PATH, LOCAL_SEARCH_SOURCE_PATH):
        source = path.read_text(encoding="utf-8")
        relative = PurePosixPath(path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, relative)
        assert [
            item for item in violations if item.rule in {"QML008", "QML009"}
        ] == []


def test_section_headers_are_wired_and_measured():
    list_source = RESULT_LIST_SOURCE_PATH.read_text(encoding="utf-8")
    bar_source = LOCAL_SEARCH_SOURCE_PATH.read_text(encoding="utf-8")
    metrics_source = METRICS_SOURCE_PATH.read_text(encoding="utf-8")

    assert "readonly property int resultSectionHeaderHeight:" in metrics_source
    assert "Enums.searchMetrics.resultSectionHeaderHeight" in list_source
    assert "sectionHeaders: control.sectionHeaders" in bar_source
    assert "Not implemented yet" not in bar_source
    assert "property bool sectionHeaders: true" in bar_source
    # The cursor must live in result space, not row space 光标必须位于结果序而非行序
    assert "rowIndex: index" in list_source
    assert "control._itemCursor === itemIndex" in list_source
