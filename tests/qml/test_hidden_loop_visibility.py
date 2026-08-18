# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Hidden loop visibility regressions. 隐藏循环动画可见性回归。"""

import time
from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "hidden-loop-visibility.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    property bool itemsVisible: true
    readonly property int processingStatus: Enums.statusLevel.processing

    function hideItems() { itemsVisible = false }
    function showItems() { itemsVisible = true }

    width: 360
    height: 160
    visible: true

    Tag {
        objectName: "processingTag"
        width: 80
        height: 28
        visible: window.itemsVisible
        text: "Work"
        status: Enums.statusLevel.processing
    }

    Marquee {
        objectName: "loopingMarquee"
        y: 48
        width: 120
        height: 28
        visible: window.itemsVisible
        text: "Long scrolling text"
        forceScroll: true
        pauseDuration: 0
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while not predicate() and time.monotonic() < deadline:
        _pump()
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _loop_animation(item: QQuickItem) -> QObject:
    animations = [
        child
        for child in item.findChildren(QObject)
        if child.metaObject().indexOfProperty("running") >= 0
        and child.metaObject().indexOfProperty("loops") >= 0
        and child.property("loops") == -1
    ]
    assert len(animations) == 1, [
        child.metaObject().className() for child in animations
    ]
    return animations[0]


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
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(150)
    return engine, component, window, warnings


def test_hidden_loops_preserve_items_and_public_state(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        tag = window.findChild(QQuickItem, "processingTag")
        marquee = window.findChild(QQuickItem, "loopingMarquee")
        assert tag is not None and marquee is not None
        marquee_start_timer = marquee.findChild(QObject, "marqueeStartTimer")
        assert marquee_start_timer is not None
        assert marquee_start_timer.parent() is marquee
        assert marquee_start_timer.property("interval") == 100
        assert marquee_start_timer.property("repeat") is False
        tag_animation = _loop_animation(tag)
        marquee_animation = _loop_animation(marquee)
        assert tag_animation.property("running") is True
        assert _wait_for(
            lambda: marquee_animation.property("running") is True
        )

        assert QMetaObject.invokeMethod(
            window, "hideItems", Qt.ConnectionType.DirectConnection
        )
        _pump()
        assert window.findChild(QQuickItem, "processingTag") is tag
        assert window.findChild(QQuickItem, "loopingMarquee") is marquee
        assert tag.property("status") == window.property("processingStatus")
        assert marquee.property("running") is True
        assert tag_animation.property("running") is False
        assert marquee_animation.property("running") is False

        assert QMetaObject.invokeMethod(
            window, "showItems", Qt.ConnectionType.DirectConnection
        )
        _pump()
        assert window.findChild(QQuickItem, "processingTag") is tag
        assert window.findChild(QQuickItem, "loopingMarquee") is marquee
        assert tag_animation.property("running") is True
        assert _wait_for(
            lambda: marquee_animation.property("running") is True
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        window.setVisible(False)
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []
