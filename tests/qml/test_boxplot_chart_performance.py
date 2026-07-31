# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Boxplot chart paint performance regressions. 箱线图绘制性能回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from test_chart_runtime_performance import (
    _animated_canvases,
    _evaluate,
    _loaders,
    _object_tree,
    _pump,
    windowed_chart_scene,
)


def test_boxplot_hover_repaints_only_dirty_strips(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    box_count = 1_000
    chart.setProperty("animated", False)
    chart.setProperty("showValues", False)
    chart.setProperty("chartType", chart.property("boxplotType"))
    chart.setProperty(
        "boxplotData",
        [
            {
                "label": f"B{index}",
                "min": index,
                "q1": index + 10,
                "median": index + 20,
                "q3": index + 30,
                "max": index + 40,
                "outliers": [index - 5, index + 45],
            }
            for index in range(box_count)
        ],
    )
    _pump(50)

    boxplot_area = _loaders(chart)["boxplotAreaLoader"].property("item")
    assert boxplot_area is not None
    content = next(
        obj
        for obj in _object_tree(boxplot_area)
        if obj.metaObject().indexOfProperty("_lastFrameBoxDrawCount") >= 0
    )
    canvas = _animated_canvases(content)[0]
    painted = QSignalSpy(canvas.painted)
    full_paint = QQmlExpression(
        QQmlEngine.contextForObject(canvas), canvas, "(requestPaint(), true)"
    )

    def request_full_paint() -> None:
        assert _evaluate(full_paint)
        assert painted.wait(1_000)

    def assert_partial_matches_full(*, expect_local: bool) -> None:
        assert painted.wait(1_000)
        draw_count = content.property("_lastFrameBoxDrawCount")
        assert 0 < draw_count <= box_count
        if expect_local:
            assert draw_count < box_count // 4
        partial_image = chart.window().grabWindow()
        request_full_paint()
        assert partial_image == chart.window().grabWindow()

    for horizontal, first_index, second_index in (
        (False, box_count // 3, box_count * 2 // 3),
        (True, box_count * 2 // 3, box_count // 3),
    ):
        content.setProperty("isHorizontal", horizontal)
        content.setProperty("hoveredIndex", -1)
        request_full_paint()
        assert content.property("_lastFrameBoxDrawCount") == box_count

        content.setProperty("hoveredIndex", first_index)
        assert_partial_matches_full(expect_local=True)
        content.setProperty("hoveredIndex", second_index)
        assert_partial_matches_full(expect_local=False)
        content.setProperty("hoveredIndex", -1)
        assert_partial_matches_full(expect_local=True)

    content.setProperty("isHorizontal", False)
    content.setProperty("showValues", True)
    request_full_paint()
    content.setProperty("hoveredIndex", box_count // 2)
    assert painted.wait(1_000)
    assert content.property("_lastFrameBoxDrawCount") == box_count
    partial_image = chart.window().grabWindow()
    request_full_paint()
    assert partial_image == chart.window().grabWindow()

    content.setProperty("isHorizontal", True)
    request_full_paint()
    content.setProperty("hoveredIndex", box_count // 3)
    assert_partial_matches_full(expect_local=True)
    assert warnings == []
