# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button Neo press-transform lazy loading. 按钮Neo按压变换懒加载回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

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
CUSTOM_BUTTON_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 260
    height: 160
    visible: true
    color: Enums.backgroundColor

    CustomButtonCore {
        objectName: "customButton"
        anchors.centerIn: parent
        width: 160
        height: 48
        text: "Custom"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _transforms(button: QObject) -> list[QObject]:
    return [
        child
        for child in button.findChildren(QObject)
        if child.metaObject().className().startswith("QQuickTranslate")
    ]


def _behaviors(button: QObject) -> list[QObject]:
    return [
        child
        for child in button.findChildren(QObject)
        if child.metaObject().className() == "QQuickBehavior"
    ]


def _neo_shadows(button: QObject) -> list[QObject]:
    return [
        child
        for child in button.findChildren(QObject)
        if child.metaObject().className().startswith("NeoShadow_QMLTYPE_")
    ]


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise AssertionError("CustomButtonCore frame did not stabilize within 800 ms")


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
        assert _behaviors(button) == []

        setSkin(Skin.NEOBRUTALISM)
        _pump()
        transforms = _transforms(button)
        assert len(transforms) == 1
        assert len(_behaviors(button)) >= 1
        expected_shift = button.property("expectedPressShift")

        button.setProperty("pseudoPressed", True)
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(expected_shift)
        assert transforms[0].property("x") == pytest.approx(expected_shift)
        assert transforms[0].property("y") == pytest.approx(expected_shift)

        button.setProperty("pseudoPressed", False)
        _pump(20)
        assert 0.0 < button.property("_neoPressShift") < expected_shift
        assert 0.0 < transforms[0].property("x") < expected_shift
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(0.0)
        assert transforms[0].property("x") == pytest.approx(0.0)

        button.setProperty("pseudoPressed", True)
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(expected_shift)
        assert transforms[0].property("x") == pytest.approx(expected_shift)

        button.setProperty("flat", True)
        _pump(250)
        assert button.property("_neoPressShift") == pytest.approx(0.0)
        assert _transforms(button) == []
        assert _behaviors(button) == []

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


def test_custom_button_neo_shadow_lifecycle_baseline(qapp):
    """Lock skin/flat shadow counts and pixels before lazy loading.

    延迟加载前固化皮肤/flat 阴影对象数与像素。
    """
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
    component.setData(
        CUSTOM_BUTTON_SOURCE, QUrl("inline:custom-button-neo-lazy.qml")
    )
    for _ in range(50):
        if not component.isLoading():
            break
        _pump()
    window = component.create()
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    button = window.findChild(QObject, "customButton")
    assert button is not None
    try:
        assert _wait_for(window.isExposed)
        shadows = _neo_shadows(button)
        assert len(shadows) == 1
        assert not shadows[0].property("visible")
        fluent_image = _stable_window_image(window)

        setSkin(Skin.NEOBRUTALISM)
        _pump(250)
        shadows = _neo_shadows(button)
        assert len(shadows) == 1
        assert shadows[0].property("visible")
        neo_image = _stable_window_image(window)
        assert neo_image != fluent_image

        button.setProperty("flat", True)
        _pump(250)
        shadows = _neo_shadows(button)
        assert len(shadows) == 1
        assert not shadows[0].property("visible")

        button.setProperty("flat", False)
        _pump(250)
        assert _stable_window_image(window) == neo_image

        setSkin(Skin.FLUENT)
        _pump(250)
        shadows = _neo_shadows(button)
        assert len(shadows) == 1
        assert not shadows[0].property("visible")
        assert _stable_window_image(window) == fluent_image

        setSkin(Skin.NEOBRUTALISM)
        _pump(250)
        assert len(_neo_shadows(button)) == 1
        assert _stable_window_image(window) == neo_image
        assert warnings == []
    finally:
        setSkin(previous_skin)
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)
