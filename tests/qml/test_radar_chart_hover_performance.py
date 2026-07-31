# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Radar chart hover paint regressions. 雷达图悬浮绘制回归。"""

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


def _pixel_difference(first, second):
    left = first.width()
    top = first.height()
    right = -1
    bottom = -1
    count = 0
    for y in range(first.height()):
        for x in range(first.width()):
            if first.pixel(x, y) == second.pixel(x, y):
                continue
            left = min(left, x)
            top = min(top, y)
            right = max(right, x)
            bottom = max(bottom, y)
            count += 1
    return left, top, right, bottom, count


def _request_full_paint(canvas, painted) -> None:
    expression = QQmlExpression(
        QQmlEngine.contextForObject(canvas), canvas, "(requestPaint(), true)"
    )
    assert _evaluate(expression)
    assert painted.wait(1_000)


def _settle_paints(painted) -> None:
    for _ in range(20):
        if not painted.wait(25):
            return
    raise AssertionError("Canvas paint queue did not settle")


def _grab_item(item):
    result = item.grabToImage()
    ready = QSignalSpy(result.ready)
    if result.image().isNull():
        assert ready.wait(1_000)
    return result.image()


def _assert_partial_matches_full(
    content, canvas, painted, total_points, *, expect_local=True
):
    assert painted.wait(1_000)
    draw_count = content.property("_lastFramePointDrawCount")
    assert 0 < draw_count <= total_points
    if expect_local:
        assert draw_count < total_points // 4
    partial_image = _grab_item(canvas)
    _request_full_paint(canvas, painted)
    full_image = _grab_item(canvas)
    assert partial_image == full_image, _pixel_difference(partial_image, full_image)


def test_radar_hover_repaints_only_local_points(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    indicator_count = 48
    series_count = 24
    point_count = indicator_count * series_count
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("radarType"))
    chart.setProperty(
        "indicators",
        [{"name": f"I{index}", "max": 100} for index in range(indicator_count)],
    )
    chart.setProperty(
        "series",
        [
            {
                "name": f"S{series_index}",
                "values": [
                    10 + ((series_index * 7 + point_index * 3) % 80)
                    for point_index in range(indicator_count)
                ],
            }
            for series_index in range(series_count)
        ],
    )
    _pump(50)

    radar_area = _loaders(chart)["radarAreaLoader"].property("item")
    assert radar_area is not None
    content = next(
        obj
        for obj in _object_tree(radar_area)
        if obj.metaObject().indexOfProperty("pointPositions") >= 0
    )
    assert content.metaObject().indexOfProperty("_lastFramePointDrawCount") >= 0
    canvas = _animated_canvases(content)[0]
    painted = QSignalSpy(canvas.painted)

    for show_labels, rings, target_index in (
        (True, 5, indicator_count // 4),
        (False, 3, indicator_count // 3),
        (True, 8, indicator_count // 2),
    ):
        chart.setProperty("showLabels", show_labels)
        chart.setProperty("rings", rings)
        content.setProperty("hoveredSeriesIndex", 0)
        content.setProperty("hoveredPointIndex", -1)
        _request_full_paint(canvas, painted)
        _settle_paints(painted)
        assert content.property("_lastFramePointDrawCount") == point_count

        content.setProperty("hoveredPointIndex", target_index)
        _assert_partial_matches_full(content, canvas, painted, point_count)
        content.setProperty("hoveredPointIndex", (target_index + 1) % indicator_count)
        _assert_partial_matches_full(content, canvas, painted, point_count)
        content.setProperty(
            "hoveredPointIndex", (target_index + indicator_count // 2) % indicator_count
        )
        _assert_partial_matches_full(
            content, canvas, painted, point_count, expect_local=False
        )
        content.setProperty("hoveredPointIndex", -1)
        _assert_partial_matches_full(content, canvas, painted, point_count)

    content.setProperty("hoveredSeriesIndex", 1)
    content.setProperty("hoveredPointIndex", indicator_count // 5)
    assert painted.wait(1_000)
    assert content.property("_lastFramePointDrawCount") == point_count
    changed_series_image = _grab_item(canvas)
    _request_full_paint(canvas, painted)
    assert changed_series_image == _grab_item(canvas)
    assert warnings == []
