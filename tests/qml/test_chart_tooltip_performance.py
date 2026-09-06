# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart tooltip lifecycle performance regressions. 图表提示框生命周期性能回归。"""

from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine, QQmlExpression

from test_chart_runtime_performance import (
    _object_tree,
    _pump,
    chart_scene,
    windowed_chart_scene,
)


def _tooltips(chart):
    return [
        obj
        for obj in _object_tree(chart)
        if obj.metaObject().className().startswith(
            ("ChartTooltip", "ChartMultiTooltip")
        )
    ]


def _assert_single_tooltip(chart, expected_type):
    tooltips = _tooltips(chart)
    assert len(tooltips) == 1
    assert tooltips[0].metaObject().className().startswith(expected_type)
    return tooltips[0]


def _repeater_item(repeater, index):
    expression = QQmlExpression(
        QQmlEngine.contextForObject(repeater),
        repeater,
        f"itemAt({index})",
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    assert isinstance(result, QObject)
    return result


def test_xy_chart_instantiates_only_the_active_tooltip(chart_scene):
    chart, warnings = chart_scene
    chart_data = [
        {"label": "Alpha", "value": 10},
        {"label": "Beta", "value": 20},
        {"label": "Gamma", "value": 30},
    ]
    value_series = [
        {"name": "First", "values": [10, 20, 30]},
        {"name": "Second", "values": [30, 20, 10]},
    ]
    scatter_series = [
        {"name": "First", "data": [[0, 10], [1, 20], [2, 30]]},
        {"name": "Second", "data": [[0, 30], [1, 20], [2, 10]]},
    ]
    chart.setProperty("animated", False)
    chart.setProperty("showTooltip", True)
    chart.setProperty("chartData", chart_data)

    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("series", None)
    _pump(20)
    tooltip = _assert_single_tooltip(chart, "ChartTooltip")
    chart.setProperty("_hoveredPointIndex", 1)
    _pump()
    assert tooltip.property("visible")
    assert tooltip.property("label") == "Beta"

    chart.setProperty("series", value_series)
    _pump(20)
    tooltip = _assert_single_tooltip(chart, "ChartMultiTooltip")
    chart.setProperty("_hoveredPointIndex", 1)
    _pump()
    assert tooltip.property("visible")
    assert tooltip.property("xLabel") == "Beta"

    chart.setProperty("showTooltip", False)
    _pump(20)
    assert _tooltips(chart) == []
    chart.setProperty("showTooltip", True)

    chart.setProperty("chartType", chart.property("barType"))
    chart.setProperty("series", None)
    _pump(20)
    tooltip = _assert_single_tooltip(chart, "ChartTooltip")
    chart.setProperty("_hoveredBarIndex", 1)
    _pump()
    assert tooltip.property("visible")
    assert tooltip.property("label") == "Beta"

    chart.setProperty("series", value_series)
    _pump(20)
    tooltip = _assert_single_tooltip(chart, "ChartMultiTooltip")
    chart.setProperty("_hoveredBarIndex", 1)
    _pump()
    assert tooltip.property("visible")
    assert tooltip.property("xLabel") == "Beta"

    chart.setProperty("chartType", chart.property("scatterType"))
    chart.setProperty("series", scatter_series)
    _pump(20)
    tooltip = _assert_single_tooltip(chart, "ChartTooltip")
    chart.setProperty("_hoveredScatterSeriesIndex", 0)
    _pump()
    assert tooltip.property("visible")
    assert tooltip.property("label") == "First"

    chart.setProperty("chartData", None)
    chart.setProperty("series", None)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("series", None)
    _pump(20)
    assert _tooltips(chart) == []
    assert warnings == []


def test_multi_tooltip_expands_long_series_name_without_overlapping_value(
    chart_scene,
):
    chart, warnings = chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("chartData", [{"label": "2026-07-10", "value": 1}])
    chart.setProperty(
        "series",
        [{"name": "单品价格走势", "values": [1], "color": "#008000"}],
    )
    formatter = QQmlExpression(
        QQmlEngine.contextForObject(chart),
        chart,
        "valueFormatter = function(value) { return '30砖 9899金 95银 99文' }",
    )
    formatter.evaluate()
    assert not formatter.hasError(), formatter.error().toString()
    chart.setProperty("_hoveredPointIndex", 0)
    _pump(50)

    tooltip = _assert_single_tooltip(chart, "ChartMultiTooltip")
    repeater = next(
        item
        for item in tooltip.findChildren(QObject)
        if item.metaObject().className() == "QQuickRepeater"
    )
    row = _repeater_item(repeater, 0)
    labels = [
        item
        for item in row.findChildren(QObject)
        if item.metaObject().indexOfProperty("text") >= 0
    ]
    name_label = next(item for item in labels if item.property("text") == "单品价格走势")
    value_label = next(
        item for item in labels if item.property("text") == "30砖 9899金 95银 99文"
    )

    assert name_label.property("width") >= name_label.property("implicitWidth")
    assert value_label.property("x") >= (
        name_label.property("x") + name_label.property("width")
    )
    assert warnings == []


def test_boxplot_tooltip_expands_metric_name_column_without_overlapping_value(
    chart_scene,
):
    chart, warnings = chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("boxplotType"))
    chart.setProperty(
        "boxplotData",
        [{"label": "2026-07-10", "min": 1, "q1": 2, "median": 3, "q3": 4, "max": 5}],
    )
    chart.setProperty("_hoveredBoxplotIndex", 0)
    _pump(50)

    tooltip = chart.findChild(QObject, "boxplotTooltip")
    assert tooltip is not None
    repeater = next(
        item
        for item in tooltip.findChildren(QObject)
        if item.metaObject().className() == "QQuickRepeater"
    )
    row = _repeater_item(repeater, 2)
    labels = [
        item
        for item in row.findChildren(QObject)
        if item.metaObject().indexOfProperty("text") >= 0
    ]
    name_label = next(item for item in labels if item.property("text") == "Median")
    value_label = next(item for item in labels if item.property("text") == "3")

    assert name_label.property("width") >= name_label.property("implicitWidth")
    assert value_label.property("x") >= (
        name_label.property("x") + name_label.property("width")
    )
    assert warnings == []


def test_disabled_tooltip_restores_first_hover_without_visual_drift(
    windowed_chart_scene,
):
    """Disabling must hide tooltips and re-enable the first hover unchanged. 禁用须隐藏提示且恢复首个 hover。"""
    chart, warnings = windowed_chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty(
        "chartData",
        [
            {"label": "Alpha", "value": 10},
            {"label": "Beta", "value": 20},
            {"label": "Gamma", "value": 30},
        ],
    )
    chart.setProperty(
        "series",
        [
            {"name": "First", "values": [10, 20, 30]},
            {"name": "Second", "values": [30, 20, 10]},
        ],
    )
    chart.setProperty("showTooltip", True)
    _pump(20)
    chart.setProperty("_hoveredPointIndex", 1)
    _pump(250)

    tooltip = _assert_single_tooltip(chart, "ChartMultiTooltip")
    assert tooltip.property("visible")
    reference_state = (
        tooltip.property("xLabel"),
        tooltip.x(),
        tooltip.y(),
        tooltip.width(),
        tooltip.height(),
    )
    reference_image = chart.window().grabWindow()
    _pump(50)
    assert chart.window().grabWindow() == reference_image

    chart.setProperty("showTooltip", False)
    _pump(20)
    assert _tooltips(chart) == []

    chart.setProperty("showTooltip", True)
    chart.setProperty("_hoveredPointIndex", -1)
    chart.setProperty("_hoveredPointIndex", 1)
    _pump(250)
    restored = _assert_single_tooltip(chart, "ChartMultiTooltip")
    restored_state = (
        restored.property("xLabel"),
        restored.x(),
        restored.y(),
        restored.width(),
        restored.height(),
    )
    assert restored.property("visible")
    assert restored_state == reference_state
    restored_image = chart.window().grabWindow()
    _pump(50)
    assert chart.window().grabWindow() == restored_image
    assert restored_image == reference_image
    assert warnings == []
