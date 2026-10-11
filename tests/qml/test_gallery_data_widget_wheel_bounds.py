# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery data-widget wheel hit bounds. 画廊数据组件滚轮命中边界回归。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
MENU_PAGE_URL = QUrl.fromLocalFile(str(ROOT / "examples" / "pages" / "MenuPage.qml"))


def _pump(milliseconds: int = 80) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose(obj) -> None:
    if obj is None:
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _viewport(control: QQuickItem) -> QQuickItem:
    candidates = [
        item
        for item in control.findChildren(QQuickItem)
        if item.metaObject().indexOfProperty("contentY") >= 0
        and item.metaObject().indexOfProperty("contentHeight") >= 0
        and any(
            marker in item.metaObject().className()
            for marker in ("Flickable", "ListView", "GridView")
        )
    ]
    assert candidates, control.metaObject().className()
    return max(candidates, key=lambda item: item.height())


def _gallery_data_widgets(page: QQuickItem) -> list[QQuickItem]:
    prefixes = (
        "ListWidget_QMLTYPE_",
        "TreeWidget_QMLTYPE_",
        "TableWidget_QMLTYPE_",
        "ListView_QMLTYPE_",
        "TableView_QMLTYPE_",
        "TreeView_QMLTYPE_",
    )
    widgets = [
        item
        for item in page.findChildren(QQuickItem)
        if item.metaObject().className().startswith(prefixes)
        and item.width() > 0
        and item.height() > 0
    ]
    assert len(widgets) == 6, [item.metaObject().className() for item in widgets]
    return sorted(
        widgets,
        key=lambda item: (
            item.mapToItem(page, 0, 0).y(),
            item.mapToItem(page, 0, 0).x(),
        ),
    )


def _send_wheel(window: QQuickWindow, x: float, y: float) -> QWheelEvent:
    scene_pos = QPointF(x, y)
    event = QWheelEvent(
        scene_pos,
        QPointF(window.x() + x, window.y() + y),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    _pump(320)
    return event


@pytest.fixture
def gallery_menu_page(qapp):
    register_gallery_resources()
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine, MENU_PAGE_URL)
    page = component.create(engine.rootContext())
    assert page is not None, [error.toString() for error in component.errors()]
    host = QQuickWindow()
    host.resize(1800, 1200)
    page.setParentItem(host.contentItem())
    page.setWidth(host.width())
    page.setHeight(host.height())
    host.show()
    _pump(500)
    try:
        yield host, page, warnings
    finally:
        _dispose(page)
        _dispose(component)
        host.close()
        _dispose(host)
        engine.collectGarbage()
        engine.clearComponentCache()
        _dispose(engine)


def test_gallery_data_widget_edge_wheel_belongs_to_outer_page(gallery_menu_page):
    """Whitespace beside each viewport must scroll the page, not its inner list.

    每个视口旁的空白区域必须滚动画廊页面，而不是误滚动内部列表。
    """
    window, page, warnings = gallery_menu_page
    outer = next(
        item
        for item in page.findChildren(QQuickItem)
        if "ScrollAreaDefault" in item.metaObject().className()
        and item.width() > 1000
    )

    for widget in _gallery_data_widgets(page):
        viewport = _viewport(widget)
        widget_pos = widget.mapToItem(window.contentItem(), 0, 0)
        viewport_pos = viewport.mapToItem(window.contentItem(), 0, 0)
        viewport_right = viewport_pos.x() + viewport.width()
        widget_right = widget_pos.x() + widget.width()
        assert viewport_right < widget_right, widget.metaObject().className()

        x = (viewport_right + widget_right) / 2
        y = viewport_pos.y() + viewport.height() / 2
        inner_before = float(viewport.property("contentY"))
        outer_before = float(outer.property("contentY"))

        _send_wheel(window, x, y)

        assert float(viewport.property("contentY")) == pytest.approx(
            inner_before, abs=0.5
        ), widget.metaObject().className()
        assert float(outer.property("contentY")) > outer_before + 1, (
            widget.metaObject().className(),
            outer.property("contentY"),
            inner_before,
            viewport.property("contentY"),
        )

    assert warnings == []
