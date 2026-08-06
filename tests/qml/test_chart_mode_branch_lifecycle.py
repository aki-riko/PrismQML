# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart mode branch lifecycle regressions. 图表模式分支生命周期回归。"""

from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types

from test_chart_runtime_performance import (
    ROOT,
    SCENE_SOURCE,
    SCENE_URL,
    _dispose_chart,
    _loaders,
    _object_tree,
    _pump,
)


INITIAL_PIE_SOURCE = SCENE_SOURCE.replace(
    b"chartType: Enums.chart.type_line",
    b"chartType: Enums.chart.type_pie",
)


def _create_initial_pie_chart():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(INITIAL_PIE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    chart = component.create(engine.rootContext())
    assert chart is not None, [error.toString() for error in component.errors()]
    _pump(20)
    return engine, component, chart, warnings


def _rendered_tooltips(chart):
    return [
        obj
        for obj in _object_tree(chart)
        if obj.metaObject().className().startswith(
            ("ChartTooltip", "ChartMultiTooltip")
        )
    ]


def test_first_xy_mode_after_non_xy_start_preserves_renderer_and_tooltip(qapp):
    engine, component, chart, warnings = _create_initial_pie_chart()
    try:
        loaders = _loaders(chart)
        assert loaders["pieAreaLoader"].property("item") is not None
        assert loaders["lineContentLoader"].property("item") is None

        chart.setProperty("chartType", chart.property("lineType"))
        _pump(20)

        line_content = loaders["lineContentLoader"].property("item")
        assert line_content is not None
        assert chart.property("_lineContent") is line_content
        assert loaders["pieAreaLoader"].property("item") is None

        chart.setProperty("_hoveredPointIndex", 1)
        _pump(20)
        tooltips = _rendered_tooltips(chart)
        assert len(tooltips) == 1
        assert tooltips[0].metaObject().className().startswith("ChartTooltip")
        assert tooltips[0].property("visible")

        chart.setProperty("chartType", chart.property("pieType"))
        _pump(20)
        assert loaders["pieAreaLoader"].property("item") is not None
        assert loaders["lineContentLoader"].property("item") is None
        assert not any(
            tooltip.property("visible") for tooltip in _rendered_tooltips(chart)
        )
        assert warnings == []
    finally:
        _dispose_chart(engine, component, chart)
