# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Line marker viewport clipping regression. 折线标记视口裁剪回归。"""

from pathlib import Path

import pytest

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "chart-data-marker-clipping.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Window {
    id: root
    width: 700
    height: 700
    visible: true

    ChartView {
        id: chart
        objectName: "chart"
        x: 20
        y: 20
        width: 640
        height: 270
        deferAnimation: true
        animated: false
        chartType: Enums.chart.type_line
        showLegend: false
        showMinMax: true
        boundaryGap: false
        series: [
            { name: "Highest", values: [13, 8, 9, 7, 8, 2, 1], color: "#0078d4" },
            { name: "Lowest", values: [-2, 3, 5, 4, 3, 1, 0], color: "#107c10" }
        ]
    }

    ChartView {
        id: barChart
        objectName: "barChart"
        x: 20
        y: 320
        width: 640
        height: 300
        deferAnimation: true
        animated: false
        chartType: Enums.chart.type_bar
        showLegend: false
        showMinMax: true
        boundaryGap: false
        series: [
            { name: "Rainfall", values: [2, 162.2, 18, 15, 25, 7], color: "#0078d4" },
            { name: "Evaporation", values: [3, 182.2, 50, 12, 18, 2.3], color: "#107c10" }
        ]
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()



def _visual_items(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _visual_item(root: QQuickItem, object_name: str):
    return next(
        (item for item in _visual_items(root) if item.objectName() == object_name),
        None,
    )


def _create_scene():
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
    return engine, component, window, warnings


def test_line_markers_render_outside_clip_and_follow_chart_viewport(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        chart = window.findChild(QQuickItem, "chart")
        assert chart is not None
        marker_layer = chart.findChild(QQuickItem, "chartMarkerLayer")
        clip = chart.findChild(QQuickItem, "chartViewportClip")
        line_component = chart.findChild(QQuickItem, "chartLineMarkers")
        line_max = _visual_item(chart, "lineMaxMarker")
        line_min = _visual_item(chart, "lineMinMarker")
        assert marker_layer is not None and clip is not None
        assert line_component is not None
        assert line_max is not None and line_min is not None
        assert marker_layer.parentItem() is clip.parentItem()
        assert clip.clip()
        assert line_max.isVisible() and line_min.isVisible()
        marker_geometry = [
            (item.objectName(), item.mapToItem(clip, 0, 0).x(),
             item.mapToItem(clip, 0, 0).y(), item.height())
            for item in _visual_items(chart)
            if item.objectName() in ("lineMaxMarker", "lineMinMarker")
        ]
        assert any(x < 0 for _name, x, _y, _height in marker_geometry), marker_geometry
        assert any(
            item.mapToItem(clip, 0, 0).x() + item.width() > clip.width()
            for item in _visual_items(chart)
            if item.objectName() in ("lineMaxMarker", "lineMinMarker")
        ), marker_geometry

        chart.setProperty("viewportStart", 0.2)
        chart.setProperty("viewportEnd", 0.8)
        _pump(250)
        moved_max = _visual_item(chart, "lineMaxMarker")
        moved_min = _visual_item(chart, "lineMinMarker")
        assert moved_max is not None and moved_min is not None
        assert moved_max.isVisible() and moved_min.isVisible()
        assert warnings == []
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()

def test_bar_markers_follow_the_rendered_bar_geometry_outside_plot_clip(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        chart = window.findChild(QQuickItem, "barChart")
        assert chart is not None
        clip = chart.findChild(QQuickItem, "chartViewportClip")
        marker_layer = chart.findChild(QQuickItem, "chartMarkerLayer")
        content = chart.property("_barContent")
        marker_component = chart.findChild(QQuickItem, "chartBarMarkers")
        assert clip is not None and marker_layer is not None and content is not None
        assert marker_component is not None
        assert marker_layer.parentItem() is clip.parentItem()
        max_marker = _visual_item(chart, "barMaxMarker_1")
        min_marker = _visual_item(chart, "barMinMarker_0")
        assert max_marker is not None and min_marker is not None
        positions = content.property("barPositions").toVariant()
        max_position = positions[1][1]
        min_position = positions[0][0]
        expected_max = content.mapToItem(
            marker_component, max_position["x"], max_position["barTop"]
        )
        expected_min = content.mapToItem(
            marker_component, min_position["x"], min_position["barTop"]
        )
        assert max_marker.x() + max_marker.width() / 2 == pytest.approx(expected_max.x())
        assert max_marker.y() == pytest.approx(
            max(0, expected_max.y() - max_marker.height() - 6)
        )
        assert min_marker.x() + min_marker.width() / 2 == pytest.approx(expected_min.x())
        assert min_marker.y() == pytest.approx(
            min(marker_layer.height() - min_marker.height(),
                expected_min.y() + min_marker.height() + 6)
        )
        assert max_marker.isVisible() and min_marker.isVisible()
        assert warnings == []
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()

