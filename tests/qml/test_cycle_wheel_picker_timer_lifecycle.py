# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""CycleWheelPicker repeat timer lifecycle. 滚轮选择器重复计时器生命周期。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    Qt,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "cycle-wheel-picker-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 200
    height: 360
    visible: true
    color: Enums.backgroundColor

    CycleWheelPicker {
        objectName: "picker"
        x: 30
        width: 140
        height: parent.height
        items: ["Alpha", "Beta", "Gamma"]
        currentIndex: 1
        cycle: false
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


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _timers(picker: QObject) -> list[QObject]:
    return [
        child
        for child in picker.findChildren(QObject)
        if child.metaObject().indexOfProperty("interval") >= 0
        and child.metaObject().indexOfProperty("repeat") >= 0
        and child.property("repeat")
    ]


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


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
    picker = window.findChild(QQuickItem, "picker")
    assert picker is not None
    picker.setCurrentIndex(1)
    assert _wait_for(lambda: picker.property("currentValue") == "Beta")
    return engine, component, window, picker, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_cycle_wheel_picker_first_button_presses_keep_visuals_and_repeat_state(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        QTest.mouseMove(window, QPoint(190, 350))
        _pump()
        QTest.mouseMove(window, QPoint(100, 180))
        assert _wait_for(lambda: picker.property("_hovered"))
        _pump(80)
        hover_hash = _image_hash(window.grabWindow())
        timers = _timers(picker)
        object_count = len(picker.findChildren(QObject))

        QTest.mouseMove(window, QPoint(100, 20))
        assert _wait_for(lambda: picker.property("_hovered"))
        QTest.mousePress(
            window, Qt.MouseButton.LeftButton, pos=QPoint(100, 20)
        )
        assert _wait_for(
            lambda: sum(bool(timer.property("running")) for timer in timers) == 1
        )
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, pos=QPoint(100, 20)
        )
        assert _wait_for(lambda: picker.property("currentIndex") == 0)
        assert all(not timer.property("running") for timer in timers)

        picker.setCurrentIndex(1)
        assert _wait_for(lambda: picker.property("currentIndex") == 1)
        QTest.mouseMove(window, QPoint(100, 340))
        assert _wait_for(lambda: picker.property("_hovered"))
        QTest.mousePress(
            window, Qt.MouseButton.LeftButton, pos=QPoint(100, 340)
        )
        assert _wait_for(
            lambda: sum(bool(timer.property("running")) for timer in timers) == 1
        )
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, pos=QPoint(100, 340)
        )
        assert _wait_for(lambda: picker.property("currentIndex") == 2)
        assert all(not timer.property("running") for timer in timers)

        print(
            "CYCLE_WHEEL_REPEAT",
            f"timers={len(timers)}",
            f"objects={object_count}",
            f"hover_hash={hover_hash}",
        )
        assert len(timers) == 1
        assert object_count == 33
        assert hover_hash == (
            "68d43bde2ec3538f0873fb76e055f5af0c7c82d3d4e34ddbf0643dd229c86b33"
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
