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


def _leaf_animated_icon(root: QQuickItem):
    """The AnimatedIcon shown in the icon-components block. 图标组件区的 AnimatedIcon。"""
    return next(
        item
        for item in root.findChildren(QQuickItem)
        if item.metaObject().indexOfProperty("stateIcons") >= 0
        and item.property("iconSize") == 28
    )


def test_icon_gallery_source_keeps_grid_cards_clickable():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "delegate: Card {" in source
    assert "clickEnabled: true" in source
    assert "onClicked: root.selectedIcon = modelData" in source


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
    assert _leaf_animated_icon(root).property("icon") == expected
    assert warnings == []
