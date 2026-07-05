# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design FlipView and Carousel skin tests."""

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


def _assert_pips(item, active, inactive):
    assert item.property("_normalRadius") == 6
    assert item.property("_activeRadius") == 10
    assert item.property("_normalDiameter") == 6
    assert item.property("_activeDiameter") == 20
    assert _rgb(item.property("_pipActiveColor")) == active
    assert _rgb(item.property("_pipHoverColor")) == active
    assert _rgb(item.property("_pipInactiveColor")) == inactive


def test_prism_design_flipview_pips_and_carousel_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
HorizontalPipsPager {
    count: 4
    currentIndex: 1
}
"""))
        _assert_pips(keep[-1][1], active=(11, 127, 137), inactive=(120, 173, 184))

        keep.append(_build(engine, b"""
import PrismQML
VerticalPipsPager {
    count: 4
    currentIndex: 1
}
"""))
        vertical_pips = keep[-1][1]
        assert vertical_pips.property("vertical") is True
        _assert_pips(vertical_pips, active=(11, 127, 137), inactive=(120, 173, 184))

        keep.append(_build(engine, b"""
import PrismQML
Carousel {
    width: 320
    height: 180
    model: [{ "text": "A" }, { "text": "B" }, { "text": "C" }]
    currentIndex: 1
    showNavButtons: true
}
"""))
        carousel = keep[-1][1]
        assert carousel.property("currentIndex") == 1
        assert carousel.property("_modelCount") == 3

        setTheme(Theme.DARK)

        keep.append(_build(engine, b"""
import PrismQML
HorizontalPipsPager {
    count: 4
    currentIndex: 1
}
"""))
        _assert_pips(keep[-1][1], active=(109, 235, 242), inactive=(106, 169, 181))

        keep.append(_build(engine, b"""
import PrismQML
VerticalPipsPager {
    count: 4
    currentIndex: 1
}
"""))
        dark_vertical_pips = keep[-1][1]
        assert dark_vertical_pips.property("vertical") is True
        _assert_pips(dark_vertical_pips, active=(109, 235, 242), inactive=(106, 169, 181))

        keep.append(_build(engine, b"""
import PrismQML
Carousel {
    width: 320
    height: 180
    model: [{ "text": "A" }, { "text": "B" }, { "text": "C" }]
    currentIndex: 1
    showNavButtons: true
}
"""))
        dark_carousel = keep[-1][1]
        assert dark_carousel.property("currentIndex") == 1
        assert dark_carousel.property("_modelCount") == 3
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
