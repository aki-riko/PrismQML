# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design window shell and status area skin tests."""

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


def _assert_shell(window, content, background):
    assert window.property("contentCornerRadius") == 8
    assert _rgb(window.property("contentBgColor")) == content
    assert _rgb(window.property("windowColor")) == background


def _assert_status_bar(item, background, divider, text):
    assert _rgb(item.property("_statusBarBackground")) == background
    assert _rgb(item.property("_statusBarDividerColor")) == divider
    assert _rgb(item.property("_statusBarTextColor")) == text


def _assert_profile_card(item, hover, pressed, title, subtitle):
    assert item.property("_profileRadius") == 6
    assert _rgb(item.property("_profileHoverColor")) == hover
    assert _rgb(item.property("_profilePressedColor")) == pressed
    assert _rgb(item.property("_profileTitleColor")) == title
    assert _rgb(item.property("_profileSubtitleColor")) == subtitle


def test_prism_design_window_shell_status_and_profile_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
NavigationWindowCore {
    visible: false
}
"""))
        window = keep[-1][1]
        _assert_shell(window, (251, 252, 254), (244, 247, 250))

        keep.append(_build(engine, b"""
import PrismQML
StatusBar {
    message: "Ready"
    leftItems: ["Ln 1"]
    rightItems: ["UTF-8"]
}
"""))
        status_bar = keep[-1][1]
        _assert_status_bar(status_bar, (251, 252, 254), (226, 234, 242), (95, 111, 128))

        keep.append(_build(engine, b"""
import PrismQML
NavigationProfileCard {
    title: "Prism"
    subtitle: "Design Skin"
    isCompacted: false
}
"""))
        profile_card = keep[-1][1]
        _assert_profile_card(
            profile_card,
            (238, 245, 255),
            (227, 237, 248),
            (23, 32, 42),
            (95, 111, 128),
        )

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
NavigationWindowCore {
    visible: false
}
"""))
        dark_window = keep[-1][1]
        _assert_shell(dark_window, (23, 28, 34), (17, 20, 24))

        keep.append(_build(engine, b"""
import PrismQML
StatusBar {
    message: "Ready"
    leftItems: ["Ln 1"]
    rightItems: ["UTF-8"]
}
"""))
        dark_status_bar = keep[-1][1]
        _assert_status_bar(dark_status_bar, (23, 28, 34), (42, 51, 61), (166, 177, 191))

        keep.append(_build(engine, b"""
import PrismQML
NavigationProfileCard {
    title: "Prism"
    subtitle: "Design Skin"
    isCompacted: false
}
"""))
        dark_profile_card = keep[-1][1]
        _assert_profile_card(
            dark_profile_card,
            (38, 48, 58),
            (32, 40, 51),
            (238, 243, 248),
            (166, 177, 191),
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
