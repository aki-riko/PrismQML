# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Lazy-loading helper timer lifecycle regressions. 懒加载辅助器计时器生命周期回归。"""

from __future__ import annotations

import hashlib
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
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "navigation"
    / "_internal"
    / "LazyLoadingHelper.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "lazy-loading-helper-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/navigation/_internal"

Window {
    id: root

    property bool targetLoaded: false
    property bool targetFailed: false
    property int activatedCount: 0
    property int completedTarget: -1
    property int completedPrevious: -1
    property string stageLog: ""
    readonly property int expectedActivationInterval:
        Math.max(
            Enums.duration.tick,
            Enums.duration.dialog - Enums.windowCloseMetrics.rippleDuration
        )
    readonly property int expectedPollingInterval: Enums.duration.tick
    readonly property int expectedRenderInterval: Enums.duration.ultraFast
    readonly property int expectedRippleDuration:
        Enums.windowCloseMetrics.rippleDuration

    function beginSwitch() {
        lazyHelper.showLoadingAndSwitch(1)
    }
    function markTargetLoaded() {
        targetLoaded = true
    }

    width: 320
    height: 180
    visible: true
    color: Enums.backgroundColor

    Component {
        id: pageComponent

        Rectangle {
            color: Enums.cardColor
        }
    }

    Loader {
        id: firstPage
        objectName: "firstPage"
        anchors.fill: parent
        sourceComponent: pageComponent
    }

    Loader {
        id: secondPage
        objectName: "secondPage"
        anchors.fill: parent
        sourceComponent: pageComponent
        active: false
        visible: false
        opacity: 0
    }

    LazyLoadingHelper {
        id: lazyHelper
        objectName: "lazyHelper"

        anchors.fill: parent
        loaders: [firstPage, secondPage]
        targetIndex: 1
        currentVisibleIndex: 0
        loaderActivationDelay: Enums.duration.dialog
        isPageLoadedFunc: function(index) {
            return index === 1 && root.targetLoaded
        }
        isPageLoadFailedFunc: function(index) {
            return index === 1 && root.targetFailed
        }
        pageLoadErrorFunc: function(index) {
            return index === 1 ? "controlled failure" : ""
        }
        activateLoaderFunc: function(index) {
            if (index === 1) {
                root.activatedCount += 1
                secondPage.active = true
            }
        }
        diagnosticFunc: function(stage, index, details) {
            root.stageLog += stage + ";"
        }

        onLoadingComplete: function(targetIndex, previousIndex) {
            root.completedTarget = targetIndex
            root.completedPrevious = previousIndex
            firstPage.visible = false
            secondPage.visible = true
            secondPage.opacity = 1
        }
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


def _direct_timers(helper: QObject) -> list[QObject]:
    return [
        child
        for child in helper.children()
        if child.metaObject().className().startswith("QQmlTimer")
    ]


def _running_timers(helper: QObject) -> list[QObject]:
    return [timer for timer in _direct_timers(helper) if timer.property("running")]


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def _stable_hash(window: QQuickWindow) -> str:
    previous = ""
    stable_count = 0
    for _ in range(30):
        _pump(40)
        image = window.grabWindow()
        assert not image.isNull()
        current = _image_hash(image)
        stable_count = stable_count + 1 if current == previous else 1
        if stable_count >= 3:
            return current
        previous = current
    raise AssertionError("Lazy-loading helper pixels did not stabilize")


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
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    helper = window.findChild(QQuickItem, "lazyHelper")
    overlay = window.findChild(QQuickItem, "lazyLoadingOverlay")
    assert helper is not None
    assert overlay is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, helper, overlay, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_lazy_loading_helper_timer_phase_baseline(qapp):
    """One timer starts only after the ripple entrance. 唯一计时器仅在涟漪入场后启动。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, helper, overlay, warnings = _create_scene()
    try:
        initial_hash = _stable_hash(window)
        initial_object_count = len(helper.findChildren(QObject))
        assert len(_direct_timers(helper)) == 1
        assert _running_timers(helper) == []

        assert QMetaObject.invokeMethod(window, "beginSwitch")
        assert _wait_for(lambda: overlay.property("visible") is True), (
            helper.property("pendingTargetIndex"),
            helper.property("isLoadingSwitching"),
            window.property("stageLog"),
            warnings,
        )
        assert overlay.property("entering") is True
        _pump(window.property("expectedRippleDuration") // 2)
        assert overlay.property("entering") is True
        assert window.property("activatedCount") == 0
        assert _running_timers(helper) == []

        activation_timer = _direct_timers(helper)[0]
        activation_timer_count = len(_direct_timers(helper))
        assert window.property("expectedActivationInterval") == 1

        assert _wait_for(lambda: window.property("activatedCount") == 1)
        assert _wait_for(
            lambda: len(_running_timers(helper)) == 1
            and _running_timers(helper)[0].property("repeat") is True
        )
        polling_timer = _running_timers(helper)[0]
        polling_timer_count = len(_direct_timers(helper))
        assert polling_timer.property("interval") == window.property(
            "expectedPollingInterval"
        )

        assert QMetaObject.invokeMethod(window, "markTargetLoaded")
        assert _wait_for(
            lambda: len(_running_timers(helper)) == 1
            and _running_timers(helper)[0].property("repeat") is False
            and _running_timers(helper)[0].property("interval")
            == window.property("expectedRenderInterval")
        )
        render_timer_count = len(_direct_timers(helper))

        assert _wait_for(lambda: window.property("completedTarget") == 1)
        assert window.property("completedPrevious") == 0
        assert _wait_for(lambda: helper.property("pendingTargetIndex") == -1)
        assert _wait_for(lambda: overlay.property("visible") is False)
        assert _running_timers(helper) == []
        restored_hash = _stable_hash(window)
        settled_timer_count = len(_direct_timers(helper))
        settled_object_count = len(helper.findChildren(QObject))

        print(
            "LAZY_HELPER_TIMER",
            f"timers=1/{activation_timer_count}/{polling_timer_count}/"
            f"{render_timer_count}/{settled_timer_count}",
            f"objects={initial_object_count}/{settled_object_count}",
            f"hashes={initial_hash}/{restored_hash}",
        )

        assert (
            activation_timer_count,
            polling_timer_count,
            render_timer_count,
            settled_timer_count,
        ) == (1, 1, 1, 1)
        assert (initial_object_count, settled_object_count) == (17, 18)
        assert (initial_hash, restored_hash) == (
            "1516b21572cdecd2baad775e49c4a2d235b7ce37c9692d90df6b9e0df92f820c",
            "1516b21572cdecd2baad775e49c4a2d235b7ce37c9692d90df6b9e0df92f820c",
        )
        assert warnings == []
        assert "helper.ripple_entrance.finish;" in window.property("stageLog")
        assert "helper.loader_activate.begin;" in window.property("stageLog")
        assert "helper.page_ready;" in window.property("stageLog")
        assert "helper.page_render.begin;" in window.property("stageLog")
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and not any(candidate is existing for existing in windows_before)
        ] == []


def test_lazy_loading_helper_source_reuses_one_stage_timer():
    """Sequential phases reuse one timer. 串行阶段复用一个计时器。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("Timer {") == 1
    assert "id: stageTimer" in source
    assert "id: loaderActivateTimer" not in source
    assert "id: lazyLoadTimer" not in source
    assert "id: pageRenderTimer" not in source
    assert "_startLoaderActivationTimer(targetIdx)" in source
    assert "_startLoaderPollingTimer(targetIdx)" in source
    assert "_startPageRenderTimer(targetIdx)" in source
