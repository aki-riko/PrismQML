# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Bar chart animation geometry regressions. 柱状图动画几何回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression

from test_chart_runtime_performance import (
    _evaluate,
    _loaders,
    _pump,
    chart_scene,
)


def _expression(content, source: str) -> QQmlExpression:
    return QQmlExpression(QQmlEngine.contextForObject(content), content, source)


def test_multi_bar_animation_reuses_cached_geometry(chart_scene):
    chart, warnings = chart_scene
    series_count = 4
    bar_count = 2_000
    chart.setProperty("animated", False)
    chart.setProperty("lttbThreshold", bar_count + 1)
    chart.setProperty("chartType", chart.property("barType"))
    chart.setProperty(
        "series",
        [
            {
                "name": f"S{series_index}",
                "values": [
                    ((index * 37 + series_index * 11) % 1_000) - 500
                    for index in range(bar_count)
                ],
            }
            for series_index in range(series_count)
        ],
    )
    _pump(50)

    content = _loaders(chart)["barContentLoader"].property("item")
    assert content is not None
    assert content.metaObject().indexOfProperty("_barGeometryBuildCount") >= 0
    context = QQmlEngine.contextForObject(content)
    rebuild = QQmlExpression(
        context,
        content,
        "(_rebuildBarGeometry(width, height), true)",
    )
    assert _evaluate(rebuild)
    assert _evaluate(
        _expression(
            content,
            "barPositions.length === 4 && barPositions[3].length === 2000",
        )
    )
    build_count = content.property("_barGeometryBuildCount")
    assert build_count >= 1

    update = QQmlExpression(
        context,
        content,
        "(_updateAnimatedBarGeometry(0.5), true)",
    )
    assert _evaluate(update)
    assert content.property("_lastFrameBarUpdateCount") == (
        series_count * bar_count
    )
    assert content.property("_barGeometryBuildCount") == build_count
    original_geometry = _expression(
        content,
        "(function() {"
        " var seriesCount = series.length;"
        " var groupWidth = width / dataLength;"
        " var barWidth = groupWidth * 0.7 / seriesCount;"
        " var barSpacing = barWidth * 0.1;"
        " var value = series[2].values[1234];"
        " var barHeight = getBarRatio(value) * height * 0.5;"
        " var expectedX = 1234 * groupWidth +"
        "     (groupWidth - barWidth * seriesCount -"
        "      barSpacing * (seriesCount - 1)) / 2 +"
        "     2 * (barWidth + barSpacing) + barWidth / 2;"
        " var baseline = valueToY(0);"
        " var expectedTop = value >= 0 ? baseline - barHeight : baseline;"
        " var bar = barPositions[2][1234];"
        " return Math.abs(bar.x - expectedX) < 0.000001 &&"
        "        Math.abs(bar.barTop - expectedTop) < 0.000001 &&"
        "        Math.abs(bar.barBottom - (expectedTop + barHeight))"
        "            < 0.000001 &&"
        "        Math.abs(bar.y - (value >= 0 ? expectedTop"
        "                                  : expectedTop + barHeight))"
        "            < 0.000001;"
        "})()",
    )
    assert _evaluate(original_geometry)
    negative_and_average_geometry = _expression(
        content,
        "(function() {"
        " var value = series[2].values[0];"
        " var barHeight = getBarRatio(value) * height * 0.5;"
        " var baseline = valueToY(0);"
        " var bar = barPositions[2][0];"
        " var averageY = valueToY(calculateAverage(series[2].values));"
        " return value < 0 &&"
        "        Math.abs(bar.barTop - baseline) < 0.000001 &&"
        "        Math.abs(bar.barBottom - (baseline + barHeight))"
        "            < 0.000001 &&"
        "        Math.abs(bar.y - bar.barBottom) < 0.000001 &&"
        "        Math.abs(_barGeometry.averageYs[2] - averageY) < 0.000001;"
        "})()",
    )
    assert _evaluate(negative_and_average_geometry)

    assert _evaluate(update)
    assert content.property("_lastFrameBarUpdateCount") == 0
    content.setProperty("hoveredIndex", bar_count // 2)
    _pump(20)
    assert content.property("_barGeometryBuildCount") == build_count
    assert content.property("_lastFrameBarUpdateCount") == 0
    assert warnings == []
