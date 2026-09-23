# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Line marker viewport clipping regression. 折线标记视口裁剪回归。"""

from pathlib import Path

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
        series: [{ name: "Rainfall", values: [200, 5, 2], color: "#0078d4" }]
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


