# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart hover search performance. 图表悬停检索性能回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from chart_perf_shared import (
    _animated_canvases,
    _evaluate,
    _loaders,
    _pump,
    chart_scene,
    windowed_chart_scene,
)


def test_line_hover_search_only_checks_the_local_x_range(chart_scene):
    chart, warnings = chart_scene
    line_content = _loaders(chart)["lineContentLoader"].property("item")
    assert line_content is not None
    points = [
        {"x": index, "y": (index * 37) % 200}
        for index in range(1_000)
    ]
    line_content.setProperty("pointPositions", points)

    for pointer_x, pointer_y in ((500, 100), (5, 10), (995, 190), (500, 500)):
        distances = [
            ((pointer_x - point["x"]) ** 2 + (pointer_y - point["y"]) ** 2, index)
            for index, point in enumerate(points)
            if (pointer_x - point["x"]) ** 2
            + (pointer_y - point["y"]) ** 2
            < 30**2
        ]
        expected = min(distances)[1] if distances else -1
        expression = QQmlExpression(
            QQmlEngine.contextForObject(line_content),
            line_content,
            f"_nearestPointIndex({pointer_x}, {pointer_y}, 30)",
        )
        assert _evaluate(expression) == expected
        assert line_content.property("_lastHoverCandidateCount") <= 60
    assert warnings == []


def test_multi_series_line_hover_uses_binary_x_search(chart_scene):
    chart, warnings = chart_scene
    point_count = 5_000
    series_count = 4
    chart.setProperty("lttbThreshold", point_count + 1)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty(
        "series",
        [
            {"name": f"S{series_index}", "values": list(range(point_count))}
            for series_index in range(series_count)
        ],
    )
    _pump(50)

    line_content = _loaders(chart)["lineContentLoader"].property("item")
    assert line_content is not None
    positions = [
        [
            {"x": point_index * 2, "y": 20 + series_index * 30}
            for point_index in range(point_count)
        ]
        for series_index in range(series_count)
    ]
    line_content.setProperty("seriesPointPositions", positions)
    context = QQmlEngine.contextForObject(line_content)
    target_index = 3_456
    nearest_x = QQmlExpression(
        context,
        line_content,
        f"_nearestSeriesPointIndexByX(seriesPointPositions[0][{target_index}].x)",
    )
    assert _evaluate(nearest_x) == target_index
    assert line_content.property("_lastSeriesHoverCandidateCount") <= 2

    midpoint_x = positions[0][target_index]["x"] + 1
    midpoint = QQmlExpression(
        context,
        line_content,
        f"_nearestSeriesPointIndexByX({midpoint_x})",
    )
    assert _evaluate(midpoint) == target_index
    assert line_content.property("_lastSeriesHoverCandidateCount") <= 2
    assert warnings == []


def test_scatter_hover_search_uses_cached_local_geometry(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    point_count = 5_000
    points = [
        [index, (index * 37) % 500]
        for index in range(point_count)
    ]
    chart.setProperty("animated", False)
    chart.setProperty("lttbThreshold", point_count + 1)
    chart.setProperty("chartType", chart.property("scatterType"))
    chart.setProperty("series", [{"name": "dense", "data": points}])
    _pump(50)

    scatter_content = _loaders(chart)["scatterContentLoader"].property("item")
    assert scatter_content is not None
    rebuild_geometry = QQmlExpression(
        QQmlEngine.contextForObject(scatter_content),
        scatter_content,
        "(_rebuildPointGeometry(width, height), true)",
    )
    assert _evaluate(rebuild_geometry)
    point_positions_length = QQmlExpression(
        QQmlEngine.contextForObject(scatter_content),
        scatter_content,
        "pointPositions.length",
    )
    assert _evaluate(point_positions_length) == point_count
    build_count = scatter_content.property("_pointGeometryBuildCount")
    assert build_count >= 1
    assert scatter_content.metaObject().indexOfProperty("_lastFramePointDrawCount") >= 0

    canvas = _animated_canvases(scatter_content)[0]
    painted = QSignalSpy(canvas.painted)
    full_paint = QQmlExpression(
        QQmlEngine.contextForObject(canvas), canvas, "(requestPaint(), true)"
    )
    assert _evaluate(full_paint)
    assert painted.wait(1_000)
    assert scatter_content.property("_lastFramePointDrawCount") == point_count

    target_index = point_count // 2
    expression = QQmlExpression(
        QQmlEngine.contextForObject(scatter_content),
        scatter_content,
        "_nearestPointIndex("
        f"pointPositions[{target_index}].x, pointPositions[{target_index}].y)",
    )
    assert _evaluate(expression) == target_index
    assert scatter_content.property("_lastHoverCandidateCount") < point_count // 4

    scatter_content.setProperty("hoveredSeriesIndex", 0)
    scatter_content.setProperty("hoveredPointIndex", target_index)
    assert painted.wait(1_000)
    assert 0 < scatter_content.property("_lastFramePointDrawCount") < point_count // 4
    partial_image = chart.window().grabWindow()
    assert _evaluate(full_paint)
    assert painted.wait(1_000)
    assert partial_image == chart.window().grabWindow()
    _pump(20)
    assert scatter_content.property("_pointGeometryBuildCount") == build_count
    assert warnings == []


def test_multi_series_bar_hover_searches_only_the_local_x_range(chart_scene):
    chart, warnings = chart_scene
    series_count = 4
    bar_count = 2_000
    chart.setProperty("lttbThreshold", bar_count + 1)
    chart.setProperty("chartType", chart.property("barType"))
    chart.setProperty(
        "series",
        [
            {"name": f"S{series_index}", "values": list(range(bar_count))}
            for series_index in range(series_count)
        ],
    )
    _pump(50)

    bar_content = _loaders(chart)["barContentLoader"].property("item")
    assert bar_content is not None
    positions = [
        [
            {
                "x": bar_index * 5 + series_index * 0.5,
                "barTop": 20 + series_index,
                "barBottom": 300 - series_index,
            }
            for bar_index in range(bar_count)
        ]
        for series_index in range(series_count)
    ]
    bar_content.setProperty("barPositions", positions)

    target_series = 2
    target_index = 1_234
    target_x = positions[target_series][target_index]["x"]
    context = QQmlEngine.contextForObject(bar_content)
    nearest_bar = QQmlExpression(
        context,
        bar_content,
        "(function() {"
        f" var hit = _nearestBarHit({target_x}, 100);"
        " return hit.seriesIndex + ':' + hit.barIndex"
        "})()",
    )
    assert _evaluate(nearest_bar) == f"{target_series}:{target_index}"
    assert bar_content.property("_lastHoverCandidateCount") <= 60

    positions[target_series][target_index]["barTop"] = 150
    bar_content.setProperty("barPositions", positions)
    assert _evaluate(nearest_bar) == f"1:{target_index}"
    assert bar_content.property("_lastHoverCandidateCount") <= 60
    assert warnings == []
