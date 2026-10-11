# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart scheduler lifecycle contracts. 图表调度生命周期合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import register_types

from chart_perf_shared import _animated_canvases, _loaders, _pump


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "chart-scheduler.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

ChartView {
    id: chart
    readonly property int lineType: Enums.chart.type_line
    readonly property int chartDuration: Enums.duration.chart
    width: 640
    height: 360
    deferAnimation: true
    animated: true
    showLegend: false
    chartType: Enums.chart.type_line
    chartData: [
        { label: "A", value: 1 },
        { label: "B", value: 3 },
        { label: "C", value: 2 }
    ]
}
"""


def _create_chart():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    chart = component.create(engine.rootContext())
    assert chart is not None, [error.toString() for error in component.errors()]
    window = QQuickWindow()
    window.resize(640, 360)
    chart.setParentItem(window.contentItem())
    window.show()
    _pump(20)
    return engine, component, chart, window


def _dispose(engine, component, chart, window):
    chart.setParentItem(None)
    window.close()
    window.deleteLater()
    chart.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QEventLoop().processEvents()


def test_scheduler_gate_pauses_canvas_and_hover(qapp):
    engine, component, chart, window = _create_chart()
    try:
        line_content = _loaders(chart)["lineContentLoader"].property("item")
        assert line_content is not None
        canvases = _animated_canvases(line_content)
        assert canvases
        canvas = canvases[0]
        before = canvas.property("animProgress")
        chart.setProperty("schedulerActive", False)
        _pump(chart.property("chartDuration") + 80)
        assert canvas.property("animProgress") == before
        mouse_areas = [
            child for child in line_content.findChildren(QObject)
            if child.metaObject().className() == "QQuickMouseArea"
        ]
        assert mouse_areas
        assert all(not area.property("enabled") for area in mouse_areas)

        chart.setProperty("schedulerActive", True)
        _pump(chart.property("chartDuration") + 80)
        assert canvas.property("animProgress") > before
        assert all(area.property("enabled") for area in mouse_areas)
    finally:
        _dispose(engine, component, chart, window)


def test_scheduler_gate_delays_entrance_animation(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    source = b"""
import QtQuick
import PrismQML
ChartView {
    width: 320
    height: 180
    deferAnimation: false
    schedulerActive: false
}
"""
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    chart = component.create(engine.rootContext())
    assert chart is not None, [error.toString() for error in component.errors()]
    try:
        _pump(200)
        assert chart.property("opacity") == 0
        chart.setProperty("schedulerActive", True)
        _pump(600)
        assert chart.property("opacity") == 1
    finally:
        chart.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QEventLoop().processEvents()


def test_scheduler_gate_keeps_latest_viewport_target(qapp):
    engine, component, chart, window = _create_chart()
    try:
        initial_start = chart.property("_renderStart")
        chart.setProperty("schedulerActive", False)
        chart.setProperty("viewportStart", 0.2)
        chart.setProperty("viewportEnd", 0.8)
        _pump(80)
        assert chart.property("_renderStart") == initial_start

        chart.setProperty("schedulerActive", True)
        _pump(chart.property("chartDuration") + 80)
        assert chart.property("_renderStart") == 0.2
        assert chart.property("_renderEnd") == 0.8
    finally:
        _dispose(engine, component, chart, window)


def test_scheduler_gate_defers_projection_and_xy_stats_until_restore(qapp):
    engine, component, chart, window = _create_chart()
    try:
        xy_chart = chart.property("_xyChartBase")
        assert xy_chart is not None
        projection_revision = chart.property("_projectionRevision")
        stats_revision = xy_chart.property("_statsRevision")
        previous_data = chart.property("_viewChartData").toVariant()
        assert len(previous_data) == 3

        chart.setProperty("schedulerActive", False)
        chart.setProperty(
            "chartData",
            [
                {"label": "D", "value": 10},
                {"label": "E", "value": 20},
            ],
        )
        chart.setProperty(
            "series",
            [{"name": "Series", "values": [10, 20, 15, 25]}],
        )
        _pump(80)

        assert chart.property("_projectionRevision") == projection_revision
        assert xy_chart.property("_statsRevision") == stats_revision
        assert len(chart.property("_viewChartData").toVariant()) == len(previous_data)

        chart.setProperty("schedulerActive", True)
        _pump(80)

        assert chart.property("_projectionRevision") == projection_revision + 1
        assert xy_chart.property("_statsRevision") == stats_revision + 1
        assert len(chart.property("_viewChartData").toVariant()) == 2
        assert len(chart.property("_viewSeries").toVariant()) == 1
        assert xy_chart.property("_calculatedValueRange").toVariant()["max"] > 25
    finally:
        _dispose(engine, component, chart, window)
