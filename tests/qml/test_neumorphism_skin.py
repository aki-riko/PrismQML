# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphism engine skin and reusable surface regressions. 新拟态引擎皮肤回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property string skinName: Enums.skin
    readonly property bool neumorphismActive: Enums.isNeumorphism
    readonly property bool outlined: Enums.hasOutlinedSurfaces
    readonly property bool softElevation: Enums.usesSoftElevation
    readonly property bool neumorphicElevation: Enums.usesNeumorphicElevation
    readonly property bool micaAllowed: Enums.allowsMica
    readonly property int surfaceRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property real surfaceBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color backgroundToken: Enums.backgroundColor
    readonly property color surfaceToken: Enums.cardColor
    readonly property color foregroundToken: Enums.foregroundColor
    readonly property color darkShadowToken: Enums.neumorphism.shadowDark
    readonly property color lightShadowToken: Enums.neumorphism.shadowLight
    readonly property color successToken: Enums.statusLevel.getColorByLevel(Enums.statusLevel.success)

    width: 320
    height: 180

    Button {
        objectName: "button"
        text: "Action"
    }

    InputCore {
        objectName: "input"
        x: 120
    }

    Card {
        objectName: "card"
        x: 120
        y: 72
        width: 160
        height: 80
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
    component.setData(QML_SOURCE, QUrl("inline:neumorphism-skin.qml"))
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


def _assert_color(root: QObject, name: str, expected: str) -> None:
    assert root.property(name) == QColor(expected)


def test_neumorphism_runtime_tokens_and_surfaces(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene()
    try:
        assert root.property("skinName") == "neumorphism"
        assert root.property("neumorphismActive") is True
        assert root.property("outlined") is False
        assert root.property("softElevation") is False
        assert root.property("neumorphicElevation") is True
        assert root.property("micaAllowed") is False
        assert root.property("surfaceRadius") == 14
        assert root.property("surfaceBorderWidth") == 0
        _assert_color(root, "backgroundToken", "#e4ebf3")
        _assert_color(root, "surfaceToken", "#e4ebf3")
        _assert_color(root, "foregroundToken", "#27364a")
        _assert_color(root, "darkShadowToken", "#b7c2d0")
        _assert_color(root, "lightShadowToken", "#ffffff")
        _assert_color(root, "successToken", "#238b64")

        for object_name in ("button", "input", "card"):
            surface = root.findChild(QObject, object_name)
            assert surface is not None
            assert any(
                "NeumorphicShadow" in child.metaObject().className()
                for child in surface.findChildren(QObject)
            )

        setTheme(Theme.DARK)
        _pump()
        _assert_color(root, "backgroundToken", "#252b35")
        _assert_color(root, "surfaceToken", "#252b35")
        _assert_color(root, "foregroundToken", "#e8eef7")
        _assert_color(root, "darkShadowToken", "#171c24")
        _assert_color(root, "lightShadowToken", "#3e4a5b")
        assert warnings == []
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_neumorphism_python_skin_round_trip():
    from prismqml.python.core.theme import ThemeManager

    manager = ThemeManager()
    previous_skin = manager.getSkin()
    try:
        manager.setSkinFromQml("neumorphism")
        assert manager.getSkin() is Skin.NEUMORPHISM
        assert manager.skin == "neumorphism"
    finally:
        manager.setSkin(previous_skin)


def test_neumorphism_is_registered_without_gallery_dependency():
    effect_qmldir = (ROOT / "prismqml" / "PrismQML" / "effects" / "qmldir").read_text(
        encoding="utf-8"
    )
    root_qmldir = (ROOT / "prismqml" / "PrismQML" / "qmldir").read_text(
        encoding="utf-8"
    )
    assert "NeumorphicShadow NeumorphicShadow.qml" in effect_qmldir
    assert "NeumorphicShadow effects/NeumorphicShadow.qml" in root_qmldir
