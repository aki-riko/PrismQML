# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart animation geometry cache performance. 图表动画几何缓存性能回归。"""

from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from chart_perf_shared import (
    _evaluate,
    _loaders,
    _object_tree,
    _pump,
    chart_scene,
)


def test_radar_animation_reuses_cached_polar_geometry(chart_scene):
    chart, warnings = chart_scene
    indicator_count = 48
    series_count = 24
    indicators = [
        {"name": f"I{index}", "max": 100}
        for index in range(indicator_count)
    ]
    series = [
        {
            "name": f"S{series_index}",
            "values": [
                10 + series_index * 3 + point_index / (indicator_count + 1)
                for point_index in range(indicator_count)
            ],
        }
        for series_index in range(series_count)
    ]
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("radarType"))
    chart.setProperty("indicators", indicators)
    chart.setProperty("series", series)
    _pump(50)

    radar_area = _loaders(chart)["radarAreaLoader"].property("item")
    assert radar_area is not None
    radar_content = next(
        obj
        for obj in _object_tree(radar_area)
        if obj.metaObject().indexOfProperty("pointPositions") >= 0
    )
    context = QQmlEngine.contextForObject(radar_content)
    rebuild_geometry = QQmlExpression(
        context,
        radar_content,
        "(_rebuildPointGeometry(width, height), true)",
    )
    assert _evaluate(rebuild_geometry)
    point_count = indicator_count * series_count
    point_positions_length = QQmlExpression(
        context,
        radar_content,
        "pointPositions.length",
    )
    assert _evaluate(point_positions_length) == point_count
    build_count = radar_content.property("_pointGeometryBuildCount")
    assert build_count >= 1
    position_changes = QSignalSpy(radar_content.pointPositionsChanged)

    update_points = QQmlExpression(
        context,
        radar_content,
        "(_updateAnimatedPoints(0.5), true)",
    )
    assert _evaluate(update_points)
    assert radar_content.property("_lastFramePointUpdateCount") == point_count
    assert radar_content.property("_pointGeometryBuildCount") == build_count
    assert position_changes.count() == 1

    assert _evaluate(update_points)
    assert radar_content.property("_lastFramePointUpdateCount") == 0
    assert radar_content.property("_pointGeometryBuildCount") == build_count
    assert position_changes.count() == 1

    update_points.setExpression("(_updateAnimatedPoints(0.75), true)")
    assert _evaluate(update_points)
    assert radar_content.property("_lastFramePointUpdateCount") == point_count
    assert radar_content.property("_pointGeometryBuildCount") == build_count
    assert position_changes.count() == 2

    assert _evaluate(rebuild_geometry)
    assert _evaluate(update_points)
    assert radar_content.property("_lastFramePointUpdateCount") == point_count
    assert radar_content.property("_pointGeometryBuildCount") == build_count + 1

    target_index = point_count // 2 + indicator_count // 2
    nearest_point = QQmlExpression(
        context,
        radar_content,
        "_nearestPointIndex("
        f"pointPositions[{target_index}].x, pointPositions[{target_index}].y)",
    )
    assert _evaluate(nearest_point) == target_index
    radar_content.setProperty("hoveredPointIndex", target_index % indicator_count)
    _pump(20)
    assert radar_content.property("_pointGeometryBuildCount") == build_count + 1
    assert warnings == []


def test_radar_animation_notifies_position_bindings(chart_scene):
    chart, warnings = chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("radarType"))
    chart.setProperty(
        "indicators",
        [
            {"name": "A", "max": 100},
            {"name": "B", "max": 100},
            {"name": "C", "max": 100},
        ],
    )
    chart.setProperty("series", [{"name": "S", "values": [20, 40, 60]}])
    _pump(20)

    radar_area = _loaders(chart)["radarAreaLoader"].property("item")
    assert radar_area is not None
    radar_content = next(
        obj
        for obj in _object_tree(radar_area)
        if obj.metaObject().indexOfProperty("pointPositions") >= 0
    )
    context = QQmlEngine.contextForObject(radar_content)
    rebuild = QQmlExpression(
        context,
        radar_content,
        "(_rebuildPointGeometry(width, height), true)",
    )
    assert _evaluate(rebuild)
    position_changes = QSignalSpy(radar_content.pointPositionsChanged)
    before_y = _evaluate(QQmlExpression(context, radar_content, "pointPositions[0].y"))

    update = QQmlExpression(
        context,
        radar_content,
        "(_updateAnimatedPoints(0.5), true)",
    )
    assert _evaluate(update)
    after_y = _evaluate(QQmlExpression(context, radar_content, "pointPositions[0].y"))

    assert after_y != before_y
    assert position_changes.count() == 1
    assert warnings == []


def test_boxplot_animation_reuses_cached_value_geometry(chart_scene):
    chart, warnings = chart_scene
    box_count = 1_000
    outliers_per_box = 2
    chart.setProperty("animated", False)
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
    boxplot_content = next(
        obj
        for obj in _object_tree(boxplot_area)
        if obj.metaObject().indexOfProperty("_boxGeometryBuildCount") >= 0
    )
    context = QQmlEngine.contextForObject(boxplot_content)
    rebuild_geometry = QQmlExpression(
        context,
        boxplot_content,
        "(_rebuildBoxGeometry(width, height), true)",
    )
    assert _evaluate(rebuild_geometry)
    geometry_length = QQmlExpression(
        context,
        boxplot_content,
        "_boxGeometry.length",
    )
    assert _evaluate(geometry_length) == box_count
    build_count = boxplot_content.property("_boxGeometryBuildCount")
    assert build_count >= 1

    update_geometry = QQmlExpression(
        context,
        boxplot_content,
        "(_updateAnimatedGeometry(0.5), true)",
    )
    assert _evaluate(update_geometry)
    assert boxplot_content.property("_lastFramePointUpdateCount") == (
        box_count * (5 + outliers_per_box)
    )
    assert boxplot_content.property("_boxGeometryBuildCount") == build_count
    vertical_position = QQmlExpression(
        context,
        boxplot_content,
        "Math.abs(_boxGeometry[0].minPosition - "
        "(_boxGeometry[0].minFinal * 0.5 + height * 0.5)) < 0.000001",
    )
    assert _evaluate(vertical_position)

    boxplot_content.setProperty("isHorizontal", True)
    assert _evaluate(rebuild_geometry)
    horizontal_build_count = boxplot_content.property("_boxGeometryBuildCount")
    assert _evaluate(update_geometry)
    horizontal_position = QQmlExpression(
        context,
        boxplot_content,
        "Math.abs(_boxGeometry[0].minPosition - "
        "_boxGeometry[0].minFinal * 0.5) < 0.000001",
    )
    assert _evaluate(horizontal_position)
    assert boxplot_content.property("_boxGeometryBuildCount") == (
        horizontal_build_count
    )
    assert _evaluate(update_geometry)
    assert boxplot_content.property("_lastFramePointUpdateCount") == 0
    boxplot_content.setProperty("hoveredIndex", box_count // 2)
    _pump(20)
    assert boxplot_content.property("_boxGeometryBuildCount") == (
        horizontal_build_count
    )
    assert warnings == []
