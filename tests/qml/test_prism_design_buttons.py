# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design button skin tests."""

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


def _rgba(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
        round(qcolor.alphaF() * 255),
    )


def _split_button_qml():
    button_dir = (
        Path(__file__).resolve().parents[2]
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "buttons"
        / "Button"
    )
    button_dir_url = QUrl.fromLocalFile(str(button_dir)).toString()
    return f"""
import QtQuick
import PrismQML
import "{button_dir_url}" as ButtonInternal

Item {{
    property color hoverColor: dropdown._splitHoverColor
    property color pressedColor: dropdown._splitPressedColor

    ButtonInternal.ButtonDropdown {{
        id: dropdown
        isToolButton: false
        feature: Enums.button.feature_split
        menuItems: ["Open"]
        controlEnabled: true
        loading: false
        parentRadius: Enums.prismDesign.radiusControl
        fontFamily: Enums.fontFamily
        fontSize: Enums.typography.body
        textColor: Enums.accentForeground
        parentStyle: Enums.button.style_primary
    }}
}}
""".encode()


def test_prism_design_split_button_on_accent_overlays(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, _split_button_qml()))
        split_button = keep[-1][1]
        assert _rgba(split_button.property("hoverColor")) == (255, 255, 255, 51)
        assert _rgba(split_button.property("pressedColor")) == (255, 255, 255, 38)

        setTheme(Theme.DARK)
        keep.append(_build(engine, _split_button_qml()))
        dark_split_button = keep[-1][1]
        assert _rgba(dark_split_button.property("hoverColor")) == (255, 255, 255, 77)
        assert _rgba(dark_split_button.property("pressedColor")) == (255, 255, 255, 51)
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


def test_prism_design_filled_button_disabled_keeps_semantic_tint(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
Button {
    text: "Delete"
    style: Enums.button.style_filled
    level: Enums.statusLevel.error
    enabled: false
}
"""))
        button = keep[-1][1]
        assert _rgba(button.property("color")) == (196, 43, 28, 115)

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
Button {
    text: "Delete"
    style: Enums.button.style_filled
    level: Enums.statusLevel.error
    enabled: false
}
"""))
        dark_button = keep[-1][1]
        assert _rgba(dark_button.property("color")) == (255, 153, 164, 115)
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
