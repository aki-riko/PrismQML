# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphism neutral-state and shared-surface regressions. 新拟态中性状态与通用表面回归。"""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml.python.core import register_types
from prismqml.python.core.theme import Skin, Theme, getSkin, getTheme, setSkin, setTheme


QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property color backgroundToken: Enums.backgroundColor
    readonly property color surfaceToken: Enums.surfaceColor
    readonly property color tableBgToken: Enums.tableBgColor
    readonly property color contentBgToken: Enums.stateColor.contentBg
    readonly property color controlToken: Enums.stateColor.controlBg
    readonly property color hoverToken: Enums.stateColor.controlBgHover
    readonly property color pressedToken: Enums.stateColor.controlBgPressed
    readonly property color disabledToken: Enums.stateColor.controlBgDisabled
    readonly property color selectedToken: Enums.stateColor.selected
    readonly property color selectedHoverToken: Enums.stateColor.selectedHover
    readonly property color menuHoverToken: Enums.stateColor.menuItemHover
    readonly property color menuPressedToken: Enums.stateColor.menuItemPressed
    readonly property color alternateRowToken: Enums.alternateRowColor
    readonly property color scrollTrackToken: Enums.scrollTrackColor
    readonly property color scrollHandleToken: Enums.scrollHandleColor
    readonly property color scrollHandleHoverToken: Enums.scrollHandleHoverColor
    readonly property color neumorphismHoverToken: Enums.neumorphism.hover
    readonly property color neumorphismPressedToken: Enums.neumorphism.pressed
    readonly property color neumorphismDisabledToken: Enums.neumorphism.disabledSurface
    readonly property color neumorphismDividerToken: Enums.neumorphism.divider
    readonly property color neumorphismIndicatorToken: Enums.neumorphism.indicator
    readonly property color neumorphismIndicatorHoverToken: Enums.neumorphism.indicatorHover
    readonly property var borderTokens: [
        Enums.borderColor,
        Enums.borderLightColor,
        Enums.borderStrongColor,
        Enums.stateColor.border,
        Enums.stateColor.borderLight,
        Enums.stateColor.borderStrong,
        Enums.stateColor.inputBorder,
        Enums.stateColor.inputBorderStrong,
        Enums.stateColor.inputBorderNormal,
        Enums.stateColor.inputBorderDisabled,
        Enums.stateColor.cardBorder,
        Enums.stateColor.dialogBorder,
        Enums.stateColor.groupBorder,
        Enums.stateColor.contentBorder,
        Enums.stateColor.pickerBorder,
        Enums.stateColor.settingCardBorder,
        Enums.stateColor.segmentedBorder,
        Enums.stateColor.segmentedSelectedBorder
    ]
    readonly property var dividerTokens: [
        Enums.dividerColor,
        Enums.stateColor.divider,
        Enums.stateColor.navDivider,
        Enums.stateColor.separator,
        Enums.stateColor.expanderSeparator
    ]
    readonly property real buttonRadius: button.radius
    readonly property real buttonBorderWidth: button.border.width
    readonly property real segmentedRadius: segmented.radius
    readonly property real segmentedBorderWidth: segmented.border.width

    width: 400
    height: 160

    Button {
        id: button

        text: "Button"
    }

    SegmentedControl {
        id: segmented

        y: 60
        items: [
            { "key": "one", "text": "One" },
            { "key": "two", "text": "Two" }
        ]
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene() -> tuple[QQmlApplicationEngine, QQmlComponent, QObject, list[str]]:
    engine = QQmlApplicationEngine()
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:neumorphism-state-matrix.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root, warnings


def _alpha(color) -> int:
    return QColor(color).alpha()


def _values(root: QObject, name: str) -> list:
    value = root.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else list(value)


def test_neumorphism_neutral_state_matrix_and_shared_geometry(qapp):
    previous_theme = getTheme()
    previous_skin = getSkin()
    try:
        for theme in (Theme.LIGHT, Theme.DARK):
            setTheme(theme)
            setSkin(Skin.NEUMORPHISM)
            engine, component, root, warnings = _create_scene()
            try:
                assert root.property("backgroundToken") == root.property("surfaceToken")
                assert root.property("backgroundToken") == root.property("tableBgToken")
                assert root.property("backgroundToken") == root.property("contentBgToken")
                assert root.property("backgroundToken") == root.property("controlToken")

                assert root.property("hoverToken") == root.property(
                    "neumorphismHoverToken"
                )
                assert root.property("pressedToken") == root.property(
                    "neumorphismPressedToken"
                )
                assert root.property("disabledToken") == root.property(
                    "neumorphismDisabledToken"
                )
                assert len(
                    {
                        QColor(root.property("controlToken")).name(),
                        QColor(root.property("hoverToken")).name(),
                        QColor(root.property("pressedToken")).name(),
                        QColor(root.property("disabledToken")).name(),
                    }
                ) == 4
                assert root.property("selectedToken") != root.property(
                    "selectedHoverToken"
                )
                assert root.property("menuHoverToken") == root.property("hoverToken")
                assert root.property("menuPressedToken") == root.property("pressedToken")
                assert root.property("alternateRowToken") == root.property("hoverToken")
                assert root.property("scrollTrackToken") != root.property(
                    "scrollHandleToken"
                )
                assert root.property("scrollHandleToken") == root.property(
                    "neumorphismIndicatorToken"
                )
                assert root.property("scrollHandleHoverToken") == root.property(
                    "neumorphismIndicatorHoverToken"
                )

                assert all(_alpha(color) == 0 for color in _values(root, "borderTokens"))
                assert all(_alpha(color) > 0 for color in _values(root, "dividerTokens"))
                assert all(
                    QColor(color) == QColor(root.property("neumorphismDividerToken"))
                    for color in _values(root, "dividerTokens")
                )
                assert root.property("buttonRadius") == 14
                assert root.property("buttonBorderWidth") == 0
                assert root.property("segmentedRadius") == 14
                assert root.property("segmentedBorderWidth") == 0
                assert warnings == []
            finally:
                root.deleteLater()
                component.deleteLater()
                engine.deleteLater()
                _pump()
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
