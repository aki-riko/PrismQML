# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Inverted-wheel behavior across shared PrismQML scroll surfaces."""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "inverted-wheel-surfaces.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent
import "../../prismqml/PrismQML/controls/containers" as Containers
import "../../prismqml/PrismQML/controls/containers" as ScrollContainers

Window {
    width: 720
    height: 700
    visible: true

    Containers.Flickable {
        id: basicFlickable
        objectName: "basicFlickable"
        x: 16
        y: 16
        width: 320
        height: 180
        interactive: false
        contentWidth: width
        contentHeight: 720
        Rectangle { width: basicFlickable.width; height: 720 }
    }

    Fluent.ListView {
        id: dataListView
        objectName: "dataListView"
        x: 368
        y: 16
        width: 320
        height: 180
        dragScrollEnabled: false
        showFooter: false
        model: 40
        delegate: Rectangle {
            required property int index
            width: ListView.view.width
            height: 30
        }
    }

    Fluent.ListWidget {
        id: listWidget
        objectName: "listWidget"
        x: 16
        y: 224
        width: 320
        height: 180
        dragScrollEnabled: false
        model: {
            var items = []
            for (var i = 0; i < 40; i++) items.push("row " + i)
            return items
        }
    }

    Fluent.TreeWidget {
        id: treeWidget
        objectName: "treeWidget"
        x: 368
        y: 224
        width: 320
        height: 180
        dragScrollEnabled: false
        model: {
            var items = []
            for (var i = 0; i < 40; i++) items.push({ "text": "node " + i })
            return items
        }
    }

    ScrollContainers.ScrollArea {
        id: nestedScrollArea
        objectName: "nestedScrollArea"
        x: 16
        y: 430
        width: 672
        height: 240

        Column {
            width: nestedScrollArea.width
            spacing: 12

            Fluent.TimelineCore {
                id: nestedTimeline
                objectName: "nestedTimeline"
                width: 320
                height: 180
                virtualized: true
                items: {
                    var groups = []
                    for (var groupIndex = 0; groupIndex < 8; groupIndex++) {
                        var cards = []
                        for (var cardIndex = 0; cardIndex < 12; cardIndex++) {
                            cards.push({
                                "text": "timeline " + groupIndex + " / " + cardIndex
                            })
                        }
                        groups.push({ "title": "group " + groupIndex, "cards": cards })
                    }
                    return groups
                }
            }

            Fluent.ListWidget {
                id: nestedListWidget
                objectName: "nestedListWidget"
                width: 320
                height: 180
                dragScrollEnabled: false
                model: {
                    var items = []
                    for (var i = 0; i < 40; i++) items.push("nested row " + i)
                    return items
                }
            }

            Rectangle { width: 1; height: 180 }
        }
    }
}
"""
SURFACE_NAMES = ("basicFlickable", "dataListView", "listWidget", "treeWidget")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(root: QQuickItem):
    pending = [root]
    seen = set()
    keep_alive = []
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        keep_alive.append(item)
        if isinstance(item, QQuickItem):
            yield item
            pending.extend(item.childItems())
        pending.extend(item.children())


def _viewport(control: QQuickItem) -> QQuickItem:
    candidates = [
        item
        for item in _descendants(control)
        if item.metaObject().indexOfProperty("contentY") >= 0
        and item.metaObject().indexOfProperty("contentHeight") >= 0
        and any(
            marker in item.metaObject().className()
            for marker in ("Flickable", "ListView", "GridView")
        )
    ]
    assert candidates, control.objectName()
    return max(candidates, key=lambda item: item.height())


def _scroll_helper(control: QQuickItem) -> QObject:
    candidates = [
        item
        for item in _descendants(control)
        if item.metaObject().indexOfProperty("targetPos") >= 0
        and item.metaObject().indexOfProperty("step") >= 0
    ]
    assert len(candidates) == 1, control.objectName()
    return candidates[0]


def _vertical_scroll_helper(control: QQuickItem) -> QObject:
    candidates = [
        item
        for item in _descendants(control)
        if item.metaObject().indexOfProperty("targetPos") >= 0
        and item.metaObject().indexOfProperty("orientation") >= 0
        and item.property("orientation") == Qt.Orientation.Vertical.value
        and item.parentItem() is not None
        and "ScrollAreaDefault" in item.parentItem().metaObject().className()
    ]
    assert len(candidates) == 1, control.objectName()
    return candidates[0]


def _send_wheel(
    window: QQuickWindow,
    item: QQuickItem,
    angle_delta: QPoint,
    inverted: bool,
) -> QWheelEvent:
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    event = QWheelEvent(
        position,
        QPointF(window.x() + position.x(), window.y() + position.y()),
        QPoint(0, 0),
        angle_delta,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        inverted,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event


@pytest.fixture
def scroll_surfaces(qapp):
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
    _pump(80)
    controls = {
        name: window.findChild(QQuickItem, name) for name in SURFACE_NAMES
    }
    assert all(controls.values()), controls
    try:
        yield window, controls, warnings
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


@pytest.mark.parametrize("surface", SURFACE_NAMES)
def test_same_physical_wheel_direction_matches_for_inverted_events(
    scroll_surfaces, surface
):
    window, controls, warnings = scroll_surfaces
    control = controls[surface]
    viewport = _viewport(control)
    helper = _scroll_helper(control)
    assert viewport.property("contentHeight") > viewport.height()
    assert viewport.property("interactive") is False

    origin = float(viewport.property("originY"))
    viewport.setProperty("contentY", origin)
    assert QMetaObject.invokeMethod(helper, "syncPosition")
    assert QCoreApplication.processEvents() is None
    _send_wheel(window, viewport, QPoint(0, -120), inverted=False)
    normal_target = float(helper.property("targetPos"))
    assert normal_target > origin
    assert _wait_for(
        lambda: float(viewport.property("contentY"))
        == pytest.approx(normal_target, abs=0.5)
    )
    normal_delta = normal_target - origin

    viewport.setProperty("contentY", origin)
    assert QMetaObject.invokeMethod(helper, "syncPosition")
    assert QCoreApplication.processEvents() is None
    _send_wheel(window, viewport, QPoint(0, 120), inverted=True)
    inverted_target = float(helper.property("targetPos"))
    assert inverted_target > origin
    assert _wait_for(
        lambda: float(viewport.property("contentY"))
        == pytest.approx(inverted_target, abs=0.5)
    )
    inverted_delta = inverted_target - origin

    assert normal_delta > 0
    assert inverted_delta == pytest.approx(normal_delta, rel=0.03, abs=1.0)
    assert warnings == []


def test_wheel_utility_normalizes_horizontal_delta_axis(scroll_surfaces):
    window, controls, warnings = scroll_surfaces
    viewport = _viewport(controls["basicFlickable"])
    origin = float(viewport.property("contentY"))

    _send_wheel(window, viewport, QPoint(-120, 0), inverted=False)
    _send_wheel(window, viewport, QPoint(120, 0), inverted=True)

    assert float(viewport.property("contentY")) == pytest.approx(origin)
    assert warnings == []


def test_gallery_style_outer_scrollarea_routes_wheel_to_inner_list(scroll_surfaces):
    window, controls, warnings = scroll_surfaces
    outer = window.findChild(QQuickItem, "nestedScrollArea")
    inner = window.findChild(QQuickItem, "nestedListWidget")
    assert outer is not None
    assert inner is not None
    outer_viewport = _viewport(outer)
    inner_viewport = _viewport(inner)
    assert outer_viewport.property("contentHeight") > outer_viewport.height()
    assert inner_viewport.property("contentHeight") > inner_viewport.height()
    outer_origin = float(outer_viewport.property("originY"))
    inner_origin = float(inner_viewport.property("originY"))
    outer_helper = _vertical_scroll_helper(outer)
    inner_top = inner_viewport.mapToItem(outer_viewport, 0, 0).y()
    outer_viewport.setProperty("contentY", outer_origin + max(0, inner_top - 10))
    assert QMetaObject.invokeMethod(outer_helper, "syncPosition")
    assert _wait_for(lambda: inner_viewport.isVisible())
    visible_outer_y = float(outer_viewport.property("contentY"))

    _send_wheel(window, inner_viewport, QPoint(0, -120), inverted=False)
    inner_helper = _scroll_helper(inner)

    assert _wait_for(
        lambda: float(inner_viewport.property("contentY")) > inner_origin + 1
    ), {
        "outerY": outer_viewport.property("contentY"),
        "innerY": inner_viewport.property("contentY"),
    }
    assert float(inner_helper.property("targetPos")) > inner_origin
    assert inner_helper.property("isOvershot") is False
    assert float(outer_viewport.property("contentY")) == pytest.approx(visible_outer_y, abs=0.5)
    _send_wheel(window, inner_viewport, QPoint(0, 120), inverted=False)
    assert _wait_for(
        lambda: float(inner_viewport.property("contentY"))
        == pytest.approx(inner_origin, abs=0.5)
    )
    assert float(outer_viewport.property("contentY")) == pytest.approx(visible_outer_y, abs=0.5)
    assert warnings == []


def test_gallery_style_outer_scrollarea_routes_wheel_to_timeline(scroll_surfaces):
    window, controls, warnings = scroll_surfaces
    outer = window.findChild(QQuickItem, "nestedScrollArea")
    timeline = window.findChild(QQuickItem, "nestedTimeline")
    assert outer is not None
    assert timeline is not None
    outer_viewport = _viewport(outer)
    timeline_viewport, helper = _viewport_and_helper(timeline)
    assert outer_viewport.property("contentHeight") > outer_viewport.height()
    assert timeline_viewport.property("contentHeight") > timeline_viewport.height()
    outer_origin = float(outer_viewport.property("originY"))
    timeline_origin = float(timeline_viewport.property("originY"))
    outer_helper = _vertical_scroll_helper(outer)
    timeline_top = timeline_viewport.mapToItem(outer_viewport, 0, 0).y()
    outer_viewport.setProperty("contentY", outer_origin + max(0, timeline_top - 10))
    assert QMetaObject.invokeMethod(outer_helper, "syncPosition")
    assert _wait_for(
        lambda: timeline_viewport.mapToItem(outer_viewport, 0, 0).y()
        < outer_viewport.height()
    )
    visible_outer_y = float(outer_viewport.property("contentY"))

    _send_wheel(window, timeline_viewport, QPoint(0, -120), inverted=False)

    assert _wait_for(
        lambda: float(timeline_viewport.property("contentY"))
        > timeline_origin + 1
    ), {
        "outerY": outer_viewport.property("contentY"),
        "timelineY": timeline_viewport.property("contentY"),
        "target": helper.property("targetPos"),
    }
    assert float(helper.property("targetPos")) > timeline_origin
    assert helper.property("isOvershot") is False
    assert float(outer_viewport.property("contentY")) == pytest.approx(visible_outer_y, abs=0.5)
    _send_wheel(window, timeline_viewport, QPoint(0, 120), inverted=False)
    assert _wait_for(
        lambda: float(timeline_viewport.property("contentY"))
        == pytest.approx(timeline_origin, abs=0.5)
    )
    assert float(outer_viewport.property("contentY")) == pytest.approx(visible_outer_y, abs=0.5)
    assert warnings == []


def _viewport_and_helper(control):
    viewport = _viewport(control)
    helper = _scroll_helper(control)
    return viewport, helper
