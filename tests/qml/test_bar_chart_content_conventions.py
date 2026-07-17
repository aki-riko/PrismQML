# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""BarChartContent runtime contracts. 柱状图内容运行时合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Chart"
    / "_internal"
    / "BarChartContent.qml"
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "bar-chart-content-conventions.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/data/Chart/_internal"

Window {
    id: root
    objectName: "window"

    readonly property point multiFirstPoint: {
        if (multiChart.barPositions.length < 1 || multiChart.barPositions[0].length < 1) {
            return Qt.point(-1, -1)
        }
        var bar = multiChart.barPositions[0][0]
        return Qt.point(multiChart.x + bar.x, multiChart.y + (bar.barTop + bar.barBottom) / 2)
    }

    width: 960
    height: 360
    visible: true

    BarChartContent {
        id: verticalChart
        objectName: "verticalChart"
        x: 20
        y: 20
        width: 280
        height: 260
        chartData: [
            { "label": "Loss", "value": -25 },
            { "label": "Gain", "value": 50 },
            { "label": "Peak", "value": 80 }
        ]
        maxValue: 100
        animated: false
        showValues: true
        getColor: function(index) { return Enums.chartColors.extendedPalette[index] }
        valueRange: ({ "min": -25, "max": 80, "hasNegative": true, "hasPositive": true })
        zeroLineRatio: 0.5
        onBarHovered: (index) => hoveredIndex = index
    }

    BarChartContent {
        id: horizontalChart
        objectName: "horizontalChart"
        x: 330
        y: 20
        width: 280
        height: 260
        chartData: [
            { "label": "Left", "value": -40 },
            { "label": "Right", "value": 65 }
        ]
        maxValue: 80
        animated: false
        showValues: true
        isHorizontal: true
        getColor: function(index) { return Enums.chartColors.extendedPalette[index + 2] }
        valueRange: ({ "min": -40, "max": 65, "hasNegative": true, "hasPositive": true })
        onBarHovered: (index) => hoveredIndex = index
    }

    BarChartContent {
        id: multiChart
        objectName: "multiChart"
        x: 640
        y: 20
        width: 280
        height: 260
        chartData: []
        maxValue: 40
        animated: false
        showValues: false
        getColor: function(index) { return Enums.chartColors.extendedPalette[index] }
        series: [
            { "name": "A", "values": [10, 30] },
            { "name": "B", "values": [20, -15] }
        ]
        showAverage: true
        showMinMax: true
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _descendants(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _descendants(child)


def _bar_item(chart: QQuickItem, value: float):
    return next(
        item
        for item in _descendants(chart)
        if item.metaObject().indexOfProperty("barValue") >= 0
        and item.isVisible()
        and item.property("barValue") == pytest.approx(value)
    )


def _click_item(window: QQuickWindow, item: QQuickItem) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    charts = {
        name: window.findChild(QQuickItem, name)
        for name in ("verticalChart", "horizontalChart", "multiChart")
    }
    assert all(charts.values())
    assert _wait_for(lambda: window.property("multiFirstPoint").x() >= 0)
    return engine, component, window, charts, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def bar_chart_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_single_series_vertical_and_horizontal_real_clicks(bar_chart_scene):
    window, charts, warnings, windows_before = bar_chart_scene
    vertical = charts["verticalChart"]
    horizontal = charts["horizontalChart"]
    vertical_hovered = []
    vertical_clicked = []
    horizontal_clicked = []
    vertical.barHovered.connect(vertical_hovered.append)
    vertical.barClicked.connect(lambda index, data: vertical_clicked.append((index, _variant(data))))
    horizontal.barClicked.connect(lambda index, data: horizontal_clicked.append((index, _variant(data))))

    vertical_gain = _bar_item(vertical, 50)
    vertical_point = vertical_gain.mapToScene(QPointF(vertical_gain.width() / 2, vertical_gain.height() / 2)).toPoint()
    QTest.mouseMove(window, vertical_point)
    assert _wait_for(lambda: vertical_hovered[-1:] == [1])
    _click_item(window, vertical_gain)
    assert _wait_for(lambda: len(vertical_clicked) == 1)
    assert vertical_clicked[0][0] == 1
    assert vertical_clicked[0][1]["label"] == "Gain"
    assert vertical_clicked[0][1]["value"] == 50

    horizontal_right = _bar_item(horizontal, 65)
    horizontal_mouse = next(
        item
        for item in horizontal_right.childItems()
        if "MouseArea" in item.metaObject().className()
    )
    assert horizontal_right.isVisible()
    assert horizontal_mouse.isVisible() and horizontal_mouse.isEnabled()
    assert horizontal_mouse.width() == pytest.approx(horizontal_right.width())
    assert horizontal_mouse.height() == pytest.approx(horizontal_right.height())
    horizontal_point = horizontal_mouse.mapToScene(
        QPointF(horizontal_mouse.width() / 2, horizontal_mouse.height() / 2)
    ).toPoint()
    QTest.mouseMove(window, horizontal_point)
    assert _wait_for(lambda: horizontal_mouse.property("containsMouse")), (
        horizontal_point,
        horizontal_right.position(),
        horizontal_mouse.position(),
    )
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=horizontal_point)
    assert _wait_for(lambda: len(horizontal_clicked) == 1)
    assert horizontal_clicked[0][0] == 1
    assert horizontal_clicked[0][1]["label"] == "Right"
    assert horizontal_clicked[0][1]["value"] == 65
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_multi_series_real_hover_click_and_markers(bar_chart_scene):
    window, charts, warnings, windows_before = bar_chart_scene
    multi = charts["multiChart"]
    hovered = []
    clicked = []
    multi.seriesBarHovered.connect(lambda series_index, bar_index: hovered.append((series_index, bar_index)))
    multi.barClicked.connect(lambda index, data: clicked.append((index, _variant(data))))

    point = window.property("multiFirstPoint").toPoint()
    QTest.mouseMove(window, point)
    assert _wait_for(lambda: hovered[-1:] == [(0, 0)])
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)
    assert _wait_for(lambda: len(clicked) == 1)
    assert clicked[0][0] == 0
    assert clicked[0][1] == {"seriesIndex": 0, "barIndex": 0, "value": 10}
    texts = [
        item.property("text")
        for item in _descendants(multi)
        if item.metaObject().indexOfProperty("text") >= 0 and item.isVisible()
    ]
    assert "30" in texts and "10" in texts
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
