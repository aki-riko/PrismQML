# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline virtual-row branch lifecycle regressions. 时间线虚拟行分支生命周期回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "timeline-virtual-row-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    width: 460
    height: 360
    visible: true
    property bool useVirtualRows: true

    TimelineCore {
        objectName: "timeline"
        anchors.fill: parent
        virtualized: root.useVirtualRows
        showScrollBar: false
        selectedRole: "commit"
        selectedKey: "two"
        items: [{
            "title": "Today",
            "status": "info",
            "cards": [
                {
                    "text": "First change",
                    "description": "Aquila",
                    "commit": "one"
                },
                {
                    "text": "Second change",
                    "description": "Kotori",
                    "commit": "two"
                }
            ]
        }]
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
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


def _visual_descendants(item):
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _row_delegates(timeline):
    rows = []
    for item in _visual_descendants(timeline):
        if item.objectName() != "timelineGraphLayer":
            continue
        row = item.parentItem()
        if row is not None and not any(row is existing for existing in rows):
            rows.append(row)
    return rows


def _card_parts(row):
    return [
        child
        for child in row.childItems()
        if child.metaObject().indexOfProperty("shadowPadding") >= 0
        and child.metaObject().indexOfProperty("isSelected") >= 0
    ]


def _header_parts(row):
    graph_layers = {
        child for child in row.childItems() if child.objectName() == "timelineGraphLayer"
    }
    card_parts = set(_card_parts(row))
    return [
        child
        for child in row.childItems()
        if child not in graph_layers
        and child not in card_parts
        and child.clip()
    ]


def _cards(timeline):
    return [
        item
        for item in _visual_descendants(timeline)
        if item.property("clickEnabled") is True
        and item.property("contentPadding") is not None
    ]


def _has_list_view_ancestor(item):
    parent = item.parentItem()
    while parent is not None:
        if "ListView" in parent.metaObject().className():
            return True
        parent = parent.parentItem()
    return False


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
    timeline = window.findChild(QQuickItem, "timeline")
    assert timeline is not None
    assert _wait_for(
        lambda: timeline.width() == pytest.approx(window.width())
        and timeline.height() == pytest.approx(window.height())
        and len(_row_delegates(timeline)) == 3
        and len([card for card in _cards(timeline) if card.isVisible()]) == 2
    )
    return engine, component, window, timeline, warnings


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
def timeline_virtual_row_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_timeline_virtual_rows_construct_only_the_active_content_branch(
    timeline_virtual_row_scene,
):
    window, timeline, warnings, windows_before = timeline_virtual_row_scene
    rows = _row_delegates(timeline)

    assert len(rows) == 3
    assert sorted(
        (len(_header_parts(row)), len(_card_parts(row))) for row in rows
    ) == [(0, 1), (0, 1), (1, 0)]
    assert sum(part.isVisible() for row in rows for part in _header_parts(row)) == 1
    assert sum(part.isVisible() for row in rows for part in _card_parts(row)) == 2
    virtual_cards = [card for card in _cards(timeline) if _has_list_view_ancestor(card)]
    hidden_full_cards = [
        card for card in _cards(timeline) if not _has_list_view_ancestor(card)
    ]
    assert len(virtual_cards) == 2
    assert all(card.isVisible() for card in virtual_cards)
    assert hidden_full_cards == []
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_virtual_card_keeps_first_click_behavior(
    timeline_virtual_row_scene,
):
    window, timeline, warnings, windows_before = timeline_virtual_row_scene
    card_clicks = []
    card_data = []
    timeline.cardClicked.connect(
        lambda group_index, card_index, text: card_clicks.append(
            (group_index, card_index, text)
        )
    )
    timeline.cardClickedData.connect(
        lambda group_index, card_index, data: card_data.append(
            (group_index, card_index, data)
        )
    )

    visible_cards = [
        card
        for card in _cards(timeline)
        if card.isVisible() and _has_list_view_ancestor(card)
    ]
    assert len(visible_cards) == 2
    first_card = min(
        visible_cards,
        key=lambda card: card.mapToScene(QPointF(0, 0)).y(),
    )
    card_point = first_card.mapToScene(
        QPointF(first_card.width() / 2, first_card.height() / 2)
    ).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=card_point)
    assert _wait_for(lambda: card_clicks == [(0, 0, "First change")])
    assert card_data[0][0:2] == (0, 0)
    assert card_data[0][2]["commit"] == "one"
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_timeline_content_branch_roundtrip_keeps_active_cards(
    timeline_virtual_row_scene,
):
    window, timeline, warnings, windows_before = timeline_virtual_row_scene

    assert window.setProperty("useVirtualRows", False)
    settled_nonvirtual = _wait_for(
        lambda: len(
            [card for card in _cards(timeline) if not _has_list_view_ancestor(card)]
        )
        == 2
        and all(
            card.isVisible()
            for card in _cards(timeline)
            if not _has_list_view_ancestor(card)
        )
        and not any(
            card.isVisible()
            for card in _cards(timeline)
            if _has_list_view_ancestor(card)
        )
    )
    assert settled_nonvirtual, {
        "uses_virtual": timeline.property("_usesVirtualList"),
        "rows": [row.isVisible() for row in _row_delegates(timeline)],
        "cards": [
            {
                "visible": card.isVisible(),
                "virtual": _has_list_view_ancestor(card),
            }
            for card in _cards(timeline)
        ],
        "warnings": warnings,
    }

    assert window.setProperty("useVirtualRows", True)
    assert _wait_for(
        lambda: len(_row_delegates(timeline)) == 3
        and len(_cards(timeline)) == 2
        and all(card.isVisible() for card in _cards(timeline))
        and all(_has_list_view_ancestor(card) for card in _cards(timeline))
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
