# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shadow default metric regressions. 阴影默认度量回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SHADOW_SOURCE = ROOT / "prismqml" / "PrismQML" / "effects" / "Shadow.qml"
SHADOWED_RECTANGLE_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "effects" / "ShadowedRectangle.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "shadow-default-metrics.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property real rectangleOffsetX: rectangle.shadowOffsetX
    readonly property real rectangleOffsetY: rectangle.shadowOffsetY
    readonly property real rectangleSpread: rectangle.shadowSpread
    readonly property real rectangleBlur: rectangle.shadowBlur
    readonly property color rectangleColor: rectangle.shadowColor
    readonly property real actualRectangleOffsetX: rectangle.shadowItem.offset.x
    readonly property real actualRectangleOffsetY: rectangle.shadowItem.offset.y
    readonly property real actualRectangleSpread: rectangle.shadowItem.spread
    readonly property real effectHorizontalOffset: multiEffectShadow.horizontalOffset
    readonly property real effectSpread: multiEffectShadow.spread
    readonly property real actualEffectHorizontalOffset: multiEffectShadow.shadowHorizontalOffset
    readonly property real actualEffectScale: multiEffectShadow.shadowScale
    readonly property real shadowBaseScale: Enums.shadow.baseScale
    readonly property real level4Blur: Enums.shadow.level4.blur
    readonly property real level4Offset: Enums.shadow.level4.offset
    readonly property color level4Color: Enums.shadow.level4.color

    ShadowedRectangle {
        id: rectangle
        objectName: "shadowedRectangle"
        width: 120
        height: 60
    }

    Shadow {
        id: multiEffectShadow
        objectName: "multiEffectShadow"
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
    _pump()
    return engine, component, root


def test_shadow_defaults_and_public_bindings_preserve_runtime_values(qapp):
    engine, component, root = _create_scene()
    try:
        assert root.property("rectangleOffsetX") == pytest.approx(0)
        assert root.property("rectangleOffsetY") == pytest.approx(2)
        assert root.property("rectangleSpread") == pytest.approx(0)
        assert root.property("actualRectangleOffsetX") == pytest.approx(0)
        assert root.property("actualRectangleOffsetY") == pytest.approx(2)
        assert root.property("actualRectangleSpread") == pytest.approx(0)
        assert root.property("effectHorizontalOffset") == pytest.approx(0)
        assert root.property("effectSpread") == pytest.approx(0)
        assert root.property("actualEffectHorizontalOffset") == pytest.approx(0)
        assert root.property("actualEffectScale") == pytest.approx(1)
        assert root.property("shadowBaseScale") == pytest.approx(1)

        rectangle = root.findChild(QQuickItem, "shadowedRectangle")
        effect = root.findChild(QQuickItem, "multiEffectShadow")
        assert rectangle is not None and effect is not None
        assert rectangle.setProperty("shadowLevel", None)
        _pump()
        assert root.property("rectangleBlur") == pytest.approx(
            root.property("level4Blur")
        )
        assert root.property("rectangleOffsetY") == pytest.approx(
            root.property("level4Offset")
        )
        assert root.property("rectangleColor") == root.property("level4Color")

        assert rectangle.setProperty("shadowOffsetX", 3.5)
        assert rectangle.setProperty("shadowSpread", 2.25)
        assert effect.setProperty("horizontalOffset", -4.5)
        assert effect.setProperty("spread", 0.75)
        _pump()

        assert root.property("actualRectangleOffsetX") == pytest.approx(3.5)
        assert root.property("actualRectangleSpread") == pytest.approx(2.25)
        assert root.property("actualEffectHorizontalOffset") == pytest.approx(-4.5)
        assert root.property("actualEffectScale") == pytest.approx(1.75)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_shadow_zero_defaults_rely_on_qml_real_type_defaults():
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")
    shadow_source = SHADOW_SOURCE.read_text(encoding="utf-8")
    rectangle_source = SHADOWED_RECTANGLE_SOURCE.read_text(encoding="utf-8")

    assert "property real horizontalOffset\n" in shadow_source
    assert "property real spread\n" in shadow_source
    assert "property real horizontalOffset: 0" not in shadow_source
    assert "property real spread: 0.0" not in shadow_source
    assert "shadowScale: Enums.shadow.baseScale + root.spread" in shadow_source
    assert "shadowScale: 1.0 + root.spread" not in shadow_source
    assert "readonly property real baseScale: 1.0" in metrics_source

    assert "property real shadowOffsetX\n" in rectangle_source
    assert "property real shadowSpread\n" in rectangle_source
    assert "property real shadowOffsetX: 0" not in rectangle_source
    assert "property real shadowSpread: 0" not in rectangle_source
    assert "Enums.shadow &&" not in rectangle_source
    assert '"#1A000000"' not in rectangle_source
