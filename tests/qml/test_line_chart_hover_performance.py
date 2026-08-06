# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Line chart hover paint regressions. 折线图悬浮绘制回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from test_chart_runtime_performance import (
    _animated_canvases,
    _evaluate,
    _loaders,
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


def test_single_line_hover_repaints_only_local_points(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    point_count = 5_000
    chart.setProperty("animated", False)
    chart.setProperty("lttbThreshold", point_count + 1)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("series", [])
    chart.setProperty(
        "chartData",
        [
            {"label": f"P{index}", "value": (index * 37) % 1_000}
            for index in range(point_count)
        ],
    )
    _pump(50)

    content = _loaders(chart)["lineContentLoader"].property("item")
    assert content is not None
    assert content.metaObject().indexOfProperty("_lastFramePointDrawCount") >= 0
    canvas = _animated_canvases(content)[0]
    painted = QSignalSpy(canvas.painted)
    _request_full_paint(canvas, painted)
    _settle_paints(painted)
    assert content.property("_lastFramePointDrawCount") == point_count

    content.setProperty("hoveredIndex", point_count // 2)
    _assert_partial_matches_full(content, canvas, painted, point_count)
    content.setProperty("hoveredIndex", point_count * 3 // 4)
    _assert_partial_matches_full(
        content, canvas, painted, point_count, expect_local=False
    )
    content.setProperty("hoveredIndex", -1)
    _assert_partial_matches_full(content, canvas, painted, point_count)

    for smooth, area, target_index in (
        (True, False, point_count // 3),
        (False, True, point_count * 2 // 3),
        (True, True, point_count // 4),
    ):
        content.setProperty("smoothLine", smooth)
        content.setProperty("isArea", area)
        content.setProperty("hoveredIndex", -1)
        _request_full_paint(canvas, painted)
        _settle_paints(painted)
        content.setProperty("hoveredIndex", target_index)
        _assert_partial_matches_full(content, canvas, painted, point_count)
    assert warnings == []


def test_multi_line_hover_matches_area_and_stacked_frames(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    point_count = 1_000
    series_count = 4
    total_points = point_count * series_count
    chart.setProperty("animated", False)
    chart.setProperty("lttbThreshold", point_count + 1)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty(
        "series",
        [
            {
                "name": f"S{series_index}",
                "values": [
                    ((index * (series_index + 3) * 17) % 900) + series_index * 20
                    for index in range(point_count)
                ],
            }
            for series_index in range(series_count)
        ],
    )
    _pump(50)

    content = _loaders(chart)["lineContentLoader"].property("item")
    assert content is not None
    canvas = _animated_canvases(content)[0]
    painted = QSignalSpy(canvas.painted)

    for smooth, area_gradient, stacked, target_index in (
        (False, False, False, point_count // 4),
        (True, False, False, point_count // 3),
        (False, True, False, point_count // 2),
        (False, False, True, point_count * 2 // 3),
        (True, False, True, point_count * 3 // 4),
    ):
        content.setProperty("smoothLine", smooth)
        content.setProperty("showAreaGradient", area_gradient)
        content.setProperty("stacked", stacked)
        chart.setProperty("_hoveredLineSeriesIndex", 1)
        chart.setProperty("_hoveredPointIndex", -1)
        _request_full_paint(canvas, painted)
        _settle_paints(painted)
        assert content.property("_lastFramePointDrawCount") == total_points
        assert content.property("hoveredSeriesIndex") == 1
        assert content.property("_paintedHoverSeriesIndex") == 1
        assert content.property("_lineGeometryDirty") is False
        chart.setProperty("_hoveredPointIndex", target_index)
        _assert_partial_matches_full(content, canvas, painted, total_points)

    chart.setProperty("_hoveredLineSeriesIndex", 2)
    chart.setProperty("_hoveredPointIndex", point_count // 5)
    assert painted.wait(1_000)
    assert content.property("_lastFramePointDrawCount") == total_points
    changed_series_image = _grab_item(canvas)
    _request_full_paint(canvas, painted)
    assert changed_series_image == _grab_item(canvas)
    assert warnings == []
