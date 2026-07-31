# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart runtime performance regressions. 图表运行时性能回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "chart-runtime-performance.qml")
)
LOADER_NAMES = (
    "barContentLoader",
    "lineContentLoader",
    "scatterContentLoader",
    "pieAreaLoader",
    "radarAreaLoader",
    "boxplotAreaLoader",
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

ChartView {
    id: chart

    readonly property int barType: Enums.chart.type_bar
    readonly property int lineType: Enums.chart.type_line
    readonly property int scatterType: Enums.chart.type_scatter
    readonly property int pieType: Enums.chart.type_pie
    readonly property int radarType: Enums.chart.type_radar
    readonly property int boxplotType: Enums.chart.type_boxplot
    readonly property int chartDuration: Enums.duration.chart
    readonly property int tickDuration: Enums.duration.tick
    readonly property var samplePoints: [
        { label: "A", value: 1 },
        { label: "B", value: 3 },
        { label: "C", value: 2 }
    ]
    readonly property var sampleSeries: [{
        name: "Series",
        values: [1, 3, 2],
        data: [[1, 1], [2, 3], [3, 2]]
    }]

    width: 640
    height: 360
    deferAnimation: true
    animated: true
    showLegend: false
    chartType: Enums.chart.type_line
    chartData: samplePoints
    series: chartType === Enums.chart.type_scatter || chartType === Enums.chart.type_radar
            ? sampleSeries : []
    indicators: [
        { name: "A", max: 5 },
        { name: "B", max: 5 },
        { name: "C", max: 5 }
    ]
    boxplotData: [{
        label: "A",
        min: 1,
        q1: 2,
        median: 3,
        q3: 4,
        max: 5,
        outliers: []
    }]
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(expression: QQmlExpression):
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return result


def _object_tree(root: QObject) -> list[QObject]:
    return [root, *root.findChildren(QObject)]


def _loaders(chart: QObject) -> dict[str, QObject]:
    loaders = {name: chart.findChild(QObject, name) for name in LOADER_NAMES}
    assert all(loaders.values())
    return loaders


def _animated_canvases(root: QObject) -> list[QObject]:
    return [
        obj
        for obj in _object_tree(root)
        if obj.metaObject().indexOfProperty("animProgress") >= 0
    ]


def _create_chart():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    chart = component.create(engine.rootContext())
    assert chart is not None, [error.toString() for error in component.errors()]
    _pump(10)
    return engine, component, chart, warnings


def _dispose_chart(engine, component, chart) -> None:
    chart.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def chart_scene(qapp):
    scene = _create_chart()
    try:
        yield scene[2], scene[3]
    finally:
        _dispose_chart(scene[0], scene[1], scene[2])


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


def test_scatter_hover_search_uses_cached_local_geometry(chart_scene):
    chart, warnings = chart_scene
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

    target_index = point_count // 2
    expression = QQmlExpression(
        QQmlEngine.contextForObject(scatter_content),
        scatter_content,
        "_nearestPointIndex("
        f"pointPositions[{target_index}].x, pointPositions[{target_index}].y)",
    )
    assert _evaluate(expression) == target_index
    assert scatter_content.property("_lastHoverCandidateCount") < point_count // 4

    scatter_content.setProperty("hoveredPointIndex", target_index)
    _pump(20)
    assert scatter_content.property("_pointGeometryBuildCount") == build_count
    assert warnings == []


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

    update_points = QQmlExpression(
        context,
        radar_content,
        "(_updateAnimatedPoints(0.5), true)",
    )
    assert _evaluate(update_points)
    assert radar_content.property("_lastFramePointUpdateCount") == point_count
    assert radar_content.property("_pointGeometryBuildCount") == build_count

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
    assert radar_content.property("_pointGeometryBuildCount") == build_count
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
