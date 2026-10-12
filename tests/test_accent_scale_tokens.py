# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Accent scale token contracts. 强调色阶令牌合同。

覆盖 WinUI 风格色阶的确定性派生、既有 accentColor/accentColorLight/
accentColorDark 语义零回归、QML 侧绑定刷新，以及 Constants.qml 兜底常量表与
Python 派生结果的一致性（防漂移）。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import get_accent_scale, register_types, setAccentColor
from prismqml.python.core.theme import (
    ACCENT_SCALE_STEPS,
    ThemeManager,
    accent_scale_for,
)

DEFAULT_ACCENT = ThemeManager.DEFAULT_ACCENT

ROOT = Path(__file__).resolve().parents[1]
PRISM_ENUMS_DIR = ROOT / "prismqml" / "PrismQML" / "PrismEnums"
PRISM_ENUMS_URL = QUrl.fromLocalFile(str(PRISM_ENUMS_DIR)).toString()

DEFAULT_SCALE = {
    "light3": "#53a7f0",
    "light2": "#258feb",
    "light1": "#1275cb",
    "accent": "#0e5a9c",
    "dark1": "#0a3f6d",
    "dark2": "#06243e",
    "dark3": "#010910",
}

ENUMS_SCENE = """
import QtQuick
import PrismQML

Item {
    property var scale: Enums.accentScale
    property string light3: Enums.accentScale.light3
    property string accent: Enums.accentScale.accent
    property string dark3: Enums.accentScale.dark3
    property int keyCount: Object.keys(Enums.accentScale).length
    property color accentColor: Enums.accentColor
    property color accentColorLight: Enums.accentColorLight
    property color accentColorDark: Enums.accentColorDark
    property color rawAccentColor: Enums.rawAccentColor
}
"""

CONSTANTS_SCENE = f"""
import QtQuick
import "{PRISM_ENUMS_URL}"

Item {{
    Constants {{ id: fallback; isDark: false }}
    property var names: ["light3", "light2", "light1", "accent", "dark1", "dark2", "dark3"]
    property var values: names.map(function (name) {{ return String(fallback.accentScale[name]) }})
    property color defaultAccent: fallback.accentDefaults.accent
}}
"""

CONSTANTS_PALETTE_SCENE = f"""
import QtQuick
import "{PRISM_ENUMS_URL}"

Item {{
    id: root
    property bool dark: false
    Constants {{ id: values; isDark: root.dark }}

    property color neoBackground: values.neoColors.background
    property color ticketBackground: values.ticketColors.background
    property color neumorphismBackground: values.neumorphismColors.background
    property color semanticSuccess: values.semanticColors.successLight
    property color demoBlue: values.demoPalette.blue
    property color automaticColor: values.colorPalette.automaticColor
    property color themeColorFirst: values.colorPalette.themeColors[0]
    property color themeColorLast: values.colorPalette.themeColors[59]
    property color standardColorLast: values.colorPalette.standardColors[9]
    property color hueColor1: values.colorPickerGradient.hueColor1
    property real huePosition6: values.colorPickerGradient.huePos6
}}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _as_mapping(value) -> dict:
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return {str(key): str(item) for key, item in dict(value).items()}


def _assert_constant_palette_values(instance, expected: dict) -> None:
    for property_name, expected_value in expected.items():
        value = instance.property(property_name)
        if property_name == "huePosition6":
            assert value == pytest.approx(expected_value)
        else:
            assert value.name() == expected_value


def _create(engine: QQmlApplicationEngine, source: str, name: str):
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl(f"inline:{name}.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _dispose(engine, component, instance) -> None:
    if instance is not None:
        instance.deleteLater()
    if component is not None:
        component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture()
def accent_scene(qapp):
    del qapp
    manager = ThemeManager()
    previous = manager.accentColor
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        setAccentColor(DEFAULT_ACCENT)
        component, instance = _create(engine, ENUMS_SCENE, "w5-accent-scale")
        _pump()
        yield manager, instance
    finally:
        setAccentColor(previous)
        _dispose(engine, component, instance)


def test_scale_steps_cover_the_seven_winui_names():
    assert [name for name, _delta in ACCENT_SCALE_STEPS] == [
        "light3",
        "light2",
        "light1",
        "accent",
        "dark1",
        "dark2",
        "dark3",
    ]


def test_scale_is_deterministic_for_the_default_accent():
    assert accent_scale_for(DEFAULT_ACCENT) == DEFAULT_SCALE
    assert accent_scale_for(DEFAULT_ACCENT) == accent_scale_for(DEFAULT_ACCENT)


def test_scale_is_deterministic_for_a_custom_accent():
    first = accent_scale_for("#107c10")
    second = accent_scale_for("#107c10")
    assert first == second
    assert first["accent"] == "#107c10"
    assert first != DEFAULT_SCALE
    # Lightness must increase towards light3 and decrease towards dark3.
    # 明度必须由 light3 到 dark3 单调递减。
    from PySide6.QtGui import QColor

    lightness = [QColor(first[name]).lightnessF() for name in DEFAULT_SCALE]
    assert lightness == sorted(lightness, reverse=True)


def test_existing_accent_variants_keep_their_values(qapp):
    del qapp
    manager = ThemeManager()
    previous = manager.accentColor
    try:
        setAccentColor(DEFAULT_ACCENT)
        assert manager.accentColor == "#0e5a9c"
        assert manager.accentColorLight == "#0f63ac"
        assert manager.accentColorDark == "#0c4c85"

        setAccentColor("#107c10")
        assert manager.accentColor == "#107c10"
        assert manager.accentColorLight == "#128812"
        assert manager.accentColorDark == "#0e690e"
    finally:
        setAccentColor(previous)


def test_scale_refreshes_with_the_accent_and_notifies(qapp):
    del qapp
    manager = ThemeManager()
    previous = manager.accentColor
    observed = []

    def record(value):
        observed.append(value)

    manager.accentColorChanged.connect(record)
    try:
        setAccentColor(DEFAULT_ACCENT)
        observed.clear()
        setAccentColor("#107c10")
        assert observed == ["#107c10"]
        assert manager.accentScale["accent"] == "#107c10"
        assert manager.accentScale["dark3"] != DEFAULT_SCALE["dark3"]
        assert get_accent_scale()["accent"] == "#107c10"
    finally:
        manager.accentColorChanged.disconnect(record)
        setAccentColor(previous)


def test_qml_accent_scale_matches_python_derivation(accent_scene):
    manager, instance = accent_scene
    assert instance.property("keyCount") == 7
    assert instance.property("light3") == DEFAULT_SCALE["light3"]
    assert instance.property("accent") == DEFAULT_SCALE["accent"]
    assert instance.property("dark3") == DEFAULT_SCALE["dark3"]
    assert _as_mapping(instance.property("scale")) == DEFAULT_SCALE
    assert manager.accentScale == DEFAULT_SCALE


def test_qml_accent_scale_follows_runtime_accent_change(accent_scene):
    manager, instance = accent_scene
    setAccentColor("#107c10")
    _pump()
    expected = accent_scale_for("#107c10")
    assert _as_mapping(instance.property("scale")) == expected
    assert instance.property("accent") == "#107c10"
    assert instance.property("dark3") == expected["dark3"]


def test_qml_skin_resolved_accent_colors_are_unchanged(accent_scene, qapp):
    del qapp
    from prismqml import Skin, setSkin

    manager, instance = accent_scene
    assert instance.property("accentColor").name() == "#0e5a9c"
    assert instance.property("accentColorLight").name() == "#0f63ac"
    assert instance.property("accentColorDark").name() == "#0c4c85"
    assert instance.property("rawAccentColor").name() == manager.accentColor

    try:
        setSkin(Skin.NEOBRUTALISM)
        _pump()
        # Skin resolver still owns accentColor; the new scale does not interfere.
        # 皮肤解析器仍拥有 accentColor；新增色阶不参与该解析。
        assert instance.property("accentColor").name() != "#0e5a9c"
        assert instance.property("scale") is not None
    finally:
        setSkin(Skin.FLUENT)
        _pump()
    assert instance.property("accentColor").name() == "#0e5a9c"


def test_constants_fallback_scale_matches_python_derivation(qapp):
    del qapp
    engine = QQmlApplicationEngine()
    component = instance = None
    try:
        component, instance = _create(engine, CONSTANTS_SCENE, "w5-accent-fallback")
        assert instance.property("defaultAccent").name() == DEFAULT_ACCENT
        values = instance.property("values")
        if hasattr(values, "toVariant"):
            values = values.toVariant()
        assert list(values) == list(DEFAULT_SCALE.values())
        assert list(values) == list(accent_scale_for(DEFAULT_ACCENT).values())
    finally:
        _dispose(engine, component, instance)


def test_constants_private_palettes_preserve_values_and_theme_bindings(qapp):
    del qapp
    engine = QQmlApplicationEngine()
    component = instance = None
    light_values = {
        "neoBackground": "#fafaf0",
        "ticketBackground": "#e9e1d2",
        "neumorphismBackground": "#e4ebf3",
        "semanticSuccess": "#0f7b0f",
        "demoBlue": "#3b82f6",
        "automaticColor": "#000000",
        "themeColorFirst": "#ffffff",
        "themeColorLast": "#375623",
        "standardColorLast": "#7030a0",
        "hueColor1": "#ffff00",
        "huePosition6": 1.0,
    }
    try:
        component, instance = _create(
            engine, CONSTANTS_PALETTE_SCENE, "w5-constants-private-palettes"
        )
        _assert_constant_palette_values(instance, light_values)

        assert instance.setProperty("dark", True)
        _pump()
        _assert_constant_palette_values(
            instance,
            {
                "neoBackground": "#1a1a1a",
                "ticketBackground": "#1d1a17",
                "neumorphismBackground": "#252b35",
                "semanticSuccess": "#0f7b0f",
                "themeColorLast": "#375623",
            },
        )
    finally:
        _dispose(engine, component, instance)
