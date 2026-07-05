# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design visual specification synchronization tests."""

import re
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs" / "guide" / "prism-design.zh.md"

PRISM_COLOR_TOKENS = (
    "background",
    "surface",
    "raised",
    "overlay",
    "header",
    "tableBg",
    "alternateRow",
    "foreground",
    "secondaryForeground",
    "tertiaryForeground",
    "disabledForeground",
    "primary",
    "primaryLight",
    "primaryDark",
    "primaryForeground",
    "secondary",
    "warm",
    "glow",
    "border",
    "borderLight",
    "borderStrong",
    "divider",
    "hover",
    "pressed",
    "disabled",
    "selected",
    "selectedHover",
    "tableHover",
    "scrollTrack",
    "scrollHandle",
    "scrollHandleHover",
    "transparentHover",
    "transparentPressed",
    "edgeShadow",
)

PRISM_GEOMETRY_TOKENS = (
    "radiusControl",
    "radiusCard",
    "radiusPopup",
    "radiusDialog",
    "borderWidth",
    "focusBorderWidth",
)

TOKEN_ROW_RE = re.compile(
    r"\|\s*`(?P<name>[A-Za-z0-9_]+)`\s*"
    r"\|\s*`(?P<light>#[0-9A-Fa-f]{6,8})`\s*"
    r"\|\s*`(?P<dark>#[0-9A-Fa-f]{6,8})`\s*\|"
)
GEOMETRY_ROW_RE = re.compile(
    r"\|\s*`(?P<name>[A-Za-z0-9_]+)`\s*\|\s*(?P<value>\d+)\s*\|"
)
CHART_ROW_RE = re.compile(
    r"\|\s*(?P<index>\d+)\s*"
    r"\|\s*`(?P<light>#[0-9A-Fa-f]{6})`\s*"
    r"\|\s*`(?P<dark>#[0-9A-Fa-f]{6})`\s*\|"
)


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _qcolor_hex(qcolor) -> str:
    if qcolor.alpha() == 255:
        return f"#{qcolor.red():02X}{qcolor.green():02X}{qcolor.blue():02X}"
    return (
        f"#{qcolor.alpha():02X}{qcolor.red():02X}"
        f"{qcolor.green():02X}{qcolor.blue():02X}"
    )


def _read_visual_spec_tokens():
    spec = SPEC_PATH.read_text(encoding="utf-8")
    color_rows = {}
    geometry_rows = {}
    chart_rows = {}

    for match in TOKEN_ROW_RE.finditer(spec):
        color_rows[match.group("name")] = {
            "light": match.group("light").upper(),
            "dark": match.group("dark").upper(),
        }

    for match in GEOMETRY_ROW_RE.finditer(spec):
        name = match.group("name")
        if name in PRISM_GEOMETRY_TOKENS:
            geometry_rows[name] = int(match.group("value"))

    for match in CHART_ROW_RE.finditer(spec):
        index = int(match.group("index")) - 1
        chart_rows[index] = {
            "light": match.group("light").upper(),
            "dark": match.group("dark").upper(),
        }

    assert set(PRISM_COLOR_TOKENS).issubset(color_rows)
    assert set(PRISM_GEOMETRY_TOKENS).issubset(geometry_rows)
    assert set(range(10)).issubset(chart_rows)
    return color_rows, geometry_rows, chart_rows


def _runtime_prism_tokens(qapp, theme):
    setTheme(theme)
    setSkin(Skin.PRISM_DESIGN)

    color_props = "\n".join(
        f"    property color token_{name}: Enums.prismDesign.{name}"
        for name in PRISM_COLOR_TOKENS
    )
    geometry_props = "\n".join(
        f"    property int token_{name}: Enums.prismDesign.{name}"
        for name in PRISM_GEOMETRY_TOKENS
    )
    chart_props = "\n".join(
        f"    property color chart_{index}: Enums.chartColors.palette[{index}]"
        for index in range(10)
    )
    qml = f"""
import QtQuick
import PrismQML
Item {{
{color_props}
{geometry_props}
{chart_props}
}}
""".encode()

    engine = QQmlApplicationEngine()
    register_types(engine)
    component = None
    item = None
    try:
        component, item = _build(engine, qml)
        qapp.processEvents()
        color_values = {
            name: _qcolor_hex(item.property(f"token_{name}"))
            for name in PRISM_COLOR_TOKENS
        }
        geometry_values = {
            name: item.property(f"token_{name}")
            for name in PRISM_GEOMETRY_TOKENS
        }
        chart_values = {
            index: _qcolor_hex(item.property(f"chart_{index}"))
            for index in range(10)
        }
        return color_values, geometry_values, chart_values
    finally:
        if item is not None:
            item.deleteLater()
        if component is not None:
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()


def test_prism_design_visual_spec_matches_runtime_tokens(qapp):
    spec_colors, spec_geometry, spec_chart = _read_visual_spec_tokens()

    try:
        light_colors, light_geometry, light_chart = _runtime_prism_tokens(qapp, Theme.LIGHT)
        dark_colors, dark_geometry, dark_chart = _runtime_prism_tokens(qapp, Theme.DARK)

        for name in PRISM_COLOR_TOKENS:
            assert light_colors[name] == spec_colors[name]["light"]
            assert dark_colors[name] == spec_colors[name]["dark"]

        for name in PRISM_GEOMETRY_TOKENS:
            assert light_geometry[name] == spec_geometry[name]
            assert dark_geometry[name] == spec_geometry[name]

        for index in range(10):
            assert light_chart[index] == spec_chart[index]["light"]
            assert dark_chart[index] == spec_chart[index]["dark"]
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
