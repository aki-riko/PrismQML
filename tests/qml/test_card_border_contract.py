# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared borders on the real CardPage. 真实卡片展示页的统一边框合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, Theme, getSkin, getTheme, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property color borderToken: Enums.stateColor.divider
    readonly property color controlBackground: Enums.stateColor.controlBg
    readonly property real borderWidth: Enums.border.thin

    width: 1200
    height: 900

    Loader {
        anchors.fill: parent
        source: Qt.resolvedUrl("../../examples/pages/CardPage.qml")
    }
}
"""


def _pump(milliseconds=30):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate):
    for _ in range(50):
        if predicate():
            return True
        _pump()
    return predicate()


def _composite(stroke, surface):
    if stroke.alphaF() in (0, 1):
        return stroke
    contribution = surface.alphaF() * (1 - stroke.alphaF())
    alpha = stroke.alphaF() + contribution
    channels = [
        (edge * stroke.alphaF() + fill * contribution) / alpha
        for edge, fill in zip(
            (stroke.redF(), stroke.greenF(), stroke.blueF()),
            (surface.redF(), surface.greenF(), surface.blueF()),
        )
    ]
    return QColor.fromRgbF(*channels, alpha)


def _assert_color(actual, expected):
    assert (
        actual.redF(), actual.greenF(), actual.blueF(), actual.alphaF()
    ) == pytest.approx(
        (expected.redF(), expected.greenF(), expected.blueF(), expected.alphaF()),
        abs=2 / 65535,
    )


def _border_item(items):
    borders = [
        item
        for item in items
        if item.isVisible()
        and item.metaObject().indexOfProperty("border") >= 0
        and item.metaObject().indexOfProperty("shadowLevel") < 0
    ]
    assert len(borders) == 1
    return borders[0]


def _has_ancestor(item, class_prefix):
    ancestor = item.parentItem()
    while ancestor is not None:
        if ancestor.metaObject().className().startswith(class_prefix):
            return True
        ancestor = ancestor.parentItem()
    return False


def _separator_item(root):
    separators = [
        item for item in root.findChildren(QQuickItem)
        if item.metaObject().className().startswith("Separator_QMLTYPE")
        and item.isVisible()
        and item.width() > 200
        and item.height() > 0
        and _has_ancestor(item, "Card_QMLTYPE")
    ]
    assert separators
    return separators[0]


def _gallery_surfaces(root):
    items = root.findChildren(QQuickItem)
    cards = [
        item for item in items
        if item.metaObject().className().startswith(
            ("Card_QMLTYPE", "SettingsCardCore_QMLTYPE")
        )
    ]
    expanders = [
        item for item in items
        if "Expander" in item.metaObject().className()
        and item.metaObject().indexOfProperty("borderColor") >= 0
    ]
    examples = [
        item for item in items
        if item.metaObject().className().startswith("ExampleCard_QMLTYPE")
    ]
    assert len(cards) == 5 and len(expanders) == 1 and len(examples) == 2
    return cards, expanders[0], examples


def _stroke(item):
    return QColor(QQmlProperty(item, "border.color").read())


def _assert_example_border(example, token, width):
    surface = next(
        item for item in example.findChildren(QQuickItem)
        if item.metaObject().className().startswith("ShadowedRectangle_QMLTYPE")
    )
    edge = _border_item(surface.parentItem().childItems())
    _assert_color(_stroke(edge), _composite(token, QColor(surface.property("color"))))
    assert QQmlProperty(edge, "border.width").read() == pytest.approx(width)


def _assert_gallery_borders(root):
    cards, expander, examples = _gallery_surfaces(root)
    assert _wait_for(
        lambda: all(
            QColor(card.property("color")) == root.property("controlBackground")
            for card in cards
        )
    )
    edge = _border_item(expander.childItems())
    separator = _separator_item(root)
    separator_color = QColor(QQmlProperty(separator, "lineColor").read())
    separator_width = QQmlProperty(separator, "lineWidth").read()
    assert separator_width == pytest.approx(root.property("borderWidth"))
    borders = [_stroke(card) for card in cards] + [_stroke(edge)]
    assert all(border == borders[0] for border in borders), [
        border.name(QColor.NameFormat.HexArgb) for border in borders
    ]
    token = separator_color
    assert token == QColor(root.property("borderToken"))
    width = root.property("borderWidth")
    for card in cards:
        _assert_color(_stroke(card), _composite(token, QColor(card.property("color"))))
        assert QQmlProperty(card, "border.width").read() == pytest.approx(width)
    assert QQmlProperty(edge, "border.width").read() == pytest.approx(width)
    _assert_color(
        _stroke(edge), _composite(separator_color, QColor(root.property("controlBackground")))
    )
    for example in examples:
        _assert_example_border(example, token, width)


@pytest.fixture
def card_page(qapp, qml_engine):
    warnings = []
    handler = lambda errors: warnings.extend(error.toString() for error in errors)
    qml_engine.warnings.connect(handler)
    component = QQmlComponent(qml_engine)
    component.setData(
        SCENE_SOURCE, QUrl.fromLocalFile(str(ROOT / "tests/qml/card-border.qml"))
    )
    assert component.status() == QQmlComponent.Status.Ready, component.errors()
    root = component.create(qml_engine.rootContext())
    assert isinstance(root, QQuickItem)
    _pump()
    try:
        yield root, warnings
    finally:
        root.deleteLater()
        component.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        qml_engine.warnings.disconnect(handler)


@pytest.mark.parametrize("skin", list(Skin), ids=lambda skin: skin.value)
@pytest.mark.parametrize("theme", (Theme.LIGHT, Theme.DARK), ids=lambda theme: theme.value)
def test_gallery_card_borders_share_tokens_and_composition(card_page, skin, theme):
    root, warnings = card_page
    previous_skin, previous_theme = getSkin(), getTheme()
    try:
        setSkin(skin)
        setTheme(theme)
        _pump()
        _assert_gallery_borders(root)
        assert warnings == []
    finally:
        setSkin(previous_skin)
        setTheme(previous_theme)


def test_expander_composes_custom_stroke_against_its_background(card_page):
    root, warnings = card_page
    _cards, expander, _examples = _gallery_surfaces(root)
    custom = QColor.fromRgbF(0.2, 0.4, 0.8, 0.4)
    assert expander.setProperty("borderColor", custom)
    edge = _border_item(expander.childItems())
    _assert_color(
        _stroke(edge), _composite(custom, QColor(root.property("controlBackground")))
    )
    assert warnings == []


def _edge_pixel(image, item, ratio, expected):
    position = item.mapToScene(QPointF(item.width() / 2, 0))
    x, y = round(position.x() * ratio), round(position.y() * ratio)
    assert 0 <= x < image.width() and 0 <= y < image.height() - 5
    candidates = [image.pixelColor(x, y + offset) for offset in range(5)]
    return min(
        candidates,
        key=lambda color: sum(
            abs(actual - wanted) for actual, wanted in zip(color.getRgb(), expected)
        ),
    ).getRgb()


def _assert_edge_pixels(image, root, ratio):
    cards, expander, _examples = _gallery_surfaces(root)
    default = root.findChild(QQuickItem, "galleryDefaultCard")
    settings = next(
        card for card in cards
        if "SettingsCardCore" in card.metaObject().className()
    )
    expected = _stroke(default).getRgb()
    edges = [
        _edge_pixel(image, card, ratio, expected)
        for card in (default, settings, expander)
    ]
    assert edges[0] == edges[1] == edges[2], edges
    assert edges[0] == pytest.approx(expected, abs=1)


def _assert_rendered_borders(root):
    window = QQuickWindow()
    window.resize(1200, 1400)
    root.setHeight(window.height())
    root.setParentItem(window.contentItem())
    try:
        window.show()
        _pump(200)
        image = window.grabWindow()
        assert not image.isNull()
        _assert_edge_pixels(image, root, window.devicePixelRatio())
    finally:
        root.setParentItem(None)
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


@pytest.mark.parametrize("theme", (Theme.LIGHT, Theme.DARK), ids=lambda theme: theme.value)
def test_real_gallery_card_edges_render_the_same_color(card_page, theme):
    root, warnings = card_page
    previous_skin, previous_theme = getSkin(), getTheme()
    try:
        setSkin(Skin.FLUENT)
        setTheme(theme)
        _assert_gallery_borders(root)
        _assert_rendered_borders(root)
        assert warnings == []
    finally:
        setSkin(previous_skin)
        setTheme(previous_theme)


def test_card_border_composition_tracks_custom_background(card_page):
    root, warnings = card_page
    previous_skin, previous_theme = getSkin(), getTheme()
    try:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        card = root.findChild(QQuickItem, "galleryDefaultCard")
        token = QColor(root.property("borderToken"))
        for color in (QColor("#80c0e0"), QColor.fromRgbF(0.2, 0.4, 0.6, 0.5)):
            assert card.setProperty("color", color)
            assert _wait_for(lambda: QColor(card.property("color")) == color)
            _assert_color(_stroke(card), _composite(token, color))
        assert warnings == []
    finally:
        setSkin(previous_skin)
        setTheme(previous_theme)
