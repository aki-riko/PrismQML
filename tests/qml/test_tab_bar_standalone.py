# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Standalone TabBar contracts. 独立 TabBar 组件合同。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl, QObject
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]


SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 760
    height: 140
    visible: false

    TabBar {
        id: bar
        objectName: "tabBar"
        width: 720
        height: 60
        detailsEnabled: true
        tabBarHeight: Enums.controlSize.tableHeaderHeight + Enums.spacing.xl
        tabContentVerticalPadding: Enums.spacing.m
        tabWidth: 180
        minimumTabWidth: 130
        maximumTabWidth: 220
        closable: true
        showAddButton: true
        tabs: [
            {
                title: "Gitora",
                icon: Enums.icon.folder,
                subtitle: "codex/multi-repo-tabs-ui",
                badgeText: "7",
                badgeLevel: Enums.statusLevel.warning
            },
            {
                title: "PrismQML",
                icon: Enums.icon.folder,
                subtitle: "main",
                badgeText: "干净",
                badgeLevel: Enums.statusLevel.success
            }
        ]
        currentIndex: 1
    }
}
""".encode("utf-8")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl("inline:tab-bar-standalone.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [
        error.toString() for error in component.errors()
    ]
    _pump(50)
    return engine, component, window


@pytest.fixture
def tab_bar_scene(qapp):
    scene = _create_scene(qapp)
    try:
        yield scene
    finally:
        engine, component, window = scene
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()


def _delegates(bar: QQuickItem) -> list[QQuickItem]:
    pending = list(bar.childItems())
    result = []
    while pending:
        item = pending.pop()
        if item.metaObject().indexOfProperty("visualOffsetX") >= 0:
            result.append(item)
        pending.extend(item.childItems())
    return result


def _descendants(root: QQuickItem):
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        yield item
        pending.extend(item.childItems())


def test_tab_bar_is_usable_without_content_pages(tab_bar_scene):
    _engine, _component, window = tab_bar_scene
    bar = window.findChild(QObject, "tabBar")
    assert bar is not None
    assert bar.property("count") is None
    assert bar.property("currentIndex") == 1
    assert bar.property("_tabBarHeight") == 60
    assert bar.property("_tabHeight") == 44
    assert bar.metaObject().indexOfProperty("addButtonItem") >= 0
    assert bar.findChild(QObject, "tabBarAddButton") is not None
    assert len(_delegates(bar)) == 2
    assert all(delegate.width() == pytest.approx(180) for delegate in _delegates(bar))
    inset = (bar.property("_tabBarHeight") - bar.property("_tabHeight")) / 2
    for delegate in _delegates(bar):
        mapped = delegate.mapToItem(bar, 0, 0)
        assert mapped.y() == pytest.approx(inset)
        assert delegate.height() == pytest.approx(bar.property("_tabHeight"))
        detail = delegate.findChild(QObject, "tabItemDetailContent")
        assert detail is not None
        assert detail.property("spacing") == pytest.approx(6)
    assert all(delegate.property("_hasDetails") is True for delegate in _delegates(bar))
    icons = [
        item for delegate in _delegates(bar) for item in _descendants(delegate)
        if item.metaObject().indexOfProperty("isSvgIcon") >= 0
    ]
    assert icons and all(item.property("isSvgIcon") is True for item in icons)
    assert not bar.findChild(QObject, "tabContentPages")


def test_tab_widget_composes_tab_bar_and_keeps_public_contract():
    tab_widget = (
        ROOT / "prismqml" / "PrismQML" / "controls" / "navigation" / "TabWidget.qml"
    ).read_text(encoding="utf-8")
    tab_bar = (
        ROOT / "prismqml" / "PrismQML" / "controls" / "navigation" / "TabBar.qml"
    ).read_text(encoding="utf-8")
    qmldir = (ROOT / "prismqml" / "PrismQML" / "qmldir").read_text(
        encoding="utf-8"
    )

    assert "TabBar controls/navigation/TabBar.qml" in qmldir
    assert "TabBar {" in tab_widget
    assert "TabContentPages {" in tab_widget
    assert "TabIndicator {" in tab_bar
    assert "TabEdgeAutoScroll {" in tab_bar
    assert "property alias addButtonItem" in tab_bar
    assert "property bool detailsEnabled" in tab_bar
