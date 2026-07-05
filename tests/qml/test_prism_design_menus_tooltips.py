# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design menu, tooltip and flyout skin tests."""

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


def _build_file(engine, path: Path):
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
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


def _assert_overlay_surface(item, background, border, shadow_alpha=None):
    assert item.property("popupRadius") == 8
    assert item.property("_popupBorderWidth") == 1
    assert _rgb(item.property("_popupBackground")) == background
    assert _rgb(item.property("_popupBorderColor")) == border
    assert item.property("_popupShadowBlur") == 16
    assert item.property("_popupShadowOffset") == 4
    if shadow_alpha is not None:
        assert _alpha(item.property("_popupShadowColor")) == shadow_alpha


def _assert_menu_item(item, hover, pressed, text):
    assert item.property("_itemRadius") == 4
    assert _rgb(item.property("_itemHoverColor")) == hover
    assert _rgb(item.property("_itemPressedColor")) == pressed
    assert _rgb(item.property("_itemTextColor")) == text


def _assert_menu_separator(item):
    assert item.property("height") == item.property("expectedHeight")


def _assert_tip(item, background, border):
    assert item.property("_tipRadius") == 8
    assert item.property("_tipBorderWidth") == 1
    assert _rgb(item.property("_tipBackground")) == background
    assert _rgb(item.property("_tipBorderColor")) == border


def _assert_tooltip(item, background, border):
    assert item.property("_tooltipRadius") == 8
    assert item.property("_tooltipBorderWidth") == 1
    assert _rgb(item.property("_tooltipBackground")) == background
    assert _rgb(item.property("_tooltipBorderColor")) == border
    assert item.property("_tooltipShadowBlur") == 16
    assert item.property("_tooltipShadowOffset") == 4


def _assert_sheet(item, background, border, divider):
    assert item.property("_sheetRadius") == 8
    assert item.property("_sheetBorderWidth") == 1
    assert _rgb(item.property("_sheetBackground")) == background
    assert _rgb(item.property("_sheetBorderColor")) == border
    assert _rgb(item.property("_sheetDividerColor")) == divider


def test_prism_design_menus_tooltips_and_flyouts_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
MenuCore {
    minWidth: 180
    Action { text: "Open"; icon: "FolderOpen" }
    Action { text: "Pin"; checkable: true; checked: true }
}
"""))
        menu = keep[-1][1]
        _assert_overlay_surface(menu, (244, 248, 247), (199, 212, 211), 36)

        keep.append(_build(engine, b"""
import PrismQML
ContextMenu {
    autoBindRightClick: false
    minWidth: 180
    Action { text: "Inspect"; icon: "Search" }
}
"""))
        context_menu = keep[-1][1]
        _assert_overlay_surface(context_menu, (244, 248, 247), (199, 212, 211), 36)

        keep.append(_build(engine, b"""
import PrismQML
SystemTrayMenu {
    minWidth: 180
    Action { text: "Open"; icon: "FolderOpen" }
}
"""))
        system_tray_menu = keep[-1][1]
        _assert_overlay_surface(system_tray_menu, (244, 248, 247), (199, 212, 211), 36)
        assert system_tray_menu.property("showAtCursor") is True

        keep.append(_build(engine, b"""
import PrismQML
MenuSeparator {
    property int expectedHeight: Enums.controlSize.menuSeparatorHeight
}
"""))
        menu_separator = keep[-1][1]
        _assert_menu_separator(menu_separator)

        keep.append(_build(engine, b"""
import PrismQML
Action {
    text: "Pin"
    shortcut: "Ctrl+P"
    checkable: true
    checked: true
}
"""))
        action = keep[-1][1]
        _assert_menu_item(action, (230, 238, 237), (220, 231, 229), (21, 35, 38))

        keep.append(_build(engine, b"""
import PrismQML
MenuDelegate {
    width: 180
    text: "Selected"
    selected: true
}
"""))
        menu_delegate = keep[-1][1]
        _assert_menu_item(menu_delegate, (230, 238, 237), (220, 231, 229), (21, 35, 38))

        keep.append(_build(engine, b"""
import PrismQML
TreeMenuDelegate {
    width: 180
    text: "Branch"
    hasChildren: true
}
"""))
        tree_delegate = keep[-1][1]
        assert tree_delegate.property("_itemRadius") == 4
        assert _rgb(tree_delegate.property("_itemHoverColor")) == (230, 238, 237)
        assert _rgb(tree_delegate.property("_itemPressedColor")) == (220, 231, 229)

        keep.append(_build(engine, b"""
import PrismQML
TooltipCore {
    text: "Overlay tooltip"
}
"""))
        tooltip = keep[-1][1]
        _assert_tooltip(tooltip, (244, 248, 247), (199, 212, 211))

        keep.append(_build(engine, b"""
import PrismQML
Flyout {
    title: "Flyout"
    content: "Overlay surface"
}
"""))
        flyout = keep[-1][1]
        _assert_tip(flyout, (244, 248, 247), (199, 212, 211))

        keep.append(_build(engine, b"""
import PrismQML
TeachingTip {
    title: "Tip"
    content: "Anchored overlay"
}
"""))
        teaching_tip = keep[-1][1]
        _assert_tip(teaching_tip, (244, 248, 247), (199, 212, 211))

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
FlyoutSheet {
    contentItem: Component {
        Item {
            implicitWidth: 120
            implicitHeight: 40
        }
    }
}
"""))
        sheet = keep[-1][1]
        _assert_sheet(sheet, (244, 248, 247), (199, 212, 211), (221, 230, 228))

        matrix_path = (
            Path(__file__).resolve().parents[2]
            / "examples"
            / "pages"
            / "PrismComponentMatrix.qml"
        )
        keep.append(_build_file(engine, matrix_path))

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
MenuCore {
    minWidth: 180
    Action { text: "Open"; icon: "FolderOpen" }
}
"""))
        dark_menu = keep[-1][1]
        _assert_overlay_surface(dark_menu, (31, 42, 45), (42, 57, 59), 54)

        keep.append(_build(engine, b"""
import PrismQML
ContextMenu {
    autoBindRightClick: false
    minWidth: 180
    Action { text: "Inspect"; icon: "Search" }
}
"""))
        dark_context_menu = keep[-1][1]
        _assert_overlay_surface(dark_context_menu, (31, 42, 45), (42, 57, 59), 54)

        keep.append(_build(engine, b"""
import PrismQML
SystemTrayMenu {
    minWidth: 180
    Action { text: "Open"; icon: "FolderOpen" }
}
"""))
        dark_system_tray_menu = keep[-1][1]
        _assert_overlay_surface(dark_system_tray_menu, (31, 42, 45), (42, 57, 59), 54)
        assert dark_system_tray_menu.property("showAtCursor") is True

        keep.append(_build(engine, b"""
import PrismQML
MenuSeparator {
    property int expectedHeight: Enums.controlSize.menuSeparatorHeight
}
"""))
        dark_menu_separator = keep[-1][1]
        _assert_menu_separator(dark_menu_separator)

        keep.append(_build(engine, b"""
import PrismQML
Action {
    text: "Pin"
    checkable: true
    checked: true
}
"""))
        dark_action = keep[-1][1]
        _assert_menu_item(dark_action, (29, 41, 43), (24, 36, 38), (238, 245, 243))

        keep.append(_build(engine, b"""
import PrismQML
TooltipCore {
    text: "Dark overlay tooltip"
}
"""))
        dark_tooltip = keep[-1][1]
        _assert_tooltip(dark_tooltip, (31, 42, 45), (42, 57, 59))

        keep.append(_build(engine, b"""
import PrismQML
Flyout {
    title: "Flyout"
    content: "Dark overlay surface"
}
"""))
        dark_flyout = keep[-1][1]
        _assert_tip(dark_flyout, (31, 42, 45), (42, 57, 59))

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
FlyoutSheet {
    contentItem: Component {
        Item {
            implicitWidth: 120
            implicitHeight: 40
        }
    }
}
"""))
        dark_sheet = keep[-1][1]
        _assert_sheet(dark_sheet, (31, 42, 45), (42, 57, 59), (34, 48, 51))
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
