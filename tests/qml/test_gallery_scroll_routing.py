# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared wheel ownership regressions. 共享滚轮所有权回归。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
    QObject,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "gallery-scroll-routing.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    width: 960
    height: 760
    visible: true

    ScrollArea {
        id: outer
        objectName: "outer"
        x: 30
        y: 20
        width: 900
        height: 700
        padding: 16

        Column {
            id: page
            width: outer.width - outer.padding * 2
            spacing: 32

            Slider {
                id: slider
                objectName: "slider"
                width: 540
                height: 40
                from: 0
                to: 100
                value: 50
                stepSize: 10
            }

            Rectangle { width: 1; height: 260; color: "transparent" }

            ScrollArea {
                id: inner
                objectName: "inner"
                width: 760
                height: 180
                orientation: Qt.Horizontal | Qt.Vertical
                padding: 8

                Rectangle {
                    id: innerContent
                    objectName: "innerContent"
                    width: 1500
                    height: 500
                    color: "#334455"
                }
            }

            Rectangle { width: 1; height: 90; color: "transparent" }

            TabWidget {
                id: tabs
                objectName: "tabs"
                width: 760
                height: 260
                tabWidth: 120
                tabs: [
                    "one", "two", "three", "four", "five", "six",
                    "seven", "eight", "nine", "ten"
                ]
            }

            Rectangle { width: 1; height: 700; color: "transparent" }
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _send_wheel(
    window: QQuickWindow,
    item: QQuickItem,
    delta_y: int = -120,
    local_x: float | None = None,
    local_y: float | None = None,
) -> QWheelEvent:
    point_x = item.width() / 2 if local_x is None else local_x
    point_y = item.height() / 2 if local_y is None else local_y
    scene_pos = item.mapToScene(QPointF(point_x, point_y))
    event = QWheelEvent(
        scene_pos,
        QPointF(window.x() + scene_pos.x(), window.y() + scene_pos.y()),
        QPoint(0, 0),
        QPoint(0, delta_y),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    _pump(240)
    return event


def _tab_flickable(window: QQuickWindow) -> QQuickItem:
    for item in window.findChildren(QQuickItem):
        parent = item.parentItem()
        if (
            parent is not None
            and "TabBar" in parent.metaObject().className()
            and item.metaObject().indexOfProperty("contentX") >= 0
            and item.metaObject().indexOfProperty("contentWidth") >= 0
        ):
            return item
    raise AssertionError("TabBar internal Flickable was not found")


def _scroll_viewport(control: QQuickItem) -> QQuickItem:
    candidates = [
        item for item in control.findChildren(QQuickItem)
        if "QQuickFlickable" in item.metaObject().className()
        and item.metaObject().indexOfProperty("contentY") >= 0
    ]
    assert candidates
    return max(candidates, key=lambda item: item.height())


def _reveal_item(outer, viewport, item) -> None:
    item_top = item.mapToItem(viewport, 0, 0).y()
    viewport.setProperty(
        "contentY",
        float(viewport.property("originY"))
        + max(0, item_top - viewport.height() / 2),
    )
    vertical_helpers = [
        helper for helper in outer.findChildren(QObject)
        if helper.metaObject().indexOfProperty("targetPos") >= 0
        and helper.property("orientation") == Qt.Orientation.Vertical.value
        and helper.metaObject().indexOfMethod("syncPosition()") >= 0
        and helper.parent() is not None
        and helper.parent().metaObject().className().startswith("ScrollAreaDefault")
        and helper.parent().height() >= outer.height() - 1
    ]
    assert len(vertical_helpers) == 1
    assert QMetaObject.invokeMethod(vertical_helpers[0], "syncPosition")
    _pump(80)


@pytest.fixture
def gallery_scene(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(120)
    try:
        yield window, warnings
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_slider_wheel_is_owned_by_slider_not_outer_scrollarea(gallery_scene):
    window, warnings = gallery_scene
    outer = window.findChild(QQuickItem, "outer")
    slider = window.findChild(QQuickItem, "slider")
    assert outer is not None and slider is not None
    outer_y_before = float(outer.property("contentY"))
    slider_before = float(slider.property("value"))

    _send_wheel(window, slider)

    assert float(slider.property("value")) != pytest.approx(slider_before)
    assert float(outer.property("contentY")) == pytest.approx(outer_y_before, abs=0.5)
    assert warnings == []


def test_tabbar_wheel_is_owned_by_inner_horizontal_viewport(gallery_scene):
    window, warnings = gallery_scene
    outer = window.findChild(QQuickItem, "outer")
    assert outer is not None
    viewport = _tab_flickable(window)
    outer_viewport = _scroll_viewport(outer)
    _reveal_item(outer, outer_viewport, viewport)
    outer_y_before = float(outer.property("contentY"))
    tab_x_before = float(viewport.property("contentX"))

    _send_wheel(window, viewport)

    assert float(viewport.property("contentX")) > tab_x_before + 1
    assert float(outer.property("contentY")) == pytest.approx(outer_y_before, abs=0.5)
    assert warnings == []


def test_inner_scrollarea_content_hit_has_one_scroll_owner(gallery_scene):
    window, warnings = gallery_scene
    outer = window.findChild(QQuickItem, "outer")
    inner = window.findChild(QQuickItem, "inner")
    content = window.findChild(QQuickItem, "innerContent")
    assert outer is not None and inner is not None and content is not None
    outer_y_before = float(outer.property("contentY"))
    inner_y_before = float(inner.property("contentY"))

    _send_wheel(window, content, local_x=100, local_y=50)

    assert float(inner.property("contentY")) > inner_y_before + 1
    assert float(outer.property("contentY")) == pytest.approx(outer_y_before, abs=0.5)
    assert warnings == []
