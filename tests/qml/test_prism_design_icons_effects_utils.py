# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design icons, effects, and utility skin tests."""

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


def _alpha(qcolor):
    return round(qcolor.alphaF(), 2)


def _assert_icons(icon, chevron, check, close, color, accent):
    assert _rgb(icon.property("color")) == color
    assert _rgb(chevron.property("color")) == color
    assert _rgb(close.property("color")) == color
    assert _rgb(check.property("color")) == accent


def _assert_shadowed_rectangle(item, card, shadow_alpha):
    assert item.property("_rectangleRadius") == 8
    assert item.property("_defaultShadowBlur") == 8
    assert item.property("_defaultShadowOffset") == 2
    assert _rgb(item.property("_rectangleColor")) == card
    assert _alpha(item.property("_defaultShadowColor")) == shadow_alpha
    assert _alpha(item.property("shadowColor")) == shadow_alpha


def _assert_popup(item, background, border, shadow_alpha):
    assert item.property("popupRadius") == 10
    assert item.property("_popupBorderWidth") == 1
    assert item.property("_popupShadowBlur") == 16
    assert item.property("_popupShadowOffset") == 4
    assert _rgb(item.property("_popupBackground")) == background
    assert _rgb(item.property("_popupBorderColor")) == border
    assert _alpha(item.property("_popupShadowColor")) == shadow_alpha


def test_prism_design_icons_effects_utils_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
Icon {
    icon: "Settings"
}
"""))
        icon = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
ChevronIcon {}
"""))
        chevron = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CheckIcon {}
"""))
        check = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CloseIcon {}
"""))
        close = keep[-1][1]
        _assert_icons(
            icon,
            chevron,
            check,
            close,
            color=(23, 32, 42),
            accent=(47, 111, 237),
        )

        keep.append(_build(engine, b"""
import PrismQML
ColorOverlay {}
"""))
        overlay = keep[-1][1]
        assert _rgb(overlay.property("color")) == (23, 32, 42)

        keep.append(_build(engine, b"""
import PrismQML
ShadowedRectangle {
    width: 120
    height: 64
}
"""))
        _assert_shadowed_rectangle(keep[-1][1], card=(255, 255, 255), shadow_alpha=0.12)

        keep.append(_build(engine, b"""
import PrismQML
PopupWindowCore {
    popupWidth: 180
    popupHeight: 120
}
"""))
        _assert_popup(
            keep[-1][1],
            background=(248, 251, 255),
            border=(217, 227, 236),
            shadow_alpha=0.14,
        )

        setTheme(Theme.DARK)

        keep.append(_build(engine, b"""
import PrismQML
Icon {
    icon: "Settings"
}
"""))
        dark_icon = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
ChevronIcon {}
"""))
        dark_chevron = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CheckIcon {}
"""))
        dark_check = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CloseIcon {}
"""))
        dark_close = keep[-1][1]
        _assert_icons(
            dark_icon,
            dark_chevron,
            dark_check,
            dark_close,
            color=(238, 243, 248),
            accent=(122, 167, 255),
        )

        keep.append(_build(engine, b"""
import PrismQML
ColorOverlay {}
"""))
        dark_overlay = keep[-1][1]
        assert _rgb(dark_overlay.property("color")) == (238, 243, 248)

        keep.append(_build(engine, b"""
import PrismQML
ShadowedRectangle {
    width: 120
    height: 64
}
"""))
        _assert_shadowed_rectangle(keep[-1][1], card=(32, 38, 46), shadow_alpha=0.18)

        keep.append(_build(engine, b"""
import PrismQML
PopupWindowCore {
    popupWidth: 180
    popupHeight: 120
}
"""))
        _assert_popup(
            keep[-1][1],
            background=(36, 43, 52),
            border=(48, 58, 70),
            shadow_alpha=0.21,
        )
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
