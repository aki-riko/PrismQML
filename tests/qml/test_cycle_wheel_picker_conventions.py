# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Cycle wheel picker parent-chain regressions. 循环滚轮选择器父链回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "cycle-wheel-picker-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 420
    height: 360

    CycleWheelPicker {
        objectName: "cyclePicker"
        x: 40
        width: 140
        items: ["Alpha", "Beta", "Gamma"]
        currentIndex: 1
        cycle: true
        showScrollButtons: false
    }

    CycleWheelPicker {
        objectName: "linearPicker"
        x: 220
        width: 140
        items: ["Alpha", "Beta", "Gamma"]
        currentIndex: 1
        cycle: false
        showScrollButtons: false
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


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
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    cycle_picker = root.findChild(QObject, "cyclePicker")
    linear_picker = root.findChild(QObject, "linearPicker")
    assert cycle_picker is not None
    assert linear_picker is not None
    assert _wait_for(lambda: cycle_picker.property("currentValue") == "Beta")
    assert _wait_for(lambda: linear_picker.property("currentValue") == "Beta")
    return engine, component, root, cycle_picker, linear_picker, warnings


def test_cycle_wheel_picker_public_methods_wrap_and_clamp(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, cycle_picker, linear_picker, warnings = _create_scene()
    try:
        cycle_changes = []
        cycle_picker.currentItemChanged.connect(
            lambda index, value: cycle_changes.append((index, value))
        )
        cycle_picker.scrollDown()
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 2)
        cycle_picker.scrollDown()
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 0)
        cycle_picker.scrollUp()
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 2)
        assert cycle_changes == [
            (2, "Gamma"),
            (0, "Alpha"),
            (2, "Gamma"),
        ]
        cycle_picker.setCurrentValue("Beta")
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 1)
        assert cycle_picker.getCurrentIndex() == 1
        assert cycle_picker.currentItem() == "Beta"
        assert cycle_changes[-1] == (2, "Gamma")

        linear_picker.setCurrentIndex(0)
        linear_picker.scrollUp()
        _pump()
        assert linear_picker.property("currentIndex") == 0
        linear_picker.scrollDown()
        assert _wait_for(lambda: linear_picker.property("currentIndex") == 1)
        linear_picker.setCurrentIndex(2)
        linear_picker.scrollDown()
        _pump()
        assert linear_picker.property("currentIndex") == 2

        linear_picker.setProperty("items", ["Only"])
        assert _wait_for(lambda: linear_picker.property("currentIndex") == 0)
        assert _wait_for(lambda: linear_picker.property("currentValue") == "Only")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []
