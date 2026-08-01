# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart viewport transition regressions. 图表视窗过渡回归。"""

import json
import math
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
CHART_VIEW_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Chart" / "ChartView.qml"
)
CHART_DATA_ZOOM_SOURCE = CHART_VIEW_SOURCE.with_name("ChartDataZoom.qml")
CHART_DATA_ZOOM_LAYER_SOURCE = (
    CHART_VIEW_SOURCE.parent / "_internal" / "ChartDataZoomLayer.qml"
)
LINE_CHART_SOURCE = CHART_VIEW_SOURCE.parent / "_internal" / "LineChartContent.qml"
XY_CHART_CORE_SOURCE = CHART_VIEW_SOURCE.parent / "_internal" / "XYChartCore.qml"
XY_SINGLE_TOOLTIP_SOURCE = (
    CHART_VIEW_SOURCE.parent / "_internal" / "XYSingleTooltip.qml"
)
XY_MULTI_TOOLTIP_SOURCE = (
    CHART_VIEW_SOURCE.parent / "_internal" / "XYMultiTooltip.qml"
)
VIEWPORT_ANIMATOR_SOURCE = (
    CHART_VIEW_SOURCE.parent / "_internal" / "ChartViewportAnimator.qml"
)
VIEWPORT_TRANSITION_SOURCE = (
    CHART_VIEW_SOURCE.parent / "_internal" / "ChartViewportTransition.js"
)
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
    readonly property real zoomOutFactor: Enums.chart.zoom_out_factor
    readonly property real zoomAnchor: 0.25
    readonly property real viewportScale: _viewportScale
    readonly property real viewportOffset: _viewportOffsetRatio
    readonly property real visualStart: _visualStart
    readonly property real visualEnd: _visualEnd
    readonly property bool transitionActive: _viewportTransitionActive
    readonly property real mappedMidpoint: viewportOffset + viewportScale * 0.5
    readonly property string renderedValuesJson: JSON.stringify(
        _viewChartData.map(function(item) { return item.value })
    )
    readonly property string renderedSeriesValuesJson: JSON.stringify(
        _viewSeries.length > 0 ? _viewSeries[0].values : []
    )
    readonly property var sourcePoints: {
        var points = []
        for (var index = 0; index < 100; index++) {
            points.push({
                label: "P" + index,
                value: (index * index + 17 * index) % 997
            })
        }
        return points
    }
    readonly property var sourceValues: sourcePoints.map(function(item) {
        return item.value
    })
    property int wheelZoomRequest: 0
    property int wheelDelta: 120
    property bool seriesMode: false

    onWheelZoomRequestChanged: {
        if (wheelZoomRequest > 0) wheelZoomed(wheelDelta, zoomAnchor)
    }

    width: 640
    height: 360
    deferAnimation: true
    animated: true
    chartType: Enums.chart.type_line
    dataZoomEnabled: true
    chartData: seriesMode ? [] : sourcePoints
    series: seriesMode ? [{ name: "series", values: sourceValues }] : []
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_transition(chart, timeout_ms: int = 2_000) -> None:
    for _ in range(timeout_ms // 10):
        if not chart.property("transitionActive"):
            return
        _pump(10)
    assert not chart.property("transitionActive")


def _reference_bucket_average(values: list[int], start: int, end: int):
    if start >= end:
        return start - 1, values[start - 1]
    average_x = (start + end - 1) / 2
    average_y = sum(values[start:end]) / (end - start)
    return average_x, average_y


def _reference_lttb_indices(values: list[int], threshold: int) -> list[int]:
    count = len(values)
    if threshold >= count or threshold < 3:
        return list(range(count))
    bucket_size = (count - 2) / (threshold - 2)
    selected = [0]
    anchor = 0
    for bucket in range(threshold - 2):
        start = math.floor((bucket + 1) * bucket_size) + 1
        end = min(math.floor((bucket + 2) * bucket_size) + 1, count - 1)
        if start >= end:
            continue
        next_start = end
        next_end = min(math.floor((bucket + 3) * bucket_size) + 1, count)
        average_x, average_y = _reference_bucket_average(
            values, next_start, next_end
        )
        anchor_y = values[anchor]
        anchor = max(
            range(start, end),
            key=lambda index: abs(
                (anchor - average_x) * (values[index] - anchor_y)
                - (anchor - index) * (average_y - anchor_y)
            ),
        )
        selected.append(anchor)
    selected.append(count - 1)
    return selected


def _create_chart(point_count: int = 100):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    scene_source = SCENE_SOURCE.replace(
        b"index < 100;", f"index < {point_count};".encode("ascii")
    )
    component.setData(scene_source, SCENE_URL)
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


def test_zoom_in_animates_the_visual_layer_before_committing_data(qapp):
    engine, component, chart = _create_chart()
    try:
        assert chart.property("renderStart") == pytest.approx(0)
        assert chart.property("renderEnd") == pytest.approx(1)
        assert chart.property("renderedPointCount") == 100

        zoom_span = chart.property("zoomInFactor")
        zoom_anchor = chart.property("zoomAnchor")
        target_start = zoom_anchor - zoom_span * zoom_anchor
        target_end = target_start + zoom_span
        chart.setProperty("wheelZoomRequest", 1)
        _pump(1)

        assert chart.property("viewportStart") == pytest.approx(target_start)
        assert chart.property("viewportEnd") == pytest.approx(target_end)
        assert chart.property("renderStart") < target_start
        assert chart.property("renderEnd") > target_end

        transition_duration = chart.property("transitionDuration")
        _pump(transition_duration // 2)

        middle_count = chart.property("renderedPointCount")
        assert chart.property("renderStart") == pytest.approx(0)
        assert chart.property("renderEnd") == pytest.approx(1)
        assert middle_count == 100
        assert 1 < chart.property("viewportScale") < 1 / zoom_span
        assert 0 < chart.property("visualStart") < target_start
        assert target_end < chart.property("visualEnd") < 1

        _wait_for_transition(chart)
        assert chart.property("renderStart") == pytest.approx(target_start, abs=0.001)
        assert chart.property("renderEnd") == pytest.approx(target_end, abs=0.001)
        assert chart.property("viewportScale") == pytest.approx(1)
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
        assert chart.property("renderStart") == pytest.approx(0)
        assert chart.property("viewportScale") > 1

        chart.setProperty("_viewportInteractive", True)
        chart.setProperty("viewportStart", 0.1)
        chart.setProperty("viewportEnd", 0.9)
        _pump(10)

        assert chart.property("renderStart") == pytest.approx(0.1)
        assert chart.property("renderEnd") == pytest.approx(0.9)
        assert chart.property("viewportScale") == pytest.approx(1)
        assert 80 <= chart.property("renderedPointCount") <= 82
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_data_zoom_syncs_external_viewport_to_range_slider(qapp):
    engine, component, chart = _create_chart()
    try:
        data_zoom = next(
            item
            for item in chart.findChildren(QObject)
            if item.metaObject().indexOfProperty("_suppressSliderUpdate") >= 0
        )
        range_slider = next(
            item
            for item in data_zoom.findChildren(QObject)
            if item.metaObject().className().startswith("SliderCore")
        )
        slider_steps = range_slider.property("to")

        data_zoom.setProperty("viewportStart", 0.2)
        data_zoom.setProperty("viewportEnd", 0.75)
        _pump(1)

        assert range_slider.property("firstValue") == round(0.2 * slider_steps)
        assert range_slider.property("secondValue") == round(0.75 * slider_steps)
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_small_dataset_moves_continuously_without_mid_animation_reslicing(qapp):
    engine, component, chart = _create_chart(point_count=10)
    try:
        chart.setProperty("wheelZoomRequest", 1)
        active_positions = []
        active_point_counts = []
        for _ in range(5):
            _pump(20)
            if chart.property("transitionActive"):
                active_positions.append(chart.property("mappedMidpoint"))
                active_point_counts.append(chart.property("renderedPointCount"))

        assert active_point_counts
        assert active_point_counts == [10] * len(active_point_counts)
        assert len({round(value, 4) for value in active_positions}) >= 3
        assert active_positions == sorted(active_positions)

        _wait_for_transition(chart)
        assert chart.property("viewportScale") == pytest.approx(1)
        assert chart.property("renderedPointCount") == 8
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_zoom_out_commits_the_target_slice_once_then_animates_to_identity(qapp):
    engine, component, chart = _create_chart()
    try:
        chart.setProperty("wheelZoomRequest", 1)
        _pump(1)
        _wait_for_transition(chart)
        previous_start = chart.property("visualStart")
        previous_end = chart.property("visualEnd")
        previous_span = previous_end - previous_start

        chart.setProperty("wheelDelta", -120)
        chart.setProperty("wheelZoomRequest", 2)
        _pump(1)

        target_span = previous_span * chart.property("zoomOutFactor")
        anchor = previous_start + previous_span * chart.property("zoomAnchor")
        target_start = anchor - target_span * chart.property("zoomAnchor")
        target_end = target_start + target_span
        assert chart.property("viewportStart") == pytest.approx(target_start)
        assert chart.property("viewportEnd") == pytest.approx(target_end)
        assert chart.property("renderStart") == pytest.approx(target_start)
        assert chart.property("renderEnd") == pytest.approx(target_end)
        assert chart.property("renderedPointCount") > 71
        assert chart.property("viewportScale") > 1

        _pump(chart.property("transitionDuration") // 2)
        assert target_start < chart.property("visualStart") < previous_start
        assert previous_end < chart.property("visualEnd") < target_end

        _wait_for_transition(chart)
        assert chart.property("viewportScale") == pytest.approx(1)
        assert chart.property("visualStart") == pytest.approx(target_start, abs=0.001)
        assert chart.property("visualEnd") == pytest.approx(target_end, abs=0.001)
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_large_dataset_keeps_the_lttb_slice_stable_during_zoom_in(qapp):
    engine, component, chart = _create_chart(point_count=10_000)
    try:
        initial_count = chart.property("renderedPointCount")
        chart.setProperty("wheelZoomRequest", 1)
        _pump(chart.property("transitionDuration") // 2)

        assert chart.property("renderStart") == pytest.approx(0)
        assert chart.property("renderEnd") == pytest.approx(1)
        assert chart.property("renderedPointCount") == initial_count
        assert chart.property("viewportScale") > 1
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_range_lttb_matches_the_allocating_reference(qapp):
    point_count = 1_000
    engine, component, chart = _create_chart(point_count=point_count)
    try:
        chart.setProperty("wheelZoomRequest", 1)
        _pump(1)
        _wait_for_transition(chart)

        render_start = chart.property("renderStart")
        render_end = chart.property("renderEnd")
        lower = max(0, math.floor(point_count * render_start))
        upper = min(point_count, math.ceil(point_count * render_end))
        all_values = [(index * index + 17 * index) % 997 for index in range(point_count)]
        source_values = all_values[lower:upper]
        expected_indices = _reference_lttb_indices(source_values, 600)
        expected_values = [source_values[index] for index in expected_indices]
        actual_values = json.loads(chart.property("renderedValuesJson"))
        assert actual_values == expected_values

        chart.setProperty("animated", False)
        chart.setProperty("seriesMode", True)
        _pump(10)
        actual_series_values = json.loads(chart.property("renderedSeriesValuesJson"))
        assert actual_series_values == expected_values
    finally:
        chart.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_chart_zoom_uses_shared_tokens_and_render_values():
    chart_view_source = CHART_VIEW_SOURCE.read_text(encoding="utf-8")
    data_zoom_source = CHART_DATA_ZOOM_SOURCE.read_text(encoding="utf-8")
    data_zoom_layer_source = CHART_DATA_ZOOM_LAYER_SOURCE.read_text(encoding="utf-8")
    line_chart_source = LINE_CHART_SOURCE.read_text(encoding="utf-8")
    xy_chart_core_source = XY_CHART_CORE_SOURCE.read_text(encoding="utf-8")
    single_tooltip_source = XY_SINGLE_TOOLTIP_SOURCE.read_text(encoding="utf-8")
    multi_tooltip_source = XY_MULTI_TOOLTIP_SOURCE.read_text(encoding="utf-8")
    animator_source = VIEWPORT_ANIMATOR_SOURCE.read_text(encoding="utf-8")
    transition_source = VIEWPORT_TRANSITION_SOURCE.read_text(encoding="utf-8")
    chart_enum_source = CHART_ENUM_SOURCE.read_text(encoding="utf-8")
    zoom_consumers = (
        chart_view_source
        + data_zoom_source
        + data_zoom_layer_source
        + line_chart_source
        + xy_chart_core_source
        + single_tooltip_source
        + multi_tooltip_source
        + animator_source
        + transition_source
    )

    assert "ChartViewportAnimator" in chart_view_source
    assert "Behavior on _renderStart" not in chart_view_source
    assert "Behavior on _renderEnd" not in chart_view_source
    assert "Behavior on viewportStart" not in chart_view_source
    assert "id: _renderTimer" not in chart_view_source
    assert "duration: Enums.duration.normal" in animator_source
    assert "viewportStart: root.chart ? root.chart._visualStart : 0" in data_zoom_layer_source
    assert "viewportEnd: root.chart ? root.chart._visualEnd : 1" in data_zoom_layer_source
    assert "xScale: control._isHorizontalBar ? 1 : control._viewportScale" in chart_view_source
    assert "yScale: control._isHorizontalBar ? control._viewportScale : 1" in chart_view_source
    assert "viewportScale: control._viewportScale" in chart_view_source
    tooltip_source = single_tooltip_source + multi_tooltip_source
    assert "chart._viewChartData" in tooltip_source
    assert "chart._viewSeries" in tooltip_source
    assert "chart.chartData[chart._hovered" not in tooltip_source
    assert "chart.series[i]" not in tooltip_source
    assert "xScale: root.viewportScale" in xy_chart_core_source
    assert "yScale: root.viewportScale" in xy_chart_core_source
    assert "y: chartAreaItem.y + root.viewportOffsetRatio" not in (
        xy_chart_core_source.split("id: yAxisLabels", 1)[1]
        .split("id: horizontalYAxisLabels", 1)[0]
    )
    assert (
        "id: horizontalYAxisLabels\n"
        "        x: Enums.spacing.s\n"
        "        y: chartAreaItem.y + root.viewportOffsetRatio * chartAreaItem.height"
    ) in xy_chart_core_source
    assert (
        "id: horizontalXAxisLabels\n\n"
        "        x: chartAreaItem.x"
    ) in xy_chart_core_source
    assert (
        "id: xAxisLabels\n"
        "        x: chartAreaItem.x + root.viewportOffsetRatio * chartAreaItem.width"
    ) in xy_chart_core_source
    assert (
        "id: scatterXAxisLabels\n\n"
        "        x: chartAreaItem.x + root.viewportOffsetRatio * chartAreaItem.width"
    ) in xy_chart_core_source

    for token in (
        "zoom_in_factor",
        "zoom_out_factor",
        "minimum_viewport_span",
        "default_anchor_ratio",
        "viewport_slider_steps",
        "lttb_threshold",
        "viewport_epsilon",
    ):
        assert f" {token}:" in chart_enum_source
        assert f"Enums.chart.{token}" in zoom_consumers

    assert "duration: 120" not in chart_view_source
    assert "interval: 50" not in chart_view_source
    assert "interval: Enums.duration.slow" in data_zoom_source
