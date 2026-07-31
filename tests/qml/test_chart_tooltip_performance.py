# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart tooltip lifecycle performance regressions. 图表提示框生命周期性能回归。"""

from test_chart_runtime_performance import _object_tree, _pump, chart_scene


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
    tooltip = _assert_single_tooltip(chart, "ChartMultiTooltip")
    assert not tooltip.property("visible")
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
