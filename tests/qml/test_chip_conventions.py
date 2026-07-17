# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chip geometry and interaction regressions. Chip 几何与交互回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "chip-runtime.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property color normalBackground: Enums.stateColor.chipBg
    readonly property color hoverBackground: Enums.stateColor.chipBgHover
    readonly property color pressedBackground: Enums.stateColor.chipBgPressed
    readonly property color checkedBackground: Enums.accentColor
    readonly property color normalContent: Enums.foregroundColor
    readonly property color checkedContent: Enums.chipColors.checkedText

    width: 400
    height: 200
    visible: true

    Chip {
        objectName: "chip"
        x: 80
        y: 60
        width: implicitWidth
        height: implicitHeight
        text: "Alpha"
        icon: Enums.icon.checkmark
    }
}
"""
ANIMATION_SETTLE_MS = 150


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    chip = window.findChild(QQuickItem, "chip")
    assert chip is not None
    return engine, component, window, chip, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = [root]
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _background(chip):
    matches = [
        item
        for item in _visual_descendants(chip)
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.width() == pytest.approx(chip.width())
        and item.height() == pytest.approx(chip.height())
    ]
    assert len(matches) == 1
    return matches[0]


def _close_button(chip):
    matches = [
        item
        for item in _visual_descendants(chip)
        if item.metaObject().className().startswith("CloseButton")
    ]
    assert len(matches) == 1
    return matches[0]


def _point_for(window, item, x_ratio=0.5, y_ratio=0.5):
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() * x_ratio, item.height() * y_ratio)
    )
    return QPoint(round(point.x()), round(point.y()))


def _read(item, name):
    prop = QQmlProperty(item, name)
    assert prop.isValid(), (item.metaObject().className(), name)
    return prop.read()


def _assert_color(actual: QColor, expected: QColor) -> None:
    assert actual.getRgbF() == pytest.approx(expected.getRgbF(), abs=1 / 65535)


def _new_visible_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def test_chip_preserves_default_geometry_and_pointer_states(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, chip, warnings = _create_scene()
    try:
        background = _background(chip)
        assert (chip.width(), chip.height()) == pytest.approx((132, 32))
        assert chip.property("implicitWidth") == pytest.approx(132)
        assert chip.property("implicitHeight") == pytest.approx(32)
        assert not chip.property("hovered")
        assert not chip.property("pressed")
        assert not chip.property("checked")
        _assert_color(background.property("color"), window.property("normalBackground"))
        _assert_color(chip.property("contentColor"), window.property("normalContent"))

        point = _point_for(window, chip, x_ratio=0.25)
        QTest.mouseMove(window, point)
        _pump(ANIMATION_SETTLE_MS)
        assert chip.property("hovered")
        _assert_color(background.property("color"), window.property("hoverBackground"))

        QTest.mousePress(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
        )
        _pump(ANIMATION_SETTLE_MS)
        assert chip.property("pressed")
        _assert_color(background.property("color"), window.property("pressedBackground"))
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_chip_click_toggles_once_and_respects_checkable(qapp):
    engine, component, window, chip, warnings = _create_scene()
    try:
        clicked = []
        toggled = []
        chip.clicked.connect(lambda: clicked.append(True))
        chip.toggled.connect(toggled.append)

        point = _point_for(window, chip, x_ratio=0.25)
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
        )
        _pump(ANIMATION_SETTLE_MS)
        assert chip.property("checked")
        assert toggled == [True]
        assert clicked == [True]
        _assert_color(_background(chip).property("color"), window.property("checkedBackground"))
        _assert_color(chip.property("contentColor"), window.property("checkedContent"))

        chip.setProperty("checkable", False)
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
        )
        _pump(20)
        assert chip.property("checked")
        assert toggled == [True]
        assert clicked == [True, True]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_chip_close_routes_without_toggling_and_updates_width(qapp):
    engine, component, window, chip, warnings = _create_scene()
    try:
        clicked = []
        toggled = []
        dismissed = []
        chip.clicked.connect(lambda: clicked.append(True))
        chip.toggled.connect(toggled.append)
        chip.dismissed.connect(lambda: dismissed.append(True))

        close_button = _close_button(chip)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, close_button),
        )
        _pump(20)
        assert dismissed == [True]
        assert clicked == []
        assert toggled == []
        assert not chip.property("checked")

        chip.setProperty("closable", False)
        _pump(20)
        assert not close_button.isVisible()
        assert chip.property("implicitWidth") == pytest.approx(112)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
