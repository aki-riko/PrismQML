# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""InfoBar progress branch lifecycle regressions. InfoBar 进度分支生命周期回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "infobar-progress-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property string initialMode: "normal"
    property real initialProgress: 0.42
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

    width: 620
    height: 180
    visible: true

    InfoBarCore {
        objectName: "infoBar"
        anchors.centerIn: parent
        visible: true
        desktopMode: true
        duration: 0
        closable: false
        title: "Progress"
        message: "Processing"
        feature: root.modeFeature
        progress: root.initialProgress
    }
}
"""


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
    info_bar = probe.findChild(QQuickItem, "infoBar")
    assert info_bar is not None
    return engine, component, probe, info_bar, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _progress_controls(info_bar: QQuickItem, prefix: str) -> list[QObject]:
    return [
        obj
        for obj in info_bar.findChildren(QObject)
        if obj.metaObject().className().startswith(prefix)
    ]


def test_normal_infobar_keeps_one_idle_progress_control_per_shape(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, info_bar, warnings = _create_scene("normal")
    try:
        assert len(_progress_controls(info_bar, "ProgressBar")) == 1
        assert len(_progress_controls(info_bar, "ProgressRing")) == 1
        mask = info_bar.findChild(QQuickItem, "infoBarProgressMask")
        content = info_bar.findChild(QQuickItem, "infoBarProgressContent")
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
def test_infobar_reuses_one_bar_control_for_both_modes(
    feature_name, expected_indeterminate, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, info_bar, warnings = _create_scene(feature_name)
    try:
        bars = _progress_controls(info_bar, "ProgressBar")
        assert len(bars) == 1
        assert bars[0].property("indeterminate") is expected_indeterminate
        mask = info_bar.findChild(QQuickItem, "infoBarProgressMask")
        content = info_bar.findChild(QQuickItem, "infoBarProgressContent")
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
def test_infobar_reuses_one_ring_control_for_all_states(
    feature_name, progress, expected_indeterminate, expected_complete, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, info_bar, warnings = _create_scene(
        feature_name, progress
    )
    try:
        rings = _progress_controls(info_bar, "ProgressRing")
        assert len(rings) == 1
        assert rings[0].property("indeterminate") is expected_indeterminate
        assert rings[0].property("visible") is (not expected_complete)
        complete_icon = info_bar.findChild(
            QQuickItem, "infoBarProgressCompleteIcon"
        )
        assert complete_icon is not None
        assert complete_icon.property("visible") is expected_complete
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_infobar_progress_modes_reuse_the_same_controls(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, info_bar, warnings = _create_scene("normal")
    try:
        bar = info_bar.findChild(QQuickItem, "infoBarProgressBar")
        ring = info_bar.findChild(QQuickItem, "infoBarProgressRing")
        assert bar is not None and ring is not None

        window.setProperty("initialMode", "bar")
        assert info_bar.findChild(QQuickItem, "infoBarProgressBar") is bar
        assert not bar.property("indeterminate")

        window.setProperty("initialMode", "indeterminate_bar")
        assert info_bar.findChild(QQuickItem, "infoBarProgressBar") is bar
        assert bar.property("indeterminate")

        window.setProperty("initialMode", "ring")
        assert info_bar.findChild(QQuickItem, "infoBarProgressRing") is ring
        assert ring.property("visible")
        assert not ring.property("indeterminate")

        window.setProperty("initialMode", "indeterminate_ring")
        assert info_bar.findChild(QQuickItem, "infoBarProgressRing") is ring
        assert ring.property("visible")
        assert ring.property("indeterminate")

        window.setProperty("initialMode", "ring")
        window.setProperty("initialProgress", 1.0)
        assert info_bar.findChild(QQuickItem, "infoBarProgressRing") is ring
        assert not ring.property("visible")

        window.setProperty("initialMode", "normal")
        assert info_bar.findChild(QQuickItem, "infoBarProgressBar") is bar
        assert info_bar.findChild(QQuickItem, "infoBarProgressRing") is ring
        assert not ring.property("visible")
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
