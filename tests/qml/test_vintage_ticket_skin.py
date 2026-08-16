# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket skin entrypoint and token regressions. 复古票据皮肤入口与令牌回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property string skinName: Enums.skin
    readonly property bool ticketActive: Enums.isVintageTicket
    readonly property bool outlined: Enums.hasOutlinedSurfaces
    readonly property bool softElevation: Enums.usesSoftElevation
    readonly property bool micaAllowed: Enums.allowsMica
    readonly property bool usesMonospace: Enums.fontFamily === Enums.fontMonospace
    readonly property int surfaceRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property real surfaceBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color backgroundToken: Enums.backgroundColor
    readonly property color surfaceToken: Enums.cardColor
    readonly property color foregroundToken: Enums.foregroundColor
    readonly property color textToken: Enums.textColor.primary
    readonly property color borderToken: Enums.borderColor
    readonly property color successToken: Enums.statusLevel.getColorByLevel(Enums.statusLevel.success)
    readonly property color dangerToken: Enums.statusLevel.getColorByLevel(Enums.statusLevel.error)
    readonly property color shadowToken: Enums.shadow.level8.color
    readonly property real paperSourceX: ticketPaper._patternSourceX
    readonly property real paperSourceY: ticketPaper._patternSourceY

    width: 96
    height: 96

    TicketPaper {
        id: ticketPaper
        objectName: "ticketPaper"
        anchors.fill: parent
        patternOriginX: 68
        patternOriginY: 48
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
    component.setData(QML_SOURCE, QUrl("inline:vintage-ticket-skin.qml"))
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


def test_vintage_ticket_runtime_tokens_and_texture(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, root, warnings = _create_scene()
    paper = root.findChild(QObject, "ticketPaper")
    assert paper is not None
    try:
        assert root.property("ticketActive") is False
        assert root.property("outlined") is False
        assert root.property("softElevation") is True
        assert root.property("micaAllowed") is True
        assert paper.property("visible") is False

        setSkin(Skin.VINTAGE_TICKET)
        _pump()
        assert root.property("skinName") == "vintage_ticket"
        assert root.property("ticketActive") is True
        assert root.property("outlined") is True
        assert root.property("softElevation") is False
        assert root.property("micaAllowed") is False
        assert root.property("usesMonospace") is True
        assert root.property("surfaceRadius") == 0
        assert root.property("surfaceBorderWidth") == 1
        assert paper.property("visible") is True
        assert root.property("paperSourceX") == -68
        assert root.property("paperSourceY") == -48
        _assert_color(root, "backgroundToken", "#e9e1d2")
        _assert_color(root, "surfaceToken", "#f8f3e8")
        _assert_color(root, "foregroundToken", "#2b211a")
        _assert_color(root, "textToken", "#2b211a")
        _assert_color(root, "borderToken", "#5a4637")
        _assert_color(root, "successToken", "#267451")
        _assert_color(root, "dangerToken", "#a33e36")
        assert root.property("shadowToken").alpha() == 0

        setTheme(Theme.DARK)
        _pump()
        _assert_color(root, "backgroundToken", "#1d1a17")
        _assert_color(root, "surfaceToken", "#28231e")
        _assert_color(root, "foregroundToken", "#ede3d2")
        _assert_color(root, "textToken", "#ede3d2")
        _assert_color(root, "borderToken", "#b4a48e")
        _assert_color(root, "successToken", "#68a77c")
        _assert_color(root, "dangerToken", "#d37b72")

        setSkin(Skin.NEOBRUTALISM)
        _pump()
        assert root.property("ticketActive") is False
        assert paper.property("visible") is False
        assert root.property("surfaceRadius") == 6
        assert root.property("surfaceBorderWidth") == 2
        assert warnings == []
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_invalid_skin_string_still_falls_back_to_fluent():
    from prismqml.python.core.theme import ThemeManager

    manager = ThemeManager()
    previous_skin = manager.getSkin()
    try:
        manager.setSkinFromQml("unknown-skin")
        assert manager.getSkin() is Skin.FLUENT
    finally:
        manager.setSkin(previous_skin)


def test_ticket_content_frame_draws_square_border_without_radius_warning(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    setSkin(Skin.VINTAGE_TICKET)
    engine = QQmlApplicationEngine()
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
import QtQuick.Window
import "../../prismqml/PrismQML/_internal" as Internal

Window {
    width: 320
    height: 240
    visible: true

    Internal.ContentFrame {
        anchors.fill: parent
        backgroundColor: "#f8f3e8"
        cornerRadius: 8
    }
}
""",
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "ticket-content-frame-warning.qml")
        ),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    try:
        _pump(50)
        assert not any(
            "Incorrect argument radius" in warning for warning in warnings
        ), warnings
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()
