# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Line chart animation geometry regressions. 折线图动画几何回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from test_chart_runtime_performance import (
    _evaluate,
    _loaders,
    _pump,
    chart_scene,
)


def _line_content(chart):
    content = _loaders(chart)["lineContentLoader"].property("item")
    assert content is not None
    assert content.metaObject().indexOfProperty("_lineGeometryBuildCount") >= 0
    return content


def _expression(content, source: str) -> QQmlExpression:
    return QQmlExpression(QQmlEngine.contextForObject(content), content, source)


def test_single_line_animation_reuses_cached_geometry(chart_scene):
    chart, warnings = chart_scene
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

    content = _line_content(chart)
    rebuild = _expression(
        content,
        "(_rebuildLineGeometry(width, height), true)",
    )
    assert _evaluate(rebuild)
    assert _evaluate(_expression(content, "pointPositions.length")) == point_count
    original_geometry = _expression(
        content,
        "(function() {"
        " var padding = Enums.spacing.m;"
        " var chartHeight = height - padding * 2;"
        " var chartWidth = width - padding * 2;"
        " var stepX = boundaryGap ? chartWidth / chartData.length"
        "                         : chartWidth / (chartData.length - 1);"
        " var expectedX = (boundaryGap ? padding + stepX / 2 : padding)"
        "                 + 1234 * stepX;"
        " var yScale = height > 0 ? chartHeight / height : 0;"
        " var expectedY = padding + valueToY(chartData[1234].value) * yScale;"
        " return Math.abs(pointPositions[1234].x - expectedX) < 0.000001 &&"
        "        Math.abs(pointPositions[1234].finalY - expectedY) < 0.000001;"
        "})()",
    )
    assert _evaluate(original_geometry)
    build_count = content.property("_lineGeometryBuildCount")
    assert build_count >= 1

    update = _expression(
        content,
        "(_updateAnimatedLineGeometry(0.5), true)",
    )
    assert _evaluate(update)
    assert content.property("_lastFramePointUpdateCount") == point_count
    assert content.property("_lineGeometryBuildCount") == build_count
    expected_position = _expression(
        content,
        "Math.abs(pointPositions[1234].y - (_lineGeometryBaseline + "
        "(pointPositions[1234].finalY - _lineGeometryBaseline) * 0.5)) "
        "< 0.000001",
    )
    assert _evaluate(expected_position)

    assert _evaluate(update)
    assert content.property("_lastFramePointUpdateCount") == 0
    content.setProperty("hoveredIndex", point_count // 2)
    _pump(20)
    assert content.property("_lineGeometryBuildCount") == build_count
    assert content.property("_lastFramePointUpdateCount") == 0
    assert warnings == []


def test_stacked_line_animation_reuses_cached_geometry(chart_scene):
    chart, warnings = chart_scene
    series_count = 4
    point_count = 2_500
    chart.setProperty("animated", False)
    chart.setProperty("lttbThreshold", point_count + 1)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty(
        "series",
        [
            {
                "name": f"S{series_index}",
                "values": [series_index + 1] * point_count,
            }
            for series_index in range(series_count)
        ],
    )
    chart.setProperty("stacked", True)
    _pump(50)

    content = _line_content(chart)
    rebuild = _expression(
        content,
        "(_rebuildLineGeometry(width, height), true)",
    )
    assert _evaluate(rebuild)
    assert _evaluate(
        _expression(
            content,
            "seriesPointPositions.length === 4 && "
            "seriesPointPositions[3].length === 2500",
        )
    )
    build_count = content.property("_lineGeometryBuildCount")

    update = _expression(
        content,
        "(_updateAnimatedLineGeometry(0.25), true)",
    )
    assert _evaluate(update)
    assert content.property("_lastFramePointUpdateCount") == (
        series_count * point_count
    )
    assert content.property("_lineGeometryBuildCount") == build_count
    assert _evaluate(
        _expression(
            content,
            "(function() {"
            " var stepX = boundaryGap ? width / 2500 : width / 2499;"
            " var expectedX = (boundaryGap ? stepX / 2 : 0) + 1234 * stepX;"
            " return seriesPointPositions[3][1234].stackedValue === 10 &&"
            "        Math.abs(seriesPointPositions[3][1234].x - expectedX)"
            "            < 0.000001 &&"
            "        Math.abs(seriesPointPositions[3][1234].finalY - valueToY(10))"
            "            < 0.000001;"
            "})()",
        )
    )
    expected_position = _expression(
        content,
        "Math.abs(seriesPointPositions[3][1234].y - "
        "(_lineGeometryBaseline + (seriesPointPositions[3][1234].finalY - "
        "_lineGeometryBaseline) * 0.25)) < 0.000001",
    )
    assert _evaluate(expected_position)

    assert _evaluate(update)
    assert content.property("_lastFramePointUpdateCount") == 0
    content.setProperty("stacked", False)
    assert _evaluate(update)
    assert content.property("_lineGeometryBuildCount") > build_count
    assert _evaluate(
        _expression(
            content,
            "seriesPointPositions[3][1234].stackedValue === 0 && "
            "Math.abs(seriesPointPositions[3][1234].finalY - valueToY(4)) "
            "< 0.000001",
        )
    )
    assert warnings == []


def test_single_line_animation_notifies_position_bindings(chart_scene):
    chart, warnings = chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty(
        "chartData",
        [
            {"label": "A", "value": 10},
            {"label": "B", "value": 30},
            {"label": "C", "value": 20},
        ],
    )
    _pump(20)

    content = _line_content(chart)
    assert _evaluate(_expression(content, "(_rebuildLineGeometry(width, height), true)"))
    position_changes = QSignalSpy(content.pointPositionsChanged)
    before_y = _evaluate(_expression(content, "pointPositions[1].y"))

    assert _evaluate(
        _expression(content, "(_updateAnimatedLineGeometry(0.5), true)")
    )
    after_y = _evaluate(_expression(content, "pointPositions[1].y"))

    assert after_y != before_y
    assert position_changes.count() == 1
    assert warnings == []
