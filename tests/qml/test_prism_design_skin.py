# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design skin token and component smoke tests."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def test_prism_design_skin_tokens_and_controls(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property string skinValue: Enums.skin
    property bool prismDesign: Enums.isPrismDesign
    property bool neobrutalism: Enums.isNeobrutalism
    property color accent: Enums.accentColor
    property color background: Enums.backgroundColor
    property color surface: Enums.surfaceColor
    property color controlBg: Enums.stateColor.controlBg
    property color segmentedSelected: Enums.stateColor.segmentedSelected
    property color treeItemHover: Enums.stateColor.treeItemHover
    property color chartFirst: Enums.chartColors.palette[0]
    property color chartGrid: Enums.chartColors.gridLine
    property int radiusControl: Enums.prismDesign.radiusControl
    property int radiusCard: Enums.prismDesign.radiusCard
    property int radiusPopup: Enums.prismDesign.radiusPopup
}
"""))
        tokens = keep[-1][1]
        assert tokens.property("skinValue") == "prism_design"
        assert tokens.property("prismDesign") is True
        assert tokens.property("neobrutalism") is False
        assert _rgb(tokens.property("accent")) == (47, 111, 237)
        assert _rgb(tokens.property("background")) == (244, 247, 250)
        assert _rgb(tokens.property("surface")) == (251, 252, 254)
        assert _rgb(tokens.property("controlBg")) == (255, 255, 255)
        assert _rgb(tokens.property("segmentedSelected")) == (219, 234, 255)
        assert _rgb(tokens.property("treeItemHover")) == (238, 245, 255)
        assert _rgb(tokens.property("chartFirst")) == (47, 111, 237)
        assert _rgb(tokens.property("chartGrid")) == (226, 234, 242)
        assert tokens.property("radiusControl") == 6
        assert tokens.property("radiusCard") == 8
        assert tokens.property("radiusPopup") == 10

        keep.append(_build(engine, b"""
import PrismQML
Button {
    text: "OK"
    style: Enums.button.style_primary
    width: 120
    height: 36
}
"""))
        button = keep[-1][1]
        assert button.property("radius") == 6
        assert button.property("_neoPressShift") == 0
        assert _rgb(button.property("color")) == (47, 111, 237)

        keep.append(_build(engine, b"""
import PrismQML
Card {
    width: 200
    height: 120
}
"""))
        card = keep[-1][1]
        assert card.property("borderRadius") == 8
        assert _rgb(card.property("color")) == (255, 255, 255)

        keep.append(_build(engine, b"""
import PrismQML
InputCore {
    width: 200
    height: 32
}
"""))
        input_core = keep[-1][1]
        assert input_core.property("radius") == 6
        assert _rgb(input_core.property("color")) == (255, 255, 255)
        assert _rgb(input_core.property("inputTextColor")) == (23, 32, 42)

        keep.append(_build(engine, b"""
import PrismQML
SegmentedControl {
    items: ["Token", "State", "Surface"]
    currentIndex: 1
}
"""))
        segmented = keep[-1][1]
        assert segmented.property("radius") == 6
        assert _rgb(segmented.property("color")) == (251, 252, 254)

        keep.append(_build(engine, b"""
import PrismQML
InfoBar {
    title: "Info"
    content: "Prism overlay"
    duration: 0
}
"""))
        info_bar = keep[-1][1]
        assert info_bar.property("radius") == 10
        assert _rgb(info_bar.property("borderColor")) == (217, 227, 236)

        page_path = Path(__file__).resolve().parents[2] / "examples" / "pages" / "PrismDesignPage.qml"
        page_component = QQmlComponent(engine, QUrl.fromLocalFile(str(page_path)))
        assert not page_component.isError(), [error.toString() for error in page_component.errors()]
        page = page_component.create(engine.rootContext())
        assert page is not None, [error.toString() for error in page_component.errors()]
        keep.append((page_component, page))

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property string skinValue: Enums.skin
    property bool prismDesign: Enums.isPrismDesign
    property color accent: Enums.accentColor
    property color background: Enums.backgroundColor
    property color surface: Enums.surfaceColor
    property color chartFirst: Enums.chartColors.palette[0]
}
"""))
        dark_tokens = keep[-1][1]
        assert dark_tokens.property("skinValue") == "prism_design"
        assert dark_tokens.property("prismDesign") is True
        assert _rgb(dark_tokens.property("accent")) == (122, 167, 255)
        assert _rgb(dark_tokens.property("background")) == (17, 20, 24)
        assert _rgb(dark_tokens.property("surface")) == (23, 28, 34)
        assert _rgb(dark_tokens.property("chartFirst")) == (122, 167, 255)
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
