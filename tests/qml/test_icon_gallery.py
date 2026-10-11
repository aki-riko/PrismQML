# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Icon Gallery integration contracts. 图标 Gallery 集成契约。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "examples" / "pages" / "IconPage.qml"
DETAIL_PANEL_WIDTH = 240
LEAF_CELL_OBJECT_NAME = "leafComponentCell"
LEAF_CELL_LABELS = (
    "CheckIcon",
    "ChevronIcon",
    "ChevronIcon (open)",
    "CloseIcon",
)


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose(obj) -> None:
    if obj is None:
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def icon_gallery(qapp):
    assert register_gallery_resources()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SOURCE_PATH)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickItem)
    root.setWidth(1200)
    root.setHeight(800)
    window = QQuickWindow()
    window.setWidth(1200)
    window.setHeight(800)
    root.setParentItem(window.contentItem())
    window.show()
    _pump(600)
    try:
        yield window, root, warnings
    finally:
        window.close()
        _dispose(root)
        _dispose(component)
        engine.collectGarbage()
        engine.clearComponentCache()
        _dispose(engine)
        _dispose(window)


def _grid(root: QQuickItem) -> QQuickItem:
    """The virtualized icon grid view. 虚拟化图标网格视图。"""
    return next(
        item
        for item in root.findChildren(QQuickItem)
        if item.inherits("QQuickGridView")
    )


def _visible_cards(root: QQuickItem):
    """Return the laid-out icon grid cards, in reading order. 按阅读顺序返回已布局的图标卡片。"""
    grid = _grid(root)
    cards = [
        child
        for child in grid.property("contentItem").childItems()
        if child.metaObject().indexOfProperty("clickEnabled") >= 0 and child.isVisible()
    ]
    cards.sort(key=lambda child: (child.y(), child.x()))
    return grid, cards


def _card_label(card: QQuickItem) -> str:
    label = next(
        item
        for item in card.findChildren(QQuickItem)
        if item.metaObject().className().startswith("QQuickText")
    )
    return str(label.property("text"))


def _leaf_cells(root: QQuickItem):
    """Laid-out leaf component cells, in reading order. 按阅读顺序返回叶子组件单元格。

    Grid delegates are visual children of the view's content item, not QObject
    children, so they are collected from the visual tree.
    网格委托是视图内容项的视觉子级而非 QObject 子级, 因此从视觉树收集。
    """
    cells = [
        child
        for child in _grid(root).property("contentItem").childItems()
        if child.objectName() == LEAF_CELL_OBJECT_NAME
    ]
    cells.sort(key=lambda cell: (cell.y(), cell.x()))
    return cells


def _cards_in_viewport(root: QQuickItem):
    """Laid-out cards intersecting the visible grid viewport. 与网格视口相交的已布局卡片。

    GridView keeps delegates alive in its cache buffer beyond the viewport, so
    viewport intersection is what a user can actually see.
    GridView 会在缓存区保留视口外的委托, 因此以视口相交作为可见判据。
    """
    grid, cards = _visible_cards(root)
    top = float(grid.property("contentY"))
    bottom = top + grid.height()
    return [
        card
        for card in cards
        if card.y() + card.height() > top and card.y() < bottom
    ]


def _left_column(root: QQuickItem) -> QQuickItem:
    """Left icon area of the page (title, search, grid). 页面左侧图标区。"""
    row = next(
        child
        for child in root.childItems()
        if "QQuickRow" in child.metaObject().className()
    )
    return row.childItems()[0]


def _detail_panel(root: QQuickItem) -> QQuickItem:
    """Right-hand detail panel of the icon page. 图标页右侧详情面板。"""
    row = next(
        child
        for child in root.childItems()
        if "QQuickRow" in child.metaObject().className()
    )
    return next(
        child for child in row.childItems() if child.width() == DETAIL_PANEL_WIDTH
    )


def test_icon_gallery_source_keeps_grid_cards_clickable():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "delegate: Card {" in source
    assert "clickEnabled: !gridCard.leafComponent" in source
    assert "onClicked: root.selectedIcon = modelData" in source
    # The leaf components are grid cells now, not a block above the grid.
    # 叶子组件已是网格单元格, 不再有网格上方的独立区块。
    assert "ComponentCard" not in source
    assert "GalleryFlow" not in source


def test_icon_gallery_leads_the_grid_with_every_leaf_component(icon_gallery):
    """Leaf components are the leading cells of the icon grid.

    叶子组件是图标网格最前面的单元格, 与枚举图标同处一个滚动列表。
    """
    window, root, warnings = icon_gallery
    left = _left_column(root)
    panel = _detail_panel(root)
    grid, cards = _visible_cards(root)
    leaves = _leaf_cells(root)

    assert [cell.property("clickEnabled") for cell in leaves] == [False] * 4
    assert [_card_label(cell) for cell in leaves] == list(LEAF_CELL_LABELS)
    # Leading cells of the laid-out grid, in one row. 已布局网格的最前面一行。
    assert leaves == cards[: len(LEAF_CELL_LABELS)]
    assert len({cell.y() for cell in leaves}) == 1
    assert len({cell.x() for cell in leaves}) == len(LEAF_CELL_LABELS)

    left_scene = left.mapToScene(QPointF(0, 0))
    panel_scene = panel.mapToScene(QPointF(0, 0))
    for cell in leaves:
        cell_scene = cell.mapToScene(QPointF(0, 0))
        assert cell_scene.x() >= left_scene.x() - 0.5
        assert cell_scene.x() + cell.width() <= left_scene.x() + left.width() + 0.5
        assert cell_scene.x() + cell.width() <= panel_scene.x()
        # Inside the grid viewport, not floating above it. 位于网格视口内, 不悬浮在网格之上。
        assert cell_scene.y() >= grid.mapToScene(QPointF(0, 0)).y() - 0.5
        assert cell_scene.y() + cell.height() <= grid.height() + 0.5

    assert warnings == []


def test_icon_gallery_leaf_cells_scroll_with_the_grid(icon_gallery):
    window, root, warnings = icon_gallery
    grid, _ = _visible_cards(root)
    before = {_card_label(cell): cell.mapToScene(QPointF(0, 0)).y() for cell in _leaf_cells(root)}
    assert set(before) == set(LEAF_CELL_LABELS)

    scroll_delta = 100
    grid.setProperty("contentY", grid.property("contentY") + scroll_delta)
    _pump(200)

    after = {_card_label(cell): cell.mapToScene(QPointF(0, 0)).y() for cell in _leaf_cells(root)}
    assert set(after) == set(LEAF_CELL_LABELS)
    for label, scene_y in after.items():
        assert abs((before[label] - scene_y) - scroll_delta) <= 1.0, label
    assert warnings == []


def test_icon_gallery_search_filters_leaf_cells_alongside_enum_icons(icon_gallery):
    window, root, warnings = icon_gallery
    root.setProperty("searchText", "chevron")
    _pump(400)

    labels = [_card_label(card) for card in _cards_in_viewport(root)]
    assert labels, "search produced no grid cells"
    assert all("chevron" in label.lower() for label in labels)
    assert "ChevronIcon" in labels
    assert "ChevronIcon (open)" in labels
    assert "CheckIcon" not in labels
    assert warnings == []


def test_icon_gallery_card_click_switches_selection(icon_gallery):
    window, root, warnings = icon_gallery
    _, cards = _visible_cards(root)
    selectable = [card for card in cards if card.property("clickEnabled") is True]
    assert selectable, "icon grid produced no selectable cards"

    card = selectable[0]
    expected = _card_label(card)
    assert expected != root.property("selectedIcon")

    point = card.mapToScene(QPointF(card.width() / 2, card.height() / 2)).toPoint()
    QTest.mouseMove(window, point)
    _pump(60)
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
    _pump(200)

    assert root.property("selectedIcon") == expected
    assert warnings == []


def test_icon_gallery_leaf_cell_click_keeps_selection(icon_gallery):
    window, root, warnings = icon_gallery
    leaves = _leaf_cells(root)
    assert leaves, "icon grid produced no leaf cells"

    cell = leaves[0]
    selected = root.property("selectedIcon")
    point = cell.mapToScene(QPointF(cell.width() / 2, cell.height() / 2)).toPoint()
    QTest.mouseMove(window, point)
    _pump(60)
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
    _pump(200)

    assert root.property("selectedIcon") == selected
    assert warnings == []
