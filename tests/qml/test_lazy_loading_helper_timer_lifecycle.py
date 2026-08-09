# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Lazy-loading helper timer lifecycle regressions. 懒加载辅助器计时器生命周期回归。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys

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
            Enums.duration.dialog
                - Enums.lazyLoadingTransitionMetrics.coverDuration
        )
    readonly property int expectedPollingInterval: Enums.duration.tick
    readonly property int expectedRenderInterval: Enums.duration.ultraFast
    readonly property int expectedCoverDuration:
        Enums.lazyLoadingTransitionMetrics.coverDuration
    readonly property int expectedRevealDuration:
        Enums.lazyLoadingTransitionMetrics.revealDuration

    function beginSwitch() {
        lazyHelper.showLoadingAndSwitch(1)
    }
    function markTargetLoaded() {
        targetLoaded = true
    }

    width: 320
    height: 180
    visible: true
    color: "#18202b"

    Item {
        id: pageHost
        anchors.fill: parent

        Loader {
            id: firstPage
            objectName: "firstPage"
            anchors.fill: parent
            sourceComponent: Rectangle { color: "#b3d9485f" }
        }

        Loader {
            id: secondPage
            objectName: "secondPage"
            anchors.fill: parent
            sourceComponent: Rectangle { color: "#3487eb" }
            active: false
            visible: false
            opacity: 0
        }
    }

    LazyPageCircleTransition {
        id: sharedPageTransition
        objectName: "lazyPageCircleTransition"
        anchors.fill: parent
    }

    LazyLoadingHelper {
        id: lazyHelper
        objectName: "lazyHelper"

        anchors.fill: parent
        loaders: [firstPage, secondPage]
        targetIndex: 1
        currentVisibleIndex: 0
        loadingText: ""
        pageTransition: sharedPageTransition
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


def _sample_pixel(window: QQuickWindow, x: int, y: int):
    image = window.grabWindow()
    assert not image.isNull()
    image_x = round(x * image.width() / window.width())
    image_y = round(y * image.height() / window.height())
    return image.pixelColor(image_x, image_y)


def _is_old_page(color) -> bool:
    return color.red() > color.blue() + 60 and color.red() > color.green() + 35


def _is_target_page(color) -> bool:
    return color.blue() > color.red() + 60 and color.blue() > color.green() + 25


def _is_loading_background(color) -> bool:
    return color.red() < 60 and color.green() < 70 and color.blue() < 80


def _is_transparent(color) -> bool:
    return color.alpha() < 32


def _is_loading_background_or_transparent(color) -> bool:
    return _is_loading_background(color) or _is_transparent(color)


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
    """旧页先收紧，等待后目标页再展开。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, helper, overlay, warnings = _create_scene()
    try:
        initial_hash = _stable_hash(window)
        initial_object_count = len(helper.findChildren(QObject))
        assert len(_direct_timers(helper)) == 1
        assert _running_timers(helper) == []
        assert _is_old_page(_sample_pixel(window, 160, 90))

        page_transition = window.findChild(QObject, "lazyPageCircleTransition")
        circle_transition = window.findChild(QObject, "qmlPageCircleTransition")
        overlay_window = window.findChild(QQuickWindow, "lazyPageCircleOverlayWindow")
        assert page_transition is not None
        assert circle_transition is not None
        assert overlay_window is not None

        assert QMetaObject.invokeMethod(window, "beginSwitch")
        assert overlay.property("visible") is False
        assert page_transition.property("active") is True
        assert _running_timers(helper) == []
        assert _wait_for(
            lambda: circle_transition.property("collapsing") is True
            and circle_transition.property("running") is True
        )
        assert _wait_for(
            lambda: 0.25 < float(circle_transition.property("progress")) < 0.75
        )
        assert window.property("activatedCount") == 0
        assert _running_timers(helper) == []
        assert overlay.property("visible") is False
        assert page_transition.property("_usingPageLayer") is True
        assert not overlay_window.isVisible()
        collapse_center = _sample_pixel(window, 160, 90)
        collapse_corner = _sample_pixel(window, 6, 6)
        assert _is_loading_background_or_transparent(collapse_corner), collapse_corner

        assert _wait_for(lambda: page_transition.property("collapsed") is True)
        assert _wait_for(lambda: overlay.property("visible") is True), (
            helper.property("pendingTargetIndex"),
            helper.property("isLoadingSwitching"),
            window.property("stageLog"),
            warnings,
        )
        covered_hash = _image_hash(window.grabWindow())
        assert covered_hash != initial_hash
        first_page = window.findChild(QQuickItem, "firstPage")
        assert first_page is not None
        assert first_page.property("visible") is False
        assert _is_loading_background(_sample_pixel(window, 160, 90))
        activation_timer = _direct_timers(helper)[0]
        activation_timer_count = len(_direct_timers(helper))
        assert _running_timers(helper) == [activation_timer]
        assert activation_timer.property("repeat") is False
        assert activation_timer.property("interval") == window.property(
            "expectedActivationInterval"
        )
        assert window.property("activatedCount") == 0

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
        second_page = window.findChild(QQuickItem, "secondPage")
        assert second_page is not None
        assert second_page.property("visible") is True
        assert page_transition.property("active") is True
        assert circle_transition.property("collapsing") is False
        assert _wait_for(
            lambda: 0.25 < float(circle_transition.property("progress")) < 0.75
        )
        assert second_page.property("visible") is True
        assert overlay.property("finishing") is True or not overlay.property("visible")
        assert helper.property("pendingTargetIndex") == 1
        assert page_transition.property("_usingPageLayer") is True
        assert not overlay_window.isVisible()
        expand_center = _sample_pixel(window, 160, 90)
        expand_corner = _sample_pixel(window, 6, 6)
        assert _is_loading_background_or_transparent(expand_corner), expand_corner
        assert _wait_for(lambda: helper.property("pendingTargetIndex") == -1)
        assert _wait_for(lambda: overlay.property("visible") is False)
        assert second_page.property("visible") is True
        assert page_transition.property("active") is False
        assert not overlay_window.isVisible()
        assert _running_timers(helper) == []
        restored_hash = _stable_hash(window)
        settled_timer_count = len(_direct_timers(helper))
        settled_object_count = len(helper.findChildren(QObject))

        print(
            "LAZY_HELPER_TIMER",
            f"timers=1/{activation_timer_count}/{polling_timer_count}/"
            f"{render_timer_count}/{settled_timer_count}",
            f"objects={initial_object_count}/{settled_object_count}",
            f"hashes={initial_hash}/{covered_hash}/{restored_hash}",
            f"collapse={collapse_center.name()}/{collapse_corner.name()}",
            f"expand={expand_center.name()}/{expand_corner.name()}",
        )

        assert (
            activation_timer_count,
            polling_timer_count,
            render_timer_count,
            settled_timer_count,
        ) == (1, 1, 1, 1)
        assert initial_object_count == settled_object_count
        assert initial_hash != restored_hash
        if sys.platform == "win32" and os.environ.get("QT_QPA_PLATFORM") == "windows":
            assert window.rendererInterface().graphicsApi().name == "Direct3D11"
            assert _is_old_page(collapse_center), collapse_center
            assert _is_target_page(expand_center), expand_center
        assert warnings == []
        assert "helper.page_collapse.finish;" in window.property("stageLog")
        assert "helper.wait_indicator.start;" in window.property("stageLog")
        assert "helper.page_expand.finish;" in window.property("stageLog")
        assert "helper.loader_activate.begin;" in window.property("stageLog")
        assert "helper.page_ready;" in window.property("stageLog")
        assert "helper.page_render.begin;" in window.property("stageLog")
        assert "helper.page_expand.begin;" in window.property("stageLog")
        assert "helper.wait_indicator.finish;" in window.property("stageLog")
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
