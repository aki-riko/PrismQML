# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ViewportMixin initialization timer regressions. 视口混入初始化计时器回归。"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "ViewportMixin.qml"
)
TIMER_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "ViewportInitTimer.qml"
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    function scrollOut() { viewport.contentY = 220 }
    function scrollBack() { viewport.contentY = 0 }
    function hideTarget() {
        trackedItem.visible = false
        viewport.contentY = 1
    }
    function showTarget() {
        trackedItem.visible = true
        viewport.contentY = 0
    }

    width: 240
    height: 120
    visible: true

    Flickable {
        id: viewport
        objectName: "viewport"
        anchors.fill: parent
        contentWidth: width
        contentHeight: 320

        Item {
            id: trackedItem
            objectName: "trackedItem"
            y: 20
            width: 40
            height: 20
        }
    }

    ViewportMixin {
        id: viewportMixin
        objectName: "viewportMixin"
        target: trackedItem
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
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


def test_viewport_mixin_init_timer_and_visibility_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("inline:viewport-mixin-timer.qml"))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    try:
        mixin = window.findChild(QObject, "viewportMixin")
        target = window.findChild(QQuickItem, "trackedItem")
        timer = window.findChild(QObject, "viewportInitTimer")
        assert mixin is not None
        assert target is not None
        assert timer is not None
        assert timer.parent() is mixin
        assert timer.property("host") == mixin
        assert timer.property("interval") == 50
        assert timer.property("repeat") is False
        assert _wait_for(lambda: mixin.property("ready") is True)
        assert mixin.property("isInViewport") is True

        assert QMetaObject.invokeMethod(window, "scrollOut")
        assert _wait_for(lambda: mixin.property("isInViewport") is False)
        assert QMetaObject.invokeMethod(window, "scrollBack")
        assert _wait_for(lambda: mixin.property("isInViewport") is True)
        assert QMetaObject.invokeMethod(window, "hideTarget")
        assert _wait_for(lambda: mixin.property("isInViewport") is False)
        assert QMetaObject.invokeMethod(window, "showTarget")
        assert _wait_for(lambda: mixin.property("isInViewport") is True)

        timers = window.findChildren(QObject, "viewportInitTimer")
        assert len(timers) == 1
        assert warnings == []
    finally:
        window.close()
        for obj in (window, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and not any(candidate is existing for existing in windows_before)
        ] == []


def test_viewport_mixin_source_keeps_init_timer_external():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    timer_source = TIMER_SOURCE_PATH.read_text(encoding="utf-8")
    assert "UtilsInternal.ViewportInitTimer {" in source
    assert "host: mixin" in source
    assert "property Timer initTimer: Timer {" not in source
    assert "interval: 50" in timer_source
    assert "onTriggered: host._init()" in timer_source
