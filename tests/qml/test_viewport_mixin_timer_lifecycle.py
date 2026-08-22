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
WATCHER_SOURCE_PATH = TIMER_SOURCE_PATH.with_name("ViewportTargetWatcher.qml")
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


def test_viewport_mixin_keeps_single_ancestor_and_visibility_contract():
    """契约锁定: instanceof 查找 + 不可见即不动画 + 外置 target 监听。

    Locks the unified contract the three consumers migrate onto: ancestor lookup
    by ``instanceof Flickable`` (not duck typing), an invisible target never
    reporting in-viewport, and target observation living in an external helper
    because the mixin is a QtObject.
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    watcher_source = WATCHER_SOURCE_PATH.read_text(encoding="utf-8")

    assert "if (p instanceof Flickable) return p" in source
    assert "p.contentY !== undefined" not in source
    assert "isInViewport = target.visible" in source

    assert "UtilsInternal.ViewportTargetWatcher {" in source
    assert "required property var host" in watcher_source
    assert "function onVisibleChanged() { host._updateViewport() }" in watcher_source
    assert "target: host.target" in watcher_source


NO_FLICKABLE_SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    function hideTarget() { trackedItem.visible = false }
    function showTarget() { trackedItem.visible = true }
    function dropTarget() { decoyMixin.target = null }

    width: 240
    height: 120
    visible: true

    // No Flickable anywhere in this subtree. 整棵子树没有 Flickable。
    Item {
        id: plainParent
        anchors.fill: parent

        Item {
            id: trackedItem
            objectName: "trackedItem"
            y: 20
            width: 40
            height: 20
        }
    }

    // A decoy that quacks like a Flickable but is not one.
    // 一个"看起来像" Flickable 但并不是的诱饵容器。
    Item {
        id: decoy
        objectName: "decoy"
        property real contentY: 0
        property real contentHeight: 320
        property Item contentItem: decoyInner
        anchors.fill: parent

        Item { id: decoyInner }

        Item {
            id: decoyChild
            objectName: "decoyChild"
            y: 20
            width: 40
            height: 20
        }
    }

    ViewportMixin {
        id: plainMixin
        objectName: "plainMixin"
        target: trackedItem
    }

    ViewportMixin {
        id: decoyMixin
        objectName: "decoyMixin"
        target: decoyChild
    }
}
""".encode("utf-8")


def _build_scene(engine, source, url):
    component = QQmlComponent(engine)
    component.setData(source, QUrl(url))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    return component, window


def test_viewport_mixin_without_flickable_follows_target_visibility(qapp):
    """无 Flickable 祖先时必须回退到目标可见性, 不可见就不动画。

    Without a Flickable ancestor the mixin must fall back to plain visibility.
    Returning true for an invisible target would keep shimmer and spinner
    animations running off-screen, which is the regression this gate blocks.
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component, window = _build_scene(
        engine, NO_FLICKABLE_SCENE, "inline:viewport-mixin-no-flickable.qml"
    )
    try:
        plain = window.findChild(QObject, "plainMixin")
        decoy_mixin = window.findChild(QObject, "decoyMixin")
        assert plain is not None
        assert decoy_mixin is not None
        assert _wait_for(lambda: plain.property("ready") is True)
        assert _wait_for(lambda: decoy_mixin.property("ready") is True)

        # No Flickable ancestor was found at all. 完全没找到 Flickable 祖先。
        assert plain.property("_flickableAncestor") is None
        assert plain.property("isInViewport") is True

        assert QMetaObject.invokeMethod(window, "hideTarget")
        assert _wait_for(lambda: plain.property("isInViewport") is False)
        assert QMetaObject.invokeMethod(window, "showTarget")
        assert _wait_for(lambda: plain.property("isInViewport") is True)

        # instanceof, not duck typing: the decoy must not count as a Flickable.
        # 用 instanceof 而非鸭子类型: 诱饵容器不得被当成 Flickable。
        assert decoy_mixin.property("_flickableAncestor") is None
        assert decoy_mixin.property("isInViewport") is True

        # A null target animates nothing. target 为空时不动画。
        assert QMetaObject.invokeMethod(window, "dropTarget")
        decoy_mixin.metaObject().invokeMethod(decoy_mixin, "_updateViewport")
        assert _wait_for(lambda: decoy_mixin.property("isInViewport") is False)

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
