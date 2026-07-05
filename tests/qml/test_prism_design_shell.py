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
    assert window.property("contentCornerRadius") == 4
    assert _rgb(window.property("contentBgColor")) == content
    assert _rgb(window.property("windowColor")) == background


def _assert_status_bar(item, background, divider, text):
    assert _rgb(item.property("_statusBarBackground")) == background
    assert _rgb(item.property("_statusBarDividerColor")) == divider
    assert _rgb(item.property("_statusBarTextColor")) == text


def _assert_profile_card(item, hover, pressed, title, subtitle):
    assert item.property("_profileRadius") == 2
    assert _rgb(item.property("_profileHoverColor")) == hover
    assert _rgb(item.property("_profilePressedColor")) == pressed
    assert _rgb(item.property("_profileTitleColor")) == title
    assert _rgb(item.property("_profileSubtitleColor")) == subtitle


def _assert_windows(item, background):
    assert item.property("windowRadius") == 8
    assert _rgb(item.property("windowColor")) == background


def _assert_compact_windows(item, content, background):
    assert item.property("contentCornerRadius") == 4
    assert _rgb(item.property("contentBgColor")) == content
    assert _rgb(item.property("windowColor")) == background


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
        _assert_shell(window, (248, 250, 249), (238, 243, 242))

        keep.append(_build(engine, b"""
import PrismQML
StatusBar {
    message: "Ready"
    leftItems: ["Ln 1"]
    rightItems: ["UTF-8"]
}
"""))
        status_bar = keep[-1][1]
        _assert_status_bar(status_bar, (248, 250, 249), (213, 223, 221), (86, 106, 109))

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
            (230, 238, 237),
            (220, 231, 229),
            (21, 35, 38),
            (86, 106, 109),
        )

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
NavigationWindowCore {
    visible: false
}
"""))
        dark_window = keep[-1][1]
        _assert_shell(dark_window, (18, 25, 27), (13, 18, 19))

        keep.append(_build(engine, b"""
import PrismQML
StatusBar {
    message: "Ready"
    leftItems: ["Ln 1"]
    rightItems: ["UTF-8"]
}
"""))
        dark_status_bar = keep[-1][1]
        _assert_status_bar(dark_status_bar, (18, 25, 27), (37, 52, 55), (164, 181, 182))

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
            (29, 41, 43),
            (24, 36, 38),
            (238, 245, 243),
            (164, 181, 182),
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


def test_prism_design_windows_public_entries_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
WindowsCore {
    visible: false
}
"""))
        windows_core = keep[-1][1]
        _assert_windows(windows_core, (238, 243, 242))

        keep.append(_build(engine, b"""
import PrismQML
Windows {
    visible: false
}
"""))
        windows = keep[-1][1]
        _assert_compact_windows(windows, (248, 250, 249), (238, 243, 242))

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
WindowsCore {
    visible: false
}
"""))
        dark_windows_core = keep[-1][1]
        _assert_windows(dark_windows_core, (13, 18, 19))

        keep.append(_build(engine, b"""
import PrismQML
Windows {
    visible: false
}
"""))
        dark_windows = keep[-1][1]
        _assert_compact_windows(dark_windows, (18, 25, 27), (13, 18, 19))
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
