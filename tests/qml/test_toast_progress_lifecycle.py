# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toast progress branch lifecycle regressions. Toast 进度分支生命周期回归。"""

from pathlib import Path
from time import perf_counter

import pytest
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
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "toast-progress-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property string initialMode: "normal"
    property real initialProgress: 0.42
    property int autoCloseDuration: 0
    property int completedCloseDuration: 0
    property int closedCount: 0
    readonly property int normalFeature: Enums.notification.feature_normal
    readonly property int barFeature: Enums.notification.feature_progress_bar
    readonly property int indeterminateBarFeature: Enums.notification.feature_indeterminate_bar
    readonly property int ringFeature: Enums.notification.feature_progress_ring
    readonly property int indeterminateRingFeature: Enums.notification.feature_indeterminate_ring
    readonly property int modeFeature:
        initialMode === "bar" ? barFeature :
        initialMode === "indeterminate_bar" ? indeterminateBarFeature :
        initialMode === "ring" ? ringFeature :
        initialMode === "indeterminate_ring" ? indeterminateRingFeature :
        normalFeature

    function showToast() { toast.show() }

    width: 520
    height: 180
    visible: true

    Toast {
        id: toast

        objectName: "toast"
        visible: true
        desktopMode: true
        duration: root.autoCloseDuration
        completeDuration: root.completedCloseDuration
        closable: false
        title: "Progress"
        message: "Processing"
        feature: root.modeFeature
        progress: root.initialProgress
        onClosed: root.closedCount += 1
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_000) -> bool:
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


def _create_scene(feature_name: str, progress: float = 0.42):
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
    probe = component.createWithInitialProperties(
        {"initialMode": feature_name, "initialProgress": progress},
        engine.rootContext(),
    )
    assert isinstance(probe, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    QCoreApplication.processEvents()
    toast = probe.findChild(QQuickItem, "toast")
    assert toast is not None
    return engine, component, probe, toast, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _progress_controls(toast: QQuickItem, prefix: str) -> list[QObject]:
    return [
        obj
        for obj in toast.findChildren(QObject)
        if obj.metaObject().className().startswith(prefix)
    ]


def _timers(toast: QQuickItem) -> list[QObject]:
    return [
        obj
        for obj in toast.findChildren(QObject)
        if obj.metaObject().className().startswith("QQmlTimer")
        and obj.parent() is toast
    ]


def test_toast_keeps_two_close_timers(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene("normal")
    try:
        timers = _timers(toast)
        object_count = len(toast.findChildren(QObject))

        print(
            "TOAST_CLOSE_TIMER",
            f"timers={len(timers)}",
            f"objects={object_count}",
        )

        assert len(timers) == 2
        assert all(timer.property("running") is False for timer in timers)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_toast_show_restarts_auto_close_for_incomplete_progress(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene("bar")
    try:
        auto_close_duration = 120
        assert window.setProperty("autoCloseDuration", auto_close_duration)
        shown_at = perf_counter()
        assert QMetaObject.invokeMethod(window, "showToast")
        _pump(auto_close_duration // 2)
        assert window.property("closedCount") == 0
        assert _wait_for(lambda: window.property("closedCount") == 1)
        elapsed_after_show_ms = (perf_counter() - shown_at) * 1_000

        print(
            "TOAST_INCOMPLETE_SHOW_TIMER",
            f"after_show_ms={elapsed_after_show_ms:.1f}",
        )

        assert elapsed_after_show_ms >= auto_close_duration * 0.75
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_toast_show_does_not_restart_active_completion_timer(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene("bar")
    try:
        shared_duration = 300
        assert window.setProperty("autoCloseDuration", shared_duration)
        assert window.setProperty("completedCloseDuration", shared_duration)
        assert window.setProperty("initialProgress", 1.0)
        _pump(190)
        assert window.property("closedCount") == 0

        shown_at = perf_counter()
        assert QMetaObject.invokeMethod(window, "showToast")
        assert sum(timer.property("running") for timer in _timers(toast)) == 2
        assert _wait_for(lambda: window.property("closedCount") == 1)
        elapsed_after_show_ms = (perf_counter() - shown_at) * 1_000

        print(
            "TOAST_CLOSE_SHOW_TRANSITION",
            f"after_show_ms={elapsed_after_show_ms:.1f}",
        )

        assert elapsed_after_show_ms < shared_duration * 0.75
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_normal_toast_keeps_one_idle_progress_control_per_shape(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene("normal")
    try:
        assert len(_progress_controls(toast, "ProgressBar")) == 1
        assert len(_progress_controls(toast, "ProgressRing")) == 1
        mask = toast.findChild(QQuickItem, "toastProgressMask")
        content = toast.findChild(QQuickItem, "toastProgressContent")
        assert mask is not None and content is not None
        assert QQmlProperty(mask, "layer.enabled").read() is False
        assert QQmlProperty(content, "layer.enabled").read() is False
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


@pytest.mark.parametrize(
    ("feature_name", "expected_indeterminate"),
    [("bar", False), ("indeterminate_bar", True)],
)
def test_toast_reuses_one_bar_control_for_both_modes(
    feature_name, expected_indeterminate, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene(feature_name)
    try:
        bars = _progress_controls(toast, "ProgressBar")
        assert len(bars) == 1
        assert bars[0].property("indeterminate") is expected_indeterminate
        mask = toast.findChild(QQuickItem, "toastProgressMask")
        content = toast.findChild(QQuickItem, "toastProgressContent")
        assert mask is not None and content is not None
        assert QQmlProperty(mask, "layer.enabled").read() is True
        assert QQmlProperty(content, "layer.enabled").read() is True
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


@pytest.mark.parametrize(
    ("feature_name", "progress", "expected_indeterminate", "expected_complete"),
    [
        ("ring", 0.42, False, False),
        ("indeterminate_ring", 0.42, True, False),
        ("ring", 1.0, False, True),
    ],
)
def test_toast_reuses_one_ring_control_for_all_states(
    feature_name, progress, expected_indeterminate, expected_complete, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene(
        feature_name, progress
    )
    try:
        rings = _progress_controls(toast, "ProgressRing")
        assert len(rings) == 1
        assert rings[0].property("indeterminate") is expected_indeterminate
        assert rings[0].property("visible") is (not expected_complete)
        complete_icon = toast.findChild(QQuickItem, "toastProgressCompleteIcon")
        assert complete_icon is not None
        assert complete_icon.property("visible") is expected_complete
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_toast_progress_modes_reuse_the_same_controls(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, toast, warnings = _create_scene("normal")
    try:
        bar = toast.findChild(QQuickItem, "toastProgressBar")
        ring = toast.findChild(QQuickItem, "toastProgressRing")
        assert bar is not None and ring is not None

        window.setProperty("initialMode", "bar")
        assert toast.findChild(QQuickItem, "toastProgressBar") is bar
        assert not bar.property("indeterminate")
        window.setProperty("initialMode", "ring")
        assert toast.findChild(QQuickItem, "toastProgressRing") is ring
        assert ring.property("visible")

        window.setProperty("initialMode", "normal")
        assert toast.findChild(QQuickItem, "toastProgressBar") is bar
        assert toast.findChild(QQuickItem, "toastProgressRing") is ring
        assert not ring.property("visible")
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
