# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart runtime performance regressions. 图表运行时性能回归。"""

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlEngine, QQmlExpression

# 兼容再导出: 拆分前同目录有 11 个消费者模块从本模块导入共享设施,
# 拆分后它们仍按原路径导入, 名称与 fixture 行为保持不变。
from chart_perf_shared import (
    LOADER_NAMES,
    ROOT,
    SCENE_SOURCE,
    SCENE_URL,
    _animated_canvases,
    _create_chart,
    _dispose_chart,
    _evaluate,
    _loaders,
    _object_tree,
    _pump,
    chart_scene,
    windowed_chart_scene,
)


def test_chart_instantiates_only_the_selected_renderer(chart_scene):
    chart, warnings = chart_scene
    loaders = _loaders(chart)
    cases = (
        ("barType", "barContentLoader"),
        ("lineType", "lineContentLoader"),
        ("scatterType", "scatterContentLoader"),
        ("pieType", "pieAreaLoader"),
        ("radarType", "radarAreaLoader"),
        ("boxplotType", "boxplotAreaLoader"),
    )

    for type_property, expected_loader in cases:
        chart.setProperty("chartType", chart.property(type_property))
        _pump(20)
        active_loaders = [
            name for name, loader in loaders.items() if loader.property("item") is not None
        ]
        assert active_loaders == [expected_loader]

    assert warnings == []


def test_three_point_line_chart_has_bounded_tree_and_no_tick_polling(chart_scene):
    chart, warnings = chart_scene
    line_loader = _loaders(chart)["lineContentLoader"]
    line_content = line_loader.property("item")
    assert line_content is not None

    tree = _object_tree(chart)
    quick_items = [obj for obj in tree if isinstance(obj, QQuickItem)]
    assert len(tree) <= 300
    assert len(quick_items) <= 170

    canvases = _animated_canvases(line_content)
    assert len(canvases) == 1
    assert 0 <= canvases[0].property("animProgress") < 1
    expression = QQmlExpression(
        QQmlEngine.contextForObject(canvases[0]),
        canvases[0],
        "animatedY(100, 300)",
    )
    initial_y = _evaluate(expression)
    assert 100 < initial_y <= 300

    tick_timers = [
        obj
        for obj in tree
        if obj.metaObject().indexOfProperty("interval") >= 0
        and obj.property("interval") == chart.property("tickDuration")
    ]
    assert tick_timers == []

    _pump(chart.property("chartDuration") + 50)
    assert canvases[0].property("animProgress") == pytest.approx(1)
    final_y = _evaluate(expression)
    assert final_y == pytest.approx(100)
    running_infinite_animations = [
        obj
        for obj in _object_tree(chart)
        if obj.metaObject().indexOfProperty("running") >= 0
        and obj.metaObject().indexOfProperty("loops") >= 0
        and obj.property("running")
        and obj.property("loops") == -1
    ]
    assert running_infinite_animations == []
    assert warnings == []


def test_empty_state_animation_runs_only_while_visible(chart_scene):
    chart, warnings = chart_scene
    empty_animation = chart.findChild(QObject, "emptyStateAnimation")
    assert empty_animation is not None
    assert not empty_animation.property("running")

    chart.setProperty("chartData", [])
    _pump(20)

    assert _loaders(chart)["lineContentLoader"].property("item") is None
    assert empty_animation.property("running")
    assert warnings == []


def test_chart_null_and_empty_inputs_stay_finite_and_select_empty_state(chart_scene):
    chart, warnings = chart_scene
    loaders = _loaders(chart)

    chart.setProperty("chartData", None)
    chart.setProperty("series", None)
    chart.setProperty("indicators", None)
    chart.setProperty("boxplotData", None)
    _pump(20)

    assert not chart.property("_hasChartData")
    assert not chart.property("_hasSeriesData")
    assert not chart.property("_hasRadarData")
    assert not chart.property("_hasBoxplotData")
    assert chart.property("maxValue") == 1
    assert loaders["lineContentLoader"].property("item") is None

    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("chartData", [])
    chart.setProperty("series", [{"name": "empty", "values": []}])
    _pump(20)
    assert loaders["lineContentLoader"].property("item") is None

    chart.setProperty("series", [{"name": "nonempty", "values": [1, 2]}])
    _pump(20)
    assert loaders["lineContentLoader"].property("item") is not None
    assert not chart.findChild(QObject, "emptyStateAnimation").property("running")
    line_content = loaders["lineContentLoader"].property("item")
    value_range = line_content.property("valueRange").toVariant()
    assert value_range["min"] != float("inf")
    assert value_range["max"] != float("inf")

    chart.setProperty("series", [None, {"name": "nonempty", "values": [1, 2]}])
    _pump(20)
    assert loaders["lineContentLoader"].property("item") is not None
    assert warnings == []

    chart.setProperty("chartType", chart.property("scatterType"))
    chart.setProperty("series", [{"name": "empty", "data": []}])
    _pump(20)
    assert loaders["scatterContentLoader"].property("item") is None

    chart.setProperty("chartType", chart.property("radarType"))
    chart.setProperty(
        "indicators",
        [None, {"name": "B", "max": 5}, {"name": "C", "max": 5}],
    )
    chart.setProperty("series", [{"name": "radar", "values": [1, 2, 3]}])
    _pump(20)
    assert loaders["radarAreaLoader"].property("item") is not None
    assert warnings == []

    chart.setProperty("series", [])
    _pump(20)
    assert loaders["radarAreaLoader"].property("item") is None

    chart.setProperty("chartType", chart.property("boxplotType"))
    chart.setProperty("boxplotData", [{"label": "bad"}])
    _pump(20)
    assert loaders["boxplotAreaLoader"].property("item") is None
    assert warnings == []
