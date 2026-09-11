# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart runtime performance shared scene and helpers. 图表运行时性能共享场景与工具。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
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


@pytest.fixture
def windowed_chart_scene(qapp):
    scene = _create_chart()
    window = QQuickWindow()
    window.resize(640, 360)
    scene[2].setParentItem(window.contentItem())
    window.show()
    _pump(20)
    try:
        yield scene[2], scene[3]
    finally:
        scene[2].setParentItem(None)
        window.close()
        window.deleteLater()
        _dispose_chart(scene[0], scene[1], scene[2])
