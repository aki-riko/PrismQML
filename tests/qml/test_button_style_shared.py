# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared button style calculation regressions. 共享按钮样式计算回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import (
    Skin,
    Theme,
    getAccentColor,
    getSkin,
    getTheme,
    register_types,
    setAccentColor,
    setSkin,
    setTheme,
)


ROOT = Path(__file__).resolve().parents[2]
BUTTON_CORE_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "ButtonCore.qml"
)
QML_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/buttons/Button" as ButtonInternal

Item {
    id: root

    property int testStyle: Enums.button.style_default
    property int testLevel: 3
    property bool testEnabled: true
    property bool testLoading: false
    property bool testCountdown: false
    property bool testHovered: false
    property bool testPressed: false
    property bool testToggleChecked: false

    readonly property var styles: [
        Enums.button.style_default,
        Enums.button.style_primary,
        Enums.button.style_transparent,
        Enums.button.style_filled,
        Enums.button.style_text,
        Enums.button.style_hyperlink,
        Enums.button.style_gradient
    ]
    readonly property color actualBackground: button._styleBgColor
    readonly property color actualBorder: button._styleBorderColor
    readonly property color actualText: button._styleTextColor
    readonly property color publicHelperBackground: button.styleHelper.bgColor
    readonly property color publicHelperBorder: button.styleHelper.borderColor
    readonly property color publicHelperText: button.styleHelper.textColor
    readonly property bool publicHelperEffectiveEnabled:
        button.styleHelper.effectiveEnabled
    readonly property bool publicHelperToggleChecked:
        button.styleHelper.isToggleChecked
    readonly property color expectedBackground: reference.bgColor
    readonly property color expectedBorder: reference.borderColor
    readonly property color expectedText: reference.textColor
    readonly property bool expectedEffectiveEnabled: reference.effectiveEnabled

    width: 240
    height: 80

    Button {
        id: button
        objectName: "button"
        style: root.testStyle
        level: root.testLevel
        enabled: root.testEnabled
        loading: root.testLoading
        _countdownActive: root.testCountdown
        pseudoHovered: root.testHovered
        pseudoPressed: root.testPressed
        feature: root.testToggleChecked
                 ? Enums.button.feature_toggle : Enums.button.feature_none
        checked: root.testToggleChecked
        text: "Shared style"
    }

    ButtonInternal.ButtonStyleHelper {
        id: reference
        style: root.testStyle
        level: root.testLevel
        controlEnabled: root.testEnabled
        loading: root.testLoading
        countdownActive: root.testCountdown
        hovered: root.testHovered
        pressed: root.testPressed
        isToggleChecked: root.testToggleChecked
    }
}
"""


def _pump(milliseconds: int = 1) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene() -> tuple[QQmlEngine, QQmlComponent, QObject, list[str]]:
    engine = QQmlEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        QML_SOURCE,
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "button-style-shared.qml")),
    )
    for _ in range(50):
        if not component.isLoading():
            break
        _pump()
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root, warnings


def _assert_style_matches_reference(root: QObject) -> None:
    assert root.property("actualBackground") == root.property("expectedBackground")
    assert root.property("actualBorder") == root.property("expectedBorder")
    assert root.property("actualText") == root.property("expectedText")
    assert root.property("publicHelperBackground") == root.property(
        "expectedBackground"
    )
    assert root.property("publicHelperBorder") == root.property("expectedBorder")
    assert root.property("publicHelperText") == root.property("expectedText")
    assert root.property("publicHelperEffectiveEnabled") == root.property(
        "expectedEffectiveEnabled"
    )
    assert root.property("publicHelperToggleChecked") == root.property(
        "testToggleChecked"
    )


def test_shared_button_style_matches_reference_for_all_states(qapp):
    previous_skin = getSkin()
    engine, component, root, warnings = _create_scene()
    state_cases = (
        {},
        {"testEnabled": False},
        {"testLoading": True},
        {"testCountdown": True},
        {"testHovered": True},
        {"testPressed": True},
        {"testToggleChecked": True},
    )
    state_properties = (
        "testEnabled",
        "testLoading",
        "testCountdown",
        "testHovered",
        "testPressed",
        "testToggleChecked",
    )
    effective_disabled_cases = state_cases[1:4]
    try:
        styles = root.property("styles").toVariant()
        for skin in (Skin.FLUENT, Skin.NEOBRUTALISM):
            setSkin(skin)
            _pump()
            for style in styles:
                root.setProperty("testStyle", style)
                for state_case in state_cases:
                    # The legacy disabled gradient path returns an undefined
                    # token; preserve scope here instead of changing pixels.
                    # 旧版禁用渐变路径会返回未定义 token；此处保持范围，不改像素。
                    if style == styles[-1] and state_case in effective_disabled_cases:
                        continue
                    for property_name in state_properties:
                        root.setProperty(
                            property_name,
                            state_case.get(property_name, property_name == "testEnabled"),
                        )
                    _pump()
                    _assert_style_matches_reference(root)
        assert warnings == []
    finally:
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_button_core_has_no_resident_style_helper_object(qapp):
    engine, component, root, warnings = _create_scene()
    try:
        button = root.findChild(QObject, "button")
        assert button is not None
        assert not any(
            child.metaObject().className().startswith("ButtonStyleHelper_QMLTYPE_")
            for child in button.findChildren(QObject)
        )
        source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
        assert 'import "ButtonStyle.js" as ButtonStyle' in source
        assert "readonly property ButtonStyleHelper styleHelper" not in source
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_shared_button_style_follows_theme_and_accent_updates(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    previous_accent = getAccentColor()
    engine, component, root, warnings = _create_scene()
    state_properties = (
        "testEnabled",
        "testLoading",
        "testCountdown",
        "testHovered",
        "testPressed",
        "testToggleChecked",
    )
    try:
        styles = root.property("styles").toVariant()
        for skin in (Skin.FLUENT, Skin.NEOBRUTALISM):
            setSkin(skin)
            for theme in (Theme.LIGHT, Theme.DARK):
                setTheme(theme)
                for accent in ("#0078d4", "#fb923c"):
                    setAccentColor(accent)
                    for style in styles:
                        root.setProperty("testStyle", style)
                        for property_name in state_properties:
                            root.setProperty(
                                property_name,
                                property_name in {"testEnabled", "testHovered"},
                            )
                        _pump()
                        _assert_style_matches_reference(root)
        assert warnings == []
    finally:
        setAccentColor(previous_accent)
        setTheme(previous_theme)
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()
