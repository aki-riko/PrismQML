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
    Q_ARG,
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
    readonly property int pageOutQuintRevealEasing: Easing.OutQuint
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
    function beginInitialLoading() {
        lazyHelper.showInitialLoading(1)
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

    PageTransition {
        id: sharedPageTransition
        objectName: "lazyPageCircleTransition"
        anchors.fill: parent
        animationType: Enums.lazyAnimation.lazy_circle
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
    """Stage-phase timers only: they are the switch's sequential budget.

    The overlay lifecycle guard is a separate, always-direct timer and must not
    be counted as a phase owner. 只取阶段计时器: 它们才是切换的串行预算。遮罩
    生命周期守卫是独立的直接子计时器, 不能算作阶段持有者。
    """
    return [
        child
        for child in helper.children()
        if child.metaObject().className().startswith("QQmlTimer")
        and child.objectName() == "lazyLoaderActivateTimer"
    ]


def _overlay_guard(helper: QObject) -> QObject:
    return helper.findChild(QObject, "lazyOverlayLifecycleGuard")


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
        guard = _overlay_guard(helper)
        assert guard is not None, "LazyLoadingHelper must own the overlay lifecycle guard"
        assert guard.property("running") is False
        assert guard.property("repeat") is True
        assert _running_timers(helper) == []
        assert _is_old_page(_sample_pixel(window, 160, 90))

        page_transition = window.findChild(QObject, "lazyPageCircleTransition")
        circle_transition = window.findChild(QObject, "qmlPageCircleTransition")
        overlay_window = window.findChild(QQuickWindow, "lazyPageCircleOverlayWindow")
        assert page_transition is not None
        assert circle_transition is not None
        assert overlay_window is not None
        assert circle_transition.property("revealEasing") == window.property(
            "pageOutQuintRevealEasing"
        )

        assert QMetaObject.invokeMethod(window, "beginSwitch")
        assert overlay.property("visible") is False
        assert page_transition.property("active") is True
        assert page_transition.property("revealEasing") == window.property(
            "pageOutQuintRevealEasing"
        )
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


def test_initial_loading_overlay_finishes_after_fast_page_ready(qapp):
    """启动首屏快速就绪后，加载覆盖层不得重新显示。"""
    engine, component, window, helper, overlay, warnings = _create_scene()
    try:
        assert QMetaObject.invokeMethod(window, "beginInitialLoading")
        assert _wait_for(lambda: overlay.property("visible") is True)

        # Complete the page before the overlay enter animation has finished.
        # This is the startup timing that previously let the enter animation
        # overwrite the exit animation and leave the spinner visible.
        assert QMetaObject.invokeMethod(window, "markTargetLoaded")
        assert _wait_for(lambda: helper.property("pendingTargetIndex") == -1)
        assert _wait_for(lambda: overlay.property("visible") is False)
        assert overlay.property("finishing") is False
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_lazy_loading_helper_source_reuses_one_stage_timer():
    """Sequential phases reuse one timer. 串行阶段复用一个计时器。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    # Exactly two direct timers: the single phase timer plus the overlay
    # lifecycle guard, which never owns a phase.
    # 直接子计时器只有两个: 唯一阶段计时器 + 遮罩生命周期守卫, 后者不持有阶段。
    assert source.count("Timer {") == 2
    assert source.count('objectName: "lazyLoaderActivateTimer"') == 1
    assert source.count('objectName: "lazyOverlayLifecycleGuard"') == 1
    assert "id: stageTimer" in source
    assert "id: overlayLifecycleGuard" in source
    assert "id: loaderActivateTimer" not in source
    assert "id: lazyLoadTimer" not in source
    assert "id: pageRenderTimer" not in source
    assert "_startLoaderActivationTimer(targetIdx)" in source
    assert "_startLoaderPollingTimer(targetIdx)" in source
    assert "_startPageRenderTimer(targetIdx)" in source


def test_activation_interval_reads_collapse_duration_from_transition():
    """激活间隔必须读实际过渡的收紧时长，而非全局 token。

    coverDuration is overridable per site. Subtracting the global token instead
    of the transition's own value would silently mis-time activation for any
    caller that overrides it, and the error is invisible until someone measures
    frames. coverDuration 可单点覆盖。减全局 token 而非过渡自身取值, 会让覆盖过的
    调用方静默算错激活时机, 而且不逐帧测量根本看不出来。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "helper.pageTransition.coverDuration" in source
    assert "helper.loaderActivationDelay - _elapsedCollapse" in source
    # The bare token must not be what the subtraction reads.
    # 减法读的不得是裸 token。
    assert (
        "helper.loaderActivationDelay\n"
        "                            - Enums.lazyLoadingTransitionMetrics"
        ".coverDuration" not in source
    )


RETARGET_SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/navigation/_internal"
import "../../prismqml/PrismQML/controls/navigation"

Window {
    id: root

    property bool targetLoaded: false
    property int activatedCount: 0
    property string stageLog: ""

    function beginInitialLoading() { lazyHelper.showInitialLoading(1) }
    function markTargetLoaded() { targetLoaded = true }
    function simulateRetarget(newIndex) { lazyHelper.pendingTargetIndex = newIndex }
    function cancelPendingSwitch() {
        lazyHelper.pendingTargetIndex = -1
        lazyHelper.isLoadingSwitching = false
    }
    function startExpand() { sharedTransition.expand(firstPage) }

    width: 360
    height: 220
    visible: true
    color: "#18202b"

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
    }
    Loader {
        id: thirdPage
        objectName: "thirdPage"
        anchors.fill: parent
        sourceComponent: Rectangle { color: "#49d98f" }
        active: false
    }

    PageTransition {
        id: sharedTransition
        objectName: "lazyPageCircleTransition"
        anchors.fill: parent
        animationType: Enums.lazyAnimation.none
    }

    LazyLoadingHelper {
        id: lazyHelper
        objectName: "lazyHelper"
        anchors.fill: parent
        loaders: [firstPage, secondPage, thirdPage]
        targetIndex: 1
        currentVisibleIndex: 0
        loadingText: ""
        pageTransition: sharedTransition
        loaderActivationDelay: Enums.duration.none
        isPageLoadedFunc: function(index) { return index !== 0 && root.targetLoaded }
        isPageLoadFailedFunc: function(index) { return false }
        pageLoadErrorFunc: function(index) { return "" }
        activateLoaderFunc: function(index) {
            root.activatedCount += 1
            if (index === 1) secondPage.active = true
            if (index === 2) thirdPage.active = true
        }
        diagnosticFunc: function(stage, index, details) { root.stageLog += stage + ";" }
        onLoadingComplete: function(targetIndex, previousIndex) {
            firstPage.visible = false
        }
    }
}
"""


def test_retarget_during_render_phase_still_hides_the_loading_overlay(qapp):
    """阶段回调被丢弃时遮罩必须重新武装并收尾。

    The render phase timer is single-shot. A retarget landing between arming that
    callback and its timeout used to return immediately, leaving no owner for the
    overlay exit: the spinner and caption stayed on screen forever.
    渲染阶段计时器是单次的。目标索引在回调武装与触发之间变化时, 旧实现直接 return,
    遮罩退场便失去持有者: 转圈与文案永久留在屏幕上。
    """
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        RETARGET_SCENE_SOURCE,
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "lazy-loading-helper-retarget.qml")
        ),
    )
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
    try:
        assert _wait_for(window.isExposed)
        assert QMetaObject.invokeMethod(window, "beginInitialLoading")
        assert _wait_for(lambda: overlay.property("visible") is True)
        assert QMetaObject.invokeMethod(window, "markTargetLoaded")
        _pump()
        # Retarget while the single-shot render phase callback is still armed.
        # 在单次渲染阶段回调仍武装时改变目标索引。
        assert QMetaObject.invokeMethod(window, "simulateRetarget", Q_ARG("QVariant", 2))
        assert _wait_for(
            lambda: overlay.property("visible") is False, timeout_ms=4_000
        ), (
            helper.property("pendingTargetIndex"),
            helper.property("isLoadingSwitching"),
            overlay.property("running"),
            window.property("stageLog"),
            warnings,
        )
        assert "helper.dropped_phase.rearm;" in window.property("stageLog")
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def _create_retarget_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        RETARGET_SCENE_SOURCE,
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "lazy-loading-helper-retarget.qml")
        ),
    )
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


def test_cancelled_switch_releases_visible_overlay_on_expansion(qapp):
    """切页取消后遮罩必须仍有持有者并正常退场。

    A cancelled switch leaves the overlay on screen with no owner for its exit.
    The expansion callback used to return as soon as the pending target was
    gone, so the spinner and caption stayed parked on screen forever.
    切换取消后遮罩留在屏上且没有退场持有者。展开回调原先在待处理目标消失时直接
    return，转圈与文案便永久停在屏幕上。
    """
    engine, component, window, helper, overlay, warnings = _create_retarget_scene()
    try:
        assert QMetaObject.invokeMethod(window, "beginInitialLoading")
        assert _wait_for(lambda: overlay.property("visible") is True)
        # The host cancels the switch under the still-visible overlay.
        # 宿主在遮罩仍然可见时取消这次切换。
        assert QMetaObject.invokeMethod(window, "cancelPendingSwitch")
        assert QMetaObject.invokeMethod(window, "startExpand")
        assert _wait_for(lambda: overlay.property("visible") is False), (
            helper.property("pendingTargetIndex"),
            helper.property("isLoadingSwitching"),
            overlay.property("visible"),
            overlay.property("finishing"),
            window.property("stageLog"),
            warnings,
        )
        assert overlay.property("finishing") is False
        assert "helper.overlay.release_without_owner;" in window.property("stageLog")
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_cancelled_switch_releases_visible_overlay_through_phase_timer(qapp):
    """阶段计时器丢弃回调时也必须释放仍在屏上的遮罩。

    The stage timer drives the same bookkeeping as the transition callbacks, so
    a cancelled switch must release the overlay from that path too.
    阶段计时器与过渡回调驱动同一套收尾逻辑，取消的切换也必须从该路径释放遮罩。
    """
    engine, component, window, helper, overlay, warnings = _create_retarget_scene()
    try:
        assert QMetaObject.invokeMethod(window, "beginInitialLoading")
        assert _wait_for(lambda: overlay.property("visible") is True)
        assert QMetaObject.invokeMethod(window, "cancelPendingSwitch")
        assert _wait_for(lambda: overlay.property("visible") is False), (
            helper.property("pendingTargetIndex"),
            helper.property("isLoadingSwitching"),
            overlay.property("visible"),
            overlay.property("finishing"),
            window.property("stageLog"),
            warnings,
        )
        assert overlay.property("finishing") is False
        assert "helper.dropped_phase.stop;" in window.property("stageLog")
        assert "helper.overlay.release_without_owner;" in window.property("stageLog")
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
