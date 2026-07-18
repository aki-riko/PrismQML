# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart runtime performance regressions. 图表运行时性能回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

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

    tick_timers = [
        obj
        for obj in tree
        if obj.metaObject().indexOfProperty("interval") >= 0
        and obj.property("interval") == chart.property("tickDuration")
    ]
    assert tick_timers == []

    _pump(chart.property("chartDuration") + 50)
    assert canvases[0].property("animProgress") == pytest.approx(1)
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
