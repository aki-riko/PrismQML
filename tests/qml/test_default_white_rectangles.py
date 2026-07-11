# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Runtime regressions for rectangles that rely on Qt's default white color."""

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
CAROUSEL_CONTENT = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Carousel"
    / "_internal"
    / "CarouselContent.qml"
)
BEFORE_AFTER_SLIDER = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Slider"
    / "BeforeAfterSlider.qml"
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "default-white.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/data/Carousel/_internal"
import "../../prismqml/PrismQML/controls/inputs/Slider"

Item {
    width: 640
    height: 240

    Rectangle {
        id: defaultRectangle
        visible: false
    }

    CarouselContent {
        id: carouselContent
        objectName: "carouselContent"
        width: 300
        height: 200
        model: []
        effect: Enums.carousel.effect_slide
        orientation: Qt.Horizontal
        currentIndex: 0
        borderRadius: Enums.radius.xlarge
    }

    BeforeAfterSlider {
        id: beforeAfterSlider
        objectName: "beforeAfterSlider"
        x: 320
        width: 300
        height: 200
        position: 0.5
    }

    readonly property color defaultRectangleColor: defaultRectangle.color
    readonly property bool carouselLayerEnabled: carouselContent.layer.enabled
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


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _find_rectangle(root: QQuickItem, width: float, height: float) -> QQuickItem:
    matches = [
        item
        for item in _walk_visual_tree(root)
        if item.metaObject().indexOfProperty("radius") >= 0
        and item.width() == pytest.approx(width)
        and item.height() == pytest.approx(height)
    ]
    assert len(matches) == 1, [
        (item.metaObject().className(), item.width(), item.height()) for item in matches
    ]
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


def _create_layer_mask(item: QQuickItem) -> tuple[QQuickItem, QQuickItem]:
    layer_effect = QQmlProperty(item, "layer.effect")
    assert layer_effect.isValid()
    effect_component = layer_effect.read()
    assert isinstance(effect_component, QQmlComponent)
    assert effect_component.status() == QQmlComponent.Status.Ready
    effect = effect_component.create(effect_component.creationContext())
    assert isinstance(effect, QQuickItem), [
        error.toString() for error in effect_component.errors()
    ]
    mask_source = effect.property("maskSource")
    assert isinstance(mask_source, QQuickItem)
    source_item = mask_source.property("sourceItem")
    assert isinstance(source_item, QQuickItem)
    return effect, source_item


def test_target_rectangles_match_qt_default_white(qapp):
    """Mask, divider, and handle must remain byte-equivalent to default white."""
    engine, component, root = _create_scene()
    effect = None
    try:
        expected = root.property("defaultRectangleColor")
        _assert_color(expected, QColor("white"))

        carousel = root.findChild(QQuickItem, "carouselContent")
        before_after = root.findChild(QQuickItem, "beforeAfterSlider")
        assert carousel is not None and before_after is not None

        assert root.property("carouselLayerEnabled") is True
        assert carousel.property("borderRadius") == 16

        effect, carousel_mask = _create_layer_mask(carousel)
        _assert_color(carousel_mask.property("color"), expected)
        assert carousel_mask.width() == 300
        assert carousel_mask.height() == 200
        assert carousel_mask.property("radius") == 16

        divider = _find_rectangle(before_after, width=2, height=200)
        handle = _find_rectangle(before_after, width=20, height=20)
        _assert_color(divider.property("color"), expected)
        _assert_color(handle.property("color"), expected)
        assert divider.x() == 149
        assert handle.x() == 140
        assert handle.y() == 90
    finally:
        if effect is not None and shiboken6.isValid(effect):
            effect.deleteLater()
        root.deleteLater()
        engine.deleteLater()
        del component
        _pump()


def test_target_sources_rely_on_qt_default_white():
    """Target rectangles must not reintroduce explicit color assignments."""
    carousel_source = CAROUSEL_CONTENT.read_text(encoding="utf-8")
    before_after_source = BEFORE_AFTER_SLIDER.read_text(encoding="utf-8")

    assert "sourceItem: Rectangle {" in carousel_source
    assert "id: dividerLine" in before_after_source
    assert "id: handle" in before_after_source

    carousel_mask_props = carousel_source.split("sourceItem: Rectangle {", 1)[1].split(
        "}", 1
    )[0]
    divider_props = before_after_source.split("id: dividerLine", 1)[1].split(
        "// Line shadow", 1
    )[0]
    handle_props = before_after_source.split("id: handle", 1)[1].split(
        "// Handle shadow", 1
    )[0]
    assert "color:" not in carousel_mask_props
    assert "color:" not in divider_props
    assert "color:" not in handle_props
