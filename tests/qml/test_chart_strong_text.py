# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chart strong-text fixed-white regressions. 图表强文字固定白色回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
CONSTANTS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Constants.qml"
CHART_INTERNAL = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Chart" / "_internal"
)
STRONG_TEXT_SOURCES = {
    CHART_INTERNAL / "BarChartContent.qml": 2,
    CHART_INTERNAL / "LineChartMarkers.qml": 2,
    CHART_INTERNAL / "ChartTooltip.qml": 1,
}
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "chart-strong-text.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/data/Chart/_internal"

Item {
    id: root

    readonly property color defaultWhite: defaultRectangle.color
    readonly property color chartStrongText: Enums.chartColors.strongText
    readonly property color textPrimary: Enums.textColor.primary

    width: 1000
    height: 300

    Rectangle {
        id: defaultRectangle
        visible: false
    }

    BarChartContent {
        objectName: "barContent"
        width: 300
        height: 200
        chartData: []
        maxValue: 500
        animated: false
        showValues: false
        getColor: function(index) { return Enums.accentColor }
        series: [{ name: "bar-series", values: [113, 421] }]
        showMinMax: true
    }

    LineChartMarkers {
        objectName: "lineMarkers"
        x: 320
        width: 300
        height: 200
        series: [{ name: "line-series", values: [509, 907] }]
        seriesPointPositions: [[{ x: 50, y: 120 }, { x: 220, y: 40 }]]
        showMinMax: true
        showAverage: false
        chartWidth: width
    }

    ChartTooltip {
        objectName: "chartTooltip"
        x: 640
        label: "tooltip-label"
        value: "tooltip-strong-value"
        isValueString: true
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(10)
    return engine, component, root


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _find_text(root: QQuickItem, text: str) -> QQuickItem:
    matches = [
        item
        for item in _walk_visual_tree(root)
        if item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == text
    ]
    assert len(matches) == 1, (
        text,
        [item.metaObject().className() for item in matches],
    )
    return matches[0]


def _assert_color(actual: QColor, expected: QColor) -> None:
    actual_channels = (actual.redF(), actual.greenF(), actual.blueF(), actual.alphaF())
    expected_channels = (
        expected.redF(),
        expected.greenF(),
        expected.blueF(),
        expected.alphaF(),
    )
    assert actual_channels == pytest.approx(expected_channels, abs=1 / 65535)


def _strong_text_items(root: QQuickItem) -> tuple[QQuickItem, ...]:
    bar = root.findChild(QQuickItem, "barContent")
    line = root.findChild(QQuickItem, "lineMarkers")
    tooltip = root.findChild(QQuickItem, "chartTooltip")
    assert bar is not None and line is not None and tooltip is not None
    return (
        _find_text(bar, "421"),
        _find_text(bar, "113"),
        _find_text(line, "907"),
        _find_text(line, "509"),
        _find_text(tooltip, "tooltip-strong-value"),
    )


def test_chart_strong_text_remains_fixed_white(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, root = _create_scene()
    try:
        expected = root.property("defaultWhite")
        _assert_color(expected, QColor("white"))
        _assert_color(root.property("chartStrongText"), expected)
        items = _strong_text_items(root)
        for theme, skin in (
            (Theme.LIGHT, Skin.FLUENT),
            (Theme.DARK, Skin.FLUENT),
            (Theme.DARK, Skin.NEOBRUTALISM),
        ):
            setTheme(theme)
            setSkin(skin)
            _pump(5)
            for item in items:
                _assert_color(item.property("color"), expected)
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_chart_sources_use_strong_text_token():
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")
    strong_text_source = constants_source.split(
        "readonly property color strongText:", 1
    )[1].split("readonly property var _fluentPalette:", 1)[0]
    assert "themeColors.accentForeground" in strong_text_source

    for source_path, expected_count in STRONG_TEXT_SOURCES.items():
        source = source_path.read_text(encoding="utf-8")
        assert source.count("color: Enums.chartColors.strongText") == expected_count
        assert 'color: "white"' not in source
