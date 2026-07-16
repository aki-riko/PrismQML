# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Data component transparent color contracts. 数据组件透明色合同。"""

from pathlib import Path

from PySide6.QtCore import QObject, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = (
    _ROOT / "prismqml/PrismQML/controls/data/Carousel/Carousel.qml",
    _ROOT / "prismqml/PrismQML/controls/data/Chart/_internal/PieChartArea.qml",
    _ROOT / "prismqml/PrismQML/controls/data/Chart/_internal/RadarChartArea.qml",
    _ROOT / "prismqml/PrismQML/controls/data/Label/Label.qml",
)
_PROBE_QML = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/data/Chart/_internal"

Item {
    width: 960
    height: 260

    Carousel {
        objectName: "carousel"
        width: 300
        height: 220
        model: []
        shadowLevel: null
        showIndicator: false
        showNavButtons: false
    }

    PieChartArea {
        objectName: "pieArea"
        x: 320
        width: 300
        height: 220
        chartData: [{ label: "Only", value: 10 }]
        totalValue: 10
        animated: false
        showValues: false
        showLegend: false
        getColor: function() { return Enums.accentColor }
    }

    RadarChartArea {
        objectName: "radarArea"
        x: 640
        width: 300
        height: 220
        indicators: [
            { name: "A", max: 10 },
            { name: "B", max: 10 },
            { name: "C", max: 10 }
        ]
        series: [{ name: "Only", values: [1, 2, 3] }]
        animated: false
        showLabels: false
        showLegend: false
        rings: 3
    }

    Label {
        objectName: "label"
        text: "Transparent sentinel"
    }
}
"""


def _wait_until_ready(component):
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]


def _find_one(root, predicate):
    matches = [item for item in root.findChildren(QObject) if predicate(item)]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _is_transparent(value):
    color = QColor(value)
    return color.isValid() and color.alpha() == 0


def _tooltip(root):
    return _find_one(
        root,
        lambda item: item.metaObject().indexOfProperty("dotColor") >= 0
        and item.metaObject().indexOfProperty("showColorDot") >= 0
        and item.metaObject().indexOfProperty("isValueString") >= 0,
    )


def _assert_carousel(carousel):
    shadow = _find_one(
        carousel,
        lambda item: item.parent() is carousel
        and "RectangularShadow" in item.metaObject().className(),
    )
    assert shadow.property("visible") is False
    assert _is_transparent(shadow.property("color"))


def _assert_label(label):
    assert _is_transparent(label.property("customTextColor"))
    assert label.property("_useCustomColor") is False
    label.setProperty("customTextColor", QColor("red"))
    assert label.property("_useCustomColor") is True
    label.setProperty("customTextColor", QColor("transparent"))
    assert label.property("_useCustomColor") is False


def test_data_components_preserve_transparent_runtime_state(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    url = QUrl.fromLocalFile(str(_ROOT / "tests/qml/data-transparent-probe.qml"))
    component.setData(_PROBE_QML, url)
    _wait_until_ready(component)
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    _assert_carousel(root.findChild(QObject, "carousel"))

    for name in ("pieArea", "radarArea"):
        tooltip = _tooltip(root.findChild(QObject, name))
        assert tooltip.property("visible") is False
        assert _is_transparent(tooltip.property("dotColor"))

    _assert_label(root.findChild(QObject, "label"))

    root.deleteLater()
    engine.deleteLater()
    qapp.processEvents()


def test_data_transparent_sources_are_the_characterized_targets():
    sources = [path.read_text(encoding="utf-8") for path in _SOURCE_PATHS]
    assert "control.shadowLevel.color : Enums.transparent" in sources[0]
    assert "root.getColor(root.hoveredIndex) : Enums.transparent" in sources[1]
    assert "root.getSeriesColor(root.hoveredSeriesIndex) : Enums.transparent" in sources[2]
    assert "customTextColor != Enums.transparent" in sources[3]
