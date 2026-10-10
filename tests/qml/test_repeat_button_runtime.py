# coding: utf-8
# SPDX-License-Identifier: MIT
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""RepeatButton held-repeat runtime contract. RepeatButton 长按重复运行时合同。

Holding the button must repeat the activation after an initial delay, releasing it must
stop the repetition immediately, and a plain click must stay a single activation.
按住按钮必须在初始延迟后持续重复触发，松开必须立刻停止重复，普通单击必须只触发一次。
"""

from __future__ import annotations

import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
BUTTONS_ROOT = ROOT / "prismqml" / "PrismQML" / "controls" / "buttons"
REPEAT_BUTTON_PATH = BUTTONS_ROOT / "RepeatButton.qml"
REPEAT_TIMER_PATH = BUTTONS_ROOT / "_internal" / "RepeatButtonRepeatTimer.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "repeat-button-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/buttons" as Buttons

Window {
    id: root
    objectName: "hostWindow"
    width: 360
    height: 240
    visible: true

    readonly property int expectedRepeatDelay: Enums.duration.spinBoxRepeatDelay
    readonly property int expectedRepeatInterval: Enums.duration.spinBoxRepeatInterval
    property int heldClicks: 0
    property int heldRepeats: 0
    property int singleClicks: 0
    property int singleRepeats: 0
    property int fixedClicks: 0
    property int fixedRepeats: 0

    Buttons.RepeatButton {
        id: heldButton
        objectName: "heldButton"
        x: 40
        y: 20
        width: 160
        height: 36
        text: "Step"
        repeatDelay: 200
        repeatInterval: 20
        onClicked: root.heldClicks += 1
        onRepeated: root.heldRepeats += 1
    }

    Buttons.RepeatButton {
        id: singleButton
        objectName: "singleButton"
        x: 40
        y: 70
        width: 160
        height: 36
        text: "Single"
        repeatDelay: 400
        repeatInterval: 20
        onClicked: root.singleClicks += 1
        onRepeated: root.singleRepeats += 1
    }

    Buttons.RepeatButton {
        id: fixedButton
        objectName: "fixedButton"
        x: 40
        y: 120
        width: 160
        height: 36
        text: "Fixed"
        autoRepeat: false
        repeatDelay: 100
        repeatInterval: 20
        onClicked: root.fixedClicks += 1
        onRepeated: root.fixedRepeats += 1
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump()
    return engine, component, window, warnings, windows_before


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    _pump(10)


def _button(window: QQuickWindow, object_name: str) -> QQuickItem:
    button = window.findChild(QQuickItem, object_name)
    assert button is not None, object_name
    return button


def _repeat_timer(button: QQuickItem) -> QObject:
    timer = button.findChild(QObject, "repeatButtonRepeatTimer")
    assert timer is not None
    return timer


def _center(button: QQuickItem) -> QPointF:
    return button.mapToScene(QPointF(button.width() / 2, button.height() / 2))


def test_hold_repeats_and_release_stops(qapp):
    """Holding repeats on the repeat interval; releasing stops it at once.

    按住时按重复间隔持续触发；松开立即停止。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        button = _button(window, "heldButton")
        timer = _repeat_timer(button)
        assert timer.property("interval") == 200
        assert timer.property("running") is False
        assert button.property("repeating") is False

        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=_center(button).toPoint())
        assert _wait_for(lambda: button.property("repeating"))
        assert timer.property("interval") == 200
        assert window.property("heldRepeats") == 0
        # The delay phase ends with the first tick, which switches to the repeat interval.
        # 延迟阶段以第一次触发结束, 随后切换到重复间隔。
        assert _wait_for(lambda: timer.property("interval") == 20, 1_500)
        assert _wait_for(lambda: window.property("heldRepeats") >= 4, 1_500)

        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, pos=_center(button).toPoint()
        )
        assert _wait_for(lambda: not button.property("repeating"))
        repeats_after_release = window.property("heldRepeats")
        assert repeats_after_release >= 4
        assert window.property("heldClicks") >= repeats_after_release
        _pump(120)
        assert window.property("heldRepeats") == repeats_after_release
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_quick_click_never_repeats(qapp):
    """A click shorter than the initial delay is one single activation.

    短于初始延迟的点击只是一次普通激活。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        button = _button(window, "singleButton")

        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=_center(button).toPoint())
        _pump(60)

        assert window.property("singleClicks") == 1
        assert window.property("singleRepeats") == 0
        assert button.property("repeating") is False
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_auto_repeat_false_never_repeats(qapp):
    """With autoRepeat disabled a held press stays a single activation.

    关闭 autoRepeat 时按住也只算一次激活。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        button = _button(window, "fixedButton")
        timer = _repeat_timer(button)
        assert button.property("autoRepeat") is False

        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=_center(button).toPoint())
        _pump(400)
        assert timer.property("running") is False
        assert button.property("repeating") is False
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, pos=_center(button).toPoint()
        )
        _pump(60)

        assert window.property("fixedRepeats") == 0
        assert window.property("fixedClicks") == 1
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_repeat_tokens_and_registration_contract():
    """Source contract: shared duration tokens and qmldir registration. 源码合同。"""
    button_source = REPEAT_BUTTON_PATH.read_text(encoding="utf-8")
    timer_source = REPEAT_TIMER_PATH.read_text(encoding="utf-8")
    qmldir_source = (BUTTONS_ROOT / "qmldir").read_text(encoding="utf-8")

    assert "property int repeatDelay: Enums.duration.spinBoxRepeatDelay" in button_source
    assert (
        "property int repeatInterval: Enums.duration.spinBoxRepeatInterval"
        in button_source
    )
    assert "ButtonLeafInternal.RepeatButtonRepeatTimer {" in button_source
    assert "required property var buttonControl" in timer_source
    assert "buttonControl.repeated()" in timer_source
    assert "buttonControl.clicked()" in timer_source
    assert "RepeatButton RepeatButton.qml" in qmldir_source
