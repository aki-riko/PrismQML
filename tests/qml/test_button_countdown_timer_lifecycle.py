# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button countdown timer lifecycle regressions. 按钮倒计时器生命周期回归。"""

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, QUrl, Qt
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


SCENE_URL = QUrl("button-countdown-timer-lifecycle.qml")
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int finishedCount: 0
    readonly property int expectedInterval: Enums.duration.countUp
    readonly property int featureNone: Enums.button.feature_none

    width: 320
    height: 120
    visible: true

    Button {
        id: countdownButton
        objectName: "countdownButton"
        anchors.centerIn: parent
        width: 180
        height: 40
        feature: Enums.button.feature_countdown
        countdown: 1
        text: "Countdown"
        onCountdownFinished: root.finishedCount += 1
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
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
    _pump(30)
    return engine, component, window, warnings


def _countdown_loader(button: QQuickItem):
    matches = [
        child
        for child in button.findChildren(QQuickItem)
        if child.metaObject().indexOfProperty("button") >= 0
        and child.metaObject().indexOfProperty("sourceComponent") >= 0
        and child.metaObject().indexOfProperty("active") >= 0
        and child.property("active")
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def test_countdown_timer_ticks_finishes_and_is_destroyed_with_feature(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        button = window.findChild(QQuickItem, "countdownButton")
        assert button is not None
        loader = _countdown_loader(button)
        assert loader.property("active")

        timer = loader.property("item")
        assert timer is not None
        assert timer.property("button") == button
        assert timer.property("interval") == window.property("expectedInterval")
        assert not timer.property("running")

        center = button.mapToScene(
            QPointF(button.width() / 2, button.height() / 2)
        ).toPoint()
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            center,
        )

        assert _wait_for(lambda: button.property("_countdownActive"))
        assert button.property("_countdownRemaining") == 1
        assert _wait_for(lambda: window.property("finishedCount") == 1)
        assert not button.property("_countdownActive")
        assert button.property("_countdownRemaining") == 0
        assert not timer.property("running")

        button.setProperty("feature", window.property("featureNone"))
        assert _wait_for(lambda: not loader.property("active"))
        assert _wait_for(lambda: loader.property("item") is None)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
