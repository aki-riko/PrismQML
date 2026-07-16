# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Remaining component color contracts. 剩余组件颜色合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty

from prismqml import Skin, Theme, register_types, setSkin, setTheme


_ROOT = Path(__file__).resolve().parents[2]
_PIE_SOURCE = _ROOT / "prismqml/PrismQML/controls/data/Chart/_internal/PieChartContent.qml"
_CROPPER_SOURCE = _ROOT / "prismqml/PrismQML/controls/inputs/_internal/ImageCropperContent.qml"
_COMBO_SOURCE = _ROOT / "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxCore.qml"
_TOGGLE_SOURCE = _ROOT / "prismqml/PrismQML/controls/inputs/Toggle/Toggle.qml"
_PROBE_QML = b"""
import QtQuick
import PrismQML

Item {
    readonly property color fixedWhite: Enums.themeColors.accentForeground
    readonly property color accentForeground: Enums.accentForeground

    width: 420
    height: 120

    Toggle {
        objectName: "toggle"
        text: "Choice"
    }

    ComboBox {
        objectName: "combo"
        x: 180
        width: 200
        enabled: false
        model: ["Alpha", "Beta"]
        currentIndex: 0
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
    component.setData(_PROBE_QML, QUrl("inline:remaining-component-colors.qml"))
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
    pending = list(root.children())
    while pending:
        item = pending.pop()
        yield item
        pending.extend(item.children())


def _combo_core(combo):
    matches = [
        item
        for item in _descendants(combo)
        if item.metaObject().indexOfProperty("editable") >= 0
        and item.metaObject().indexOfProperty("useDefaultContent") >= 0
        and item.metaObject().indexOfProperty("isOpen") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _combo_background(core):
    matches = []
    for item in core.children():
        border = QQmlProperty(item, "border.color")
        if border.isValid() and item.metaObject().className().startswith(
            "QQuickRectangle_QML_"
        ):
            matches.append(item)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _assert_rgba(color, expected):
    actual = (color.redF(), color.greenF(), color.blueF(), color.alphaF())
    assert actual == pytest.approx(expected, abs=1 / 65535)


def test_toggle_and_combo_preserve_fixed_runtime_colors(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEOBRUTALISM)
    engine, component, root = _create_scene()
    try:
        toggle = root.findChild(QObject, "toggle")
        combo = root.findChild(QObject, "combo")
        background = _combo_background(_combo_core(combo))
        _assert_rgba(root.property("fixedWhite"), (1, 1, 1, 1))
        _assert_rgba(toggle.property("textColorLight"), (0, 0, 0, 1))
        _assert_rgba(QQmlProperty(background, "border.color").read(), (0, 0, 0, 0.4))
        setTheme(Theme.DARK)
        _pump(5)
        assert toggle.property("textColorLight") == root.property("accentForeground")
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_remaining_component_color_sources_are_characterized():
    assert 'ctx.fillStyle = "white"' in _PIE_SOURCE.read_text(encoding="utf-8")
    assert 'ctx.fillStyle = "white"' in _CROPPER_SOURCE.read_text(encoding="utf-8")
    assert "Qt.rgba(0, 0, 0, 0.4)" in _COMBO_SOURCE.read_text(encoding="utf-8")
    assert 'Enums.accentForeground : "black"' in _TOGGLE_SOURCE.read_text(encoding="utf-8")
