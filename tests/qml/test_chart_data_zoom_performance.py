# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart data zoom thumbnail performance regressions. 图表缩略视窗性能回归。"""

from pathlib import Path

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from test_chart_runtime_performance import (
    _evaluate,
    _object_tree,
    _pump,
    windowed_chart_scene,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Chart"
    / "ChartDataZoom.qml"
)


def _request_full_paint(canvas, painted) -> None:
    expression = QQmlExpression(
        QQmlEngine.contextForObject(canvas), canvas, "(requestPaint(), true)"
    )
    assert _evaluate(expression)
    assert painted.wait(1_000)


def test_data_zoom_repaints_reuse_cached_value_range(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    value_count = 100_000
    values = [((index * 37) % 10_000) / 10 for index in range(value_count)]
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("dataZoomEnabled", True)
    chart.setProperty("series", [{"name": "dense", "values": values}])
    _pump(50)

    data_zoom = next(
        obj
        for obj in _object_tree(chart)
        if obj.metaObject().indexOfProperty("_suppressSliderUpdate") >= 0
    )
    canvas = next(
        obj
        for obj in _object_tree(data_zoom)
        if obj.metaObject().indexOfProperty("_drawValues") >= 0
    )
    assert canvas.metaObject().indexOfProperty("_drawFrameBuildCount") >= 0
    context = QQmlEngine.contextForObject(canvas)
    assert _evaluate(QQmlExpression(context, canvas, "_drawValues.length")) == value_count
    assert _evaluate(QQmlExpression(context, canvas, "_drawMinimum")) == 0
    assert _evaluate(QQmlExpression(context, canvas, "_drawMaximum")) == 999.9

    painted = QSignalSpy(canvas.painted)
    _request_full_paint(canvas, painted)
    build_count = canvas.property("_drawFrameBuildCount")
    assert build_count >= 1
    for _ in range(3):
        _request_full_paint(canvas, painted)
        assert canvas.property("_drawFrameBuildCount") == build_count

    chart.setWidth(600)
    assert painted.wait(1_000)
    assert canvas.property("_drawFrameBuildCount") == build_count
    assert warnings == []


def test_data_zoom_paint_loop_uses_cached_value_range():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    paint_section = source.split("onPaint: {", 1)[1].split(
        "Component.onCompleted:", 1
    )[0]
    assert "for (var i = 1; i < vals.length; i++)" not in paint_section
    assert "var minV = _drawMinimum" in paint_section
    assert "var maxV = _drawMaximum" in paint_section
