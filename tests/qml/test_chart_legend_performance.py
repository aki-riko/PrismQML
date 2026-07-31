# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart legend lifecycle performance regressions. 图表图例生命周期性能回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from test_chart_runtime_performance import (
    _evaluate,
    _object_tree,
    _pump,
    chart_scene,
)


def _legends(chart):
    return [
        obj
        for obj in _object_tree(chart)
        if obj.metaObject().className().startswith("ChartBottomLegend")
    ]


def _to_variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def test_xy_chart_instantiates_only_the_active_legend(chart_scene):
    chart, warnings = chart_scene
    series_count = 500
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("showLegend", False)
    chart.setProperty(
        "series",
        [
            {"name": f"S{index}", "values": None, "data": None}
            for index in range(series_count)
        ],
    )
    _pump(20)
    assert _legends(chart) == []

    chart.setProperty("showLegend", True)
    _pump(20)
    assert _legends(chart) == []

    for type_property, legend_style, clickable in (
        ("lineType", "line", True),
        ("barType", "bar", True),
        ("scatterType", "dot", False),
    ):
        chart.setProperty("chartType", chart.property(type_property))
        chart.setProperty(
            "series",
            [
                {
                    "name": f"S{index}",
                    "values": [index, index + 1],
                    "data": [[0, index], [1, index + 1]],
                }
                for index in range(3)
            ],
        )
        _pump(20)
        legends = _legends(chart)
        assert len(legends) == 1
        assert legends[0].property("legendStyle") == legend_style
        assert legends[0].property("clickable") is clickable
        chart.setProperty("_hiddenSeriesIndices", [1])
        _pump()
        assert _to_variant(legends[0].property("hiddenIndices")) == (
            [1] if clickable else []
        )
        chart.setProperty("_hiddenSeriesIndices", [])
        click = QQmlExpression(
            QQmlEngine.contextForObject(legends[0]),
            legends[0],
            "(itemClicked(1), true)",
        )
        _evaluate(click)
        assert _to_variant(chart.property("_hiddenSeriesIndices")) == (
            [1] if clickable else []
        )

    chart.setProperty("showLegend", False)
    _pump(20)
    assert _legends(chart) == []
    assert warnings == []


def test_pie_chart_legend_follows_visibility_and_routes_events(chart_scene):
    chart, warnings = chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("showLegend", False)
    chart.setProperty("chartData", None)
    chart.setProperty("chartType", chart.property("pieType"))
    chart.setProperty(
        "chartData",
        [
            {"label": "Alpha", "value": 10},
            {"label": "Beta", "value": 20},
            {"label": "Gamma", "value": 30},
        ],
    )
    _pump(20)
    assert _legends(chart) == []

    chart.setProperty("showLegend", True)
    _pump(20)
    legends = _legends(chart)
    assert len(legends) == 1
    assert legends[0].property("legendStyle") == "dot"
    clicked = QSignalSpy(chart.sliceClicked)
    context = QQmlEngine.contextForObject(legends[0])
    _evaluate(QQmlExpression(context, legends[0], "(itemHovered(1), true)"))
    assert chart.property("_hoveredSliceIndex") == 1
    _evaluate(QQmlExpression(context, legends[0], "(itemClicked(1), true)"))
    assert clicked.count() == 1

    chart.setProperty("showLegend", False)
    _pump(20)
    assert _legends(chart) == []
    assert warnings == []


def test_radar_chart_legend_follows_visibility_and_routes_events(chart_scene):
    chart, warnings = chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("showLegend", False)
    chart.setProperty("indicators", None)
    chart.setProperty("series", None)
    chart.setProperty("chartType", chart.property("radarType"))
    chart.setProperty("series", None)
    chart.setProperty(
        "indicators",
        [
            {"name": "Speed", "max": 100},
            {"name": "Power", "max": 100},
            {"name": "Range", "max": 100},
        ],
    )
    chart.setProperty(
        "series",
        [
            {"name": "Alpha", "values": [10, 20, 30]},
            {"name": "Beta", "values": [30, 20, 10]},
            {"name": "Gamma", "values": [20, 30, 10]},
        ],
    )
    _pump(20)
    assert _legends(chart) == []

    chart.setProperty("showLegend", True)
    _pump(20)
    legends = _legends(chart)
    assert len(legends) == 1
    assert legends[0].property("legendStyle") == "bar"
    chart.setProperty("_hiddenSeriesIndices", [1])
    _pump()
    assert _to_variant(legends[0].property("hiddenIndices")) == [1]
    context = QQmlEngine.contextForObject(legends[0])
    _evaluate(QQmlExpression(context, legends[0], "(itemHovered(2), true)"))
    assert chart.property("_hoveredRadarSeriesIndex") == 2
    assert chart.property("_hoveredRadarPointIndex") == -1
    _evaluate(QQmlExpression(context, legends[0], "(itemClicked(1), true)"))
    assert _to_variant(chart.property("_hiddenSeriesIndices")) == []

    chart.setProperty("showLegend", False)
    _pump(20)
    assert _legends(chart) == []
    assert warnings == []
