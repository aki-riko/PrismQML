# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design container, drawer and layout skin tests."""

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
    return round(qcolor.alphaF() * 255)


def _assert_drawer(item, background, border):
    assert item.property("radius") == 10
    assert item.property("_drawerBorderWidth") == 1
    assert _rgb(item.property("_drawerBackground")) == background
    assert _rgb(item.property("_drawerBorderColor")) == border


def _assert_scroll_bar(item, track, handle, hover, pressed):
    assert _rgb(item.property("_scrollTrackColor")) == track
    assert _rgb(item.property("_scrollHandleDefaultColor")) == handle
    assert _rgb(item.property("_scrollHandleHoverColor")) == hover
    assert _rgb(item.property("_scrollHandlePressedColor")) == pressed
    assert _rgb(item.property("_scrollHandleColor")) == handle


def _assert_scroll_bar_entry(item, track, handle, hover, pressed):
    assert _rgb(item.property("_scrollTrackColor")) == track
    assert _rgb(item.property("_scrollThumbDefaultColor")) == handle
    assert _rgb(item.property("_scrollThumbHoverColor")) == hover
    assert _rgb(item.property("_scrollThumbPressedColor")) == pressed
    assert _rgb(item.property("_scrollThumbColor")) == handle


def _assert_split_pane(item, grip):
    assert _alpha(item.property("_splitHandleColor")) == 0
    assert _rgb(item.property("_splitGripColor")) == grip


def test_prism_design_containers_layout_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
Drawer {
    drawerWidth: 280
}
"""))
        drawer = keep[-1][1]
        _assert_drawer(drawer, (248, 251, 255), (217, 227, 236))

        keep.append(_build(engine, b"""
import PrismQML
ScrollBar {
}
"""))
        scroll_bar = keep[-1][1]
        _assert_scroll_bar(
            scroll_bar,
            (234, 241, 247),
            (170, 184, 199),
            (143, 160, 178),
            (47, 111, 237),
        )

        keep.append(_build(engine, b"""
import PrismQML
ScrollBarEntry {
}
"""))
        scroll_bar_entry = keep[-1][1]
        _assert_scroll_bar_entry(
            scroll_bar_entry,
            (234, 241, 247),
            (170, 184, 199),
            (143, 160, 178),
            (47, 111, 237),
        )

        keep.append(_build(engine, b"""
import PrismQML
SplitPane {
    preferredWidth: 320
    preferredHeight: 160
}
"""))
        split_pane = keep[-1][1]
        _assert_split_pane(split_pane, (170, 184, 199))

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
Drawer {
    drawerWidth: 280
}
"""))
        dark_drawer = keep[-1][1]
        _assert_drawer(dark_drawer, (36, 43, 52), (48, 58, 70))

        keep.append(_build(engine, b"""
import PrismQML
ScrollBar {
}
"""))
        dark_scroll_bar = keep[-1][1]
        _assert_scroll_bar(
            dark_scroll_bar,
            (21, 26, 32),
            (70, 84, 100),
            (91, 107, 127),
            (122, 167, 255),
        )

        keep.append(_build(engine, b"""
import PrismQML
ScrollBarEntry {
}
"""))
        dark_scroll_bar_entry = keep[-1][1]
        _assert_scroll_bar_entry(
            dark_scroll_bar_entry,
            (21, 26, 32),
            (70, 84, 100),
            (91, 107, 127),
            (122, 167, 255),
        )

        keep.append(_build(engine, b"""
import PrismQML
SplitPane {
    preferredWidth: 320
    preferredHeight: 160
}
"""))
        dark_split_pane = keep[-1][1]
        _assert_split_pane(dark_split_pane, (70, 84, 100))
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
