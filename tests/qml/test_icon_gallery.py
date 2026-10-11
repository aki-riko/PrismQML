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
LEAF_CARDS = (
    ("leafCheckIconCard", "CheckIcon"),
    ("leafChevronIconCard", "ChevronIcon"),
    ("leafChevronOpenCard", "ChevronIcon (animated, isOpen)"),
    ("leafCloseIconCard", "CloseIcon"),
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


def _visible_cards(root: QQuickItem):
    """Return the laid-out icon grid cards, in reading order. 按阅读顺序返回已布局的图标卡片。"""
    grid = next(
        item
        for item in root.findChildren(QQuickItem)
        if item.inherits("QQuickGridView")
    )
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


def _left_column(root: QQuickItem) -> QQuickItem:
    """Left icon area of the page (title, search, leaf cards, grid). 页面左侧图标区。"""
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
    assert "clickEnabled: true" in source
    assert "onClicked: root.selectedIcon = modelData" in source


def test_icon_gallery_shows_every_leaf_component_in_the_icon_area(icon_gallery):
    """Leaf components live in the left icon area, above the icon grid.

    叶子组件展示在左侧图标区、图标网格上方, 不占用右侧详情面板。
    """
    window, root, warnings = icon_gallery
    left = _left_column(root)
    panel = _detail_panel(root)
    grid, _ = _visible_cards(root)

    left_scene = left.mapToScene(QPointF(0, 0))
    panel_scene = panel.mapToScene(QPointF(0, 0))
    grid_top = grid.mapToScene(QPointF(0, 0)).y()

    positions = []
    for object_name, label in LEAF_CARDS:
        card = root.findChild(QQuickItem, object_name)
        assert card is not None, object_name
        assert card.isVisible(), object_name

        label_item = card.findChild(QQuickItem, "componentCardLabel")
        assert label_item is not None, object_name
        assert label_item.property("text") == label

        card_scene = card.mapToScene(QPointF(0, 0))
        assert card_scene.x() >= left_scene.x() - 0.5, object_name
        assert card_scene.x() + card.width() <= left_scene.x() + left.width() + 0.5
        # Above the icon grid and clear of the right-hand panel. 位于网格上方且不侵入右侧面板。
        assert card_scene.y() + card.height() <= grid_top + 0.5, object_name
        assert card_scene.x() + card.width() <= panel_scene.x(), object_name
        positions.append((card.x(), card.y()))

    assert len(set(positions)) == len(LEAF_CARDS)
    assert warnings == []


def test_icon_gallery_card_click_switches_selection(icon_gallery):
    window, root, warnings = icon_gallery
    _, cards = _visible_cards(root)
    assert cards, "icon grid produced no laid-out cards"

    card = cards[0]
    assert card.property("clickEnabled") is True
    expected = _card_label(card)
    assert expected != root.property("selectedIcon")

    point = card.mapToScene(QPointF(card.width() / 2, card.height() / 2)).toPoint()
    QTest.mouseMove(window, point)
    _pump(60)
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
    _pump(200)

    assert root.property("selectedIcon") == expected
    assert warnings == []
