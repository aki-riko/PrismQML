# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button Neo press-transform lazy loading. 按钮Neo按压变换懒加载回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[2]
QML_SOURCE = b"""
import QtQuick
import PrismQML

Button {
    text: "Neo lazy"
    width: 160
    height: 48
    readonly property real expectedPressShift: Enums.neo.pressOffset
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _transforms(button: QObject) -> list[QObject]:
    return [
        child
        for child in button.findChildren(QObject)
        if child.metaObject().className().startswith("QQuickTranslate")
    ]


def test_neo_press_transform_loads_only_with_neo_skin(qapp):
    previous_skin = getSkin()
    setSkin(Skin.FLUENT)
    engine = QQmlEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:button-neo-lazy.qml"))
    for _ in range(50):
        if not component.isLoading():
            break
        _pump()
    button = component.create()
    assert button is not None, [error.toString() for error in component.errors()]
    try:
        assert _transforms(button) == []

        setSkin(Skin.NEOBRUTALISM)
        _pump()
        transforms = _transforms(button)
        assert len(transforms) == 1
        expected_shift = button.property("expectedPressShift")

        button.setProperty("pseudoPressed", True)
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(expected_shift)
        assert transforms[0].property("x") == pytest.approx(expected_shift)
        assert transforms[0].property("y") == pytest.approx(expected_shift)

        button.setProperty("flat", True)
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(0.0)
        assert _transforms(button) == []

        button.setProperty("flat", False)
        _pump(1)
        transforms = _transforms(button)
        assert len(transforms) == 1
        assert button.property("_neoPressShift") < expected_shift
        assert transforms[0].property("x") < expected_shift
        _pump(250)
        assert transforms[0].property("x") == pytest.approx(expected_shift)

        setSkin(Skin.FLUENT)
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(0.0)
        assert _transforms(button) == []

        setSkin(Skin.NEOBRUTALISM)
        _pump(1)
        transforms = _transforms(button)
        assert len(transforms) == 1
        assert button.property("_neoPressShift") < expected_shift
        assert transforms[0].property("x") < expected_shift
        _pump(250)
        assert transforms[0].property("x") == pytest.approx(expected_shift)
        assert warnings == []
    finally:
        button.setProperty("pseudoPressed", False)
        setSkin(previous_skin)
        button.deleteLater()
        engine.deleteLater()
        _pump(1)
