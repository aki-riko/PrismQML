# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TabWidget state color contracts. TabWidget 状态色合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import Skin, Theme, register_types, setSkin, setTheme


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATH = _ROOT / "prismqml/PrismQML/controls/navigation/TabWidget.qml"
_PROBE_QML = b"""
import QtQuick
import PrismQML

Item {
    width: 500
    height: 220

    Component {
        id: page
        Item {}
    }

    TabWidget {
        objectName: "tabWidget"
        width: 480
        height: 200
        movable: true
        tabs: [
            { title: "Alpha", content: page },
            { title: "Bravo", content: page }
        ]
    }
}
"""


def _pump(milliseconds=20):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(_PROBE_QML, QUrl("inline:tab-widget-state-colors.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root


def _descendants(root):
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        yield item
        pending.extend(item.childItems())


def _parts(root):
    tab = root.findChild(QQuickItem, "tabWidget")
    delegates = sorted(
        (
            item
            for item in _descendants(tab)
            if item.metaObject().indexOfProperty("visualOffsetX") >= 0
            and item.metaObject().indexOfProperty("selected") >= 0
        ),
        key=lambda item: item.x(),
    )
    assert len(delegates) == 2
    target = delegates[1]
    backgrounds = [
        item
        for item in target.childItems()
        if item.metaObject().indexOfProperty("radius") >= 0
        and item.metaObject().indexOfProperty("color") >= 0
    ]
    assert len(backgrounds) == 1
    return tab, target, backgrounds[0]


def _assert_color(color, expected):
    actual = (color.redF(), color.greenF(), color.blueF(), color.alphaF())
    assert actual == pytest.approx(expected, abs=1 / 65535)


def _assert_state_colors(tab, delegate, background, expected):
    delegate.setProperty("hovered", True)
    _pump(120)
    _assert_color(background.property("color"), expected["hover"])
    delegate.setProperty("hovered", False)
    delegate.setProperty("pressed", True)
    _pump(120)
    _assert_color(background.property("color"), expected["pressed"])
    delegate.setProperty("pressed", False)
    tab.setProperty("_dragSourceIndex", 1)
    _pump(120)
    _assert_color(background.property("color"), expected["drag"])
    tab.setProperty("_dragSourceIndex", -1)


def test_tab_widget_preserves_fluent_state_colors(qapp):
    setSkin(Skin.FLUENT)
    engine, component, root = _create_scene()
    tab, delegate, background = _parts(root)
    try:
        for theme, expected in (
            (Theme.LIGHT, {"hover": (0, 0, 0, 0.04), "pressed": (0, 0, 0, 0.03), "drag": (0, 0, 0, 0.05)}),
            (Theme.DARK, {"hover": (1, 1, 1, 0.06), "pressed": (1, 1, 1, 0.04), "drag": (1, 1, 1, 0.08)}),
        ):
            setTheme(theme)
            _pump(5)
            _assert_state_colors(tab, delegate, background, expected)
    finally:
        setTheme(Theme.LIGHT)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_tab_widget_state_color_sources_are_characterized():
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    for expression in (
        "Qt.rgba(1, 1, 1, 0.08)",
        "Qt.rgba(0, 0, 0, 0.05)",
        "Qt.rgba(1, 1, 1, 0.04)",
        "Qt.rgba(0, 0, 0, 0.03)",
        "Qt.rgba(1, 1, 1, 0.06)",
        "Qt.rgba(0, 0, 0, 0.04)",
    ):
        assert expression in source
