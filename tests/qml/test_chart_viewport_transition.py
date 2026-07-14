# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart viewport transition regressions. 图表视窗过渡回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
CHART_VIEW_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Chart" / "ChartView.qml"
)
CHART_DATA_ZOOM_SOURCE = CHART_VIEW_SOURCE.with_name("ChartDataZoom.qml")
LINE_CHART_SOURCE = CHART_VIEW_SOURCE.parent / "_internal" / "LineChartContent.qml"
CHART_ENUM_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Chart.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "chart-viewport-transition.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

ChartView {
    id: chart

    readonly property real renderStart: _renderStart
    readonly property real renderEnd: _renderEnd
    readonly property int renderedPointCount: _viewChartData.length
    readonly property int transitionDuration: Enums.duration.normal
    readonly property real zoomInFactor: Enums.chart.zoom_in_factor
    readonly property real zoomAnchor: 0.25
    property bool wheelZoomRequested: false

    onWheelZoomRequestedChanged: {
        if (wheelZoomRequested) wheelZoomed(120, zoomAnchor)
    }

    width: 640
    height: 360
    deferAnimation: true
    animated: true
    chartType: Enums.chart.type_line
    dataZoomEnabled: true
    chartData: {
        var points = []
        for (var index = 0; index < 100; index++) {
            points.push({ label: "P" + index, value: index })
        }
        return points
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_chart():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    chart = component.create(engine.rootContext())
    assert chart is not None, [error.toString() for error in component.errors()]
    _pump(1)
    return engine, component, chart


def test_wheel_zoom_animates_the_render_viewport(qapp):
    engine, component, chart = _create_chart()
    try:
        assert chart.property("renderStart") == pytest.approx(0)
        assert chart.property("renderEnd") == pytest.approx(1)
        assert chart.property("renderedPointCount") == 100

        zoom_span = chart.property("zoomInFactor")
        zoom_anchor = chart.property("zoomAnchor")
        target_start = zoom_anchor - zoom_span * zoom_anchor
        target_end = target_start + zoom_span
        chart.setProperty("wheelZoomRequested", True)

        assert chart.property("viewportStart") == pytest.approx(target_start)
        assert chart.property("viewportEnd") == pytest.approx(target_end)
        assert chart.property("renderStart") < target_start
        assert chart.property("renderEnd") > target_end

        transition_duration = chart.property("transitionDuration")
        _pump(transition_duration // 2)

        middle_start = chart.property("renderStart")
        middle_end = chart.property("renderEnd")
        middle_count = chart.property("renderedPointCount")
        assert 0 < middle_start < target_start
        assert target_end < middle_end < 1
        assert 70 < middle_count < 100

        _pump(transition_duration)
        assert chart.property("renderStart") == pytest.approx(target_start, abs=0.001)
        assert chart.property("renderEnd") == pytest.approx(target_end, abs=0.001)
        assert 70 <= chart.property("renderedPointCount") <= 72
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_direct_manipulation_updates_render_viewport_immediately(qapp):
    engine, component, chart = _create_chart()
    try:
        chart.setProperty("viewportStart", 0.2)
        chart.setProperty("viewportEnd", 0.8)
        _pump(chart.property("transitionDuration") // 2)
        assert 0 < chart.property("renderStart") < 0.2

        chart.setProperty("_viewportInteractive", True)
        chart.setProperty("viewportStart", 0.1)
        chart.setProperty("viewportEnd", 0.9)
        _pump(1)

        assert chart.property("renderStart") == pytest.approx(0.1)
        assert chart.property("renderEnd") == pytest.approx(0.9)
        assert 80 <= chart.property("renderedPointCount") <= 82
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_chart_zoom_uses_shared_tokens_and_render_values():
    chart_view_source = CHART_VIEW_SOURCE.read_text(encoding="utf-8")
    data_zoom_source = CHART_DATA_ZOOM_SOURCE.read_text(encoding="utf-8")
    line_chart_source = LINE_CHART_SOURCE.read_text(encoding="utf-8")
    chart_enum_source = CHART_ENUM_SOURCE.read_text(encoding="utf-8")
    zoom_consumers = chart_view_source + data_zoom_source + line_chart_source

    assert "Behavior on _renderStart" in chart_view_source
    assert "Behavior on _renderEnd" in chart_view_source
    assert "Behavior on viewportStart" not in chart_view_source
    assert "id: _renderTimer" not in chart_view_source
    assert "duration: Enums.duration.normal" in chart_view_source
    assert "viewportStart: control._renderStart" in chart_view_source
    assert "viewportEnd: control._renderEnd" in chart_view_source

    for token in (
        "zoom_in_factor",
        "zoom_out_factor",
        "minimum_viewport_span",
        "default_anchor_ratio",
        "viewport_slider_steps",
        "lttb_threshold",
    ):
        assert f" {token}:" in chart_enum_source
        assert f"Enums.chart.{token}" in zoom_consumers

    assert "duration: 120" not in chart_view_source
    assert "interval: 50" not in chart_view_source
    assert "interval: Enums.duration.slow" in data_zoom_source
