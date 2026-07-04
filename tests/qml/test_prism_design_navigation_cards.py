# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design navigation and structural container skin tests."""

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


def _assert_nav_item(item, background, border, content):
    assert item.property("_navItemRadius") == 6
    assert item.property("_navItemBorderWidth") == 1
    assert _rgb(item.property("_navItemBackground")) == background
    assert _rgb(item.property("_navItemBorderColor")) == border
    assert _rgb(item.property("_navItemContentColor")) == content


def test_prism_design_navigation_and_cards_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
NavigationBarItem {
    text: "Home"
    icon: "Home"
    selected: true
}
"""))
        nav_bar_item = keep[-1][1]
        _assert_nav_item(nav_bar_item, (219, 234, 255), (170, 184, 199), (47, 111, 237))

        keep.append(_build(engine, b"""
import PrismQML
NavigationViewItem {
    text: "Dashboard"
    icon: "Home"
    selected: true
}
"""))
        nav_view_item = keep[-1][1]
        _assert_nav_item(nav_view_item, (219, 234, 255), (170, 184, 199), (47, 111, 237))

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
SettingsCardCore {
    title: "Appearance"
    content: "Prism Design"
}
"""))
        settings_card = keep[-1][1]
        assert settings_card.property("borderRadius") == 8
        assert _rgb(settings_card.property("color")) == (255, 255, 255)

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
NavigationBarItem {
    text: "Home"
    icon: "Home"
    selected: true
}
"""))
        dark_nav_bar_item = keep[-1][1]
        _assert_nav_item(dark_nav_bar_item, (29, 58, 99), (75, 90, 107), (122, 167, 255))

        keep.append(_build(engine, b"""
import PrismQML
NavigationViewItem {
    text: "Dashboard"
    icon: "Home"
    selected: true
}
"""))
        dark_nav_view_item = keep[-1][1]
        _assert_nav_item(dark_nav_view_item, (29, 58, 99), (75, 90, 107), (122, 167, 255))

        keep.append(_build(engine, b"""
import PrismQML
Card {
    width: 200
    height: 120
}
"""))
        dark_card = keep[-1][1]
        assert dark_card.property("borderRadius") == 8
        assert _rgb(dark_card.property("color")) == (32, 38, 46)

        keep.append(_build(engine, b"""
import PrismQML
SettingsCardCore {
    title: "Appearance"
    content: "Prism Design"
}
"""))
        dark_settings_card = keep[-1][1]
        assert dark_settings_card.property("borderRadius") == 8
        assert _rgb(dark_settings_card.property("color")) == (32, 38, 46)
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
