# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Popup position tracking regressions. 弹层位置跟踪回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
POPUP_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "utils" / "PopupWindowCore.qml"
)
TIP_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Tooltip"
    / "TipPopup.qml"
)
TRACKER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "_internal"
    / "PopupPositionTracker.qml"
)
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "popup-position-tracking.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int panelOffset: Enums.popupMetrics.panelOffset
    readonly property int controlGap: Enums.popupMetrics.controlGap
    readonly property int tipGap: Enums.spacing.xs

    function openPopup() { popup.openAtControl(anchor) }
    function showTip() { tip.show() }

    width: 420
    height: 280
    visible: true

    Flickable {
        id: flickable
        objectName: "flickable"
        x: 20
        y: 20
        width: 260
        height: 180
        contentWidth: width
        contentHeight: 600
        clip: true

        Rectangle {
            id: anchor
            objectName: "anchor"
            x: 40
            y: 60
            width: 100
            height: 32
            color: Enums.accentColor
        }
    }

    PopupWindowCore {
        id: popup
        objectName: "popup"
        targetControl: anchor
        popupWidth: 180
        popupHeight: 100
        closeOnClickOutside: false
        stealFocus: false
    }

    TipPopup {
        id: tip
        objectName: "tip"
        target: anchor
        modal: false
        duration: Enums.duration.persistent
        animationType: Enums.flyout.dropDown
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_600) -> bool:
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
        and not any(window is accepted for accepted in allowed)
    ]


def _global_origin(window: QQuickWindow, item: QQuickItem):
    return window.mapToGlobal(item.mapToScene(QPointF()).toPoint())


def _repeat_timers(root: QObject) -> list[QObject]:
    return [
        obj
        for obj in root.findChildren(QObject)
        if obj.metaObject().indexOfProperty("interval") >= 0
        and obj.metaObject().indexOfProperty("repeat") >= 0
        and obj.property("repeat")
    ]


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
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    items = {
        name: window.findChild(QQuickItem, name)
        for name in ("anchor", "flickable", "popup", "tip")
    }
    assert all(items.values())
    return engine, component, window, items, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def popup_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_popup_window_follows_target_and_scroll_without_polling(popup_scene):
    window, items, warnings, windows_before = popup_scene
    anchor = items["anchor"]
    flickable = items["flickable"]
    popup = items["popup"]
    popup_windows = popup.findChildren(QWindow)
    assert len(popup_windows) == 1
    popup_window = popup_windows[0]

    assert QMetaObject.invokeMethod(window, "openPopup")
    assert _wait_for(lambda: popup.property("isOpen") and popup_window.isVisible())
    assert _repeat_timers(popup) == []

    target_global = _global_origin(window, anchor)
    assert popup_window.x() == target_global.x() - window.property("panelOffset")
    assert popup_window.y() == (
        target_global.y()
        + round(anchor.height())
        + window.property("controlGap")
        - window.property("panelOffset")
    )

    anchor.setX(anchor.x() + 36)
    target_global = _global_origin(window, anchor)
    assert _wait_for(
        lambda: popup_window.x()
        == target_global.x() - window.property("panelOffset")
    )

    old_y = popup_window.y()
    flickable.setProperty("contentY", 30)
    assert _wait_for(lambda: popup_window.y() == old_y - 30)

    flickable.setProperty("contentY", 260)
    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: not popup_window.isVisible())
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_tip_popup_follows_target_and_closes_out_of_view_without_polling(
    popup_scene,
):
    window, items, warnings, windows_before = popup_scene
    anchor = items["anchor"]
    flickable = items["flickable"]
    tip = items["tip"]
    tip_windows = tip.findChildren(QWindow)
    assert len(tip_windows) == 2
    popup_window = next(
        candidate
        for candidate in tip_windows
        if candidate.width() == 220 and candidate.height() == 90
    )

    assert QMetaObject.invokeMethod(window, "showTip")
    assert _wait_for(lambda: tip.property("_isOpen") and popup_window.isVisible())
    _pump(250)
    assert _repeat_timers(tip) == []

    target_global = _global_origin(window, anchor)
    expected_x = target_global.x() + anchor.width() / 2 - popup_window.width() / 2
    expected_y = target_global.y() + anchor.height() + window.property("tipGap")
    assert _wait_for(lambda: tip.property("_animX") == pytest.approx(expected_x))
    assert _wait_for(lambda: tip.property("_animY") == pytest.approx(expected_y))

    anchor.setX(anchor.x() + 28)
    target_global = _global_origin(window, anchor)
    expected_x = target_global.x() + anchor.width() / 2 - popup_window.width() / 2
    assert _wait_for(lambda: tip.property("_animX") == pytest.approx(expected_x))

    old_y = tip.property("_animY")
    flickable.setProperty("contentY", 24)
    assert _wait_for(lambda: tip.property("_animY") == pytest.approx(old_y - 24))

    flickable.setProperty("contentY", 260)
    assert _wait_for(lambda: not tip.property("_isOpen"))
    assert _wait_for(lambda: not popup_window.isVisible())
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_popup_tracking_source_is_event_driven():
    popup_source = POPUP_SOURCE.read_text(encoding="utf-8")
    tip_source = TIP_SOURCE.read_text(encoding="utf-8")
    tracker_source = TRACKER_SOURCE.read_text(encoding="utf-8")
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")

    for source in (popup_source, tip_source):
        assert "PopupPositionTracker {" in source
        assert "id: positionTracker" not in source
        assert "interval: Enums.popupMetrics.trackerIntervalMs" not in source
    assert "function onAfterAnimating()" in tracker_source
    assert "function scheduleUpdate()" in tracker_source
    assert "Timer {" not in tracker_source
    assert "trackerIntervalMs" not in metrics_source
