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
    Property,
    Slot,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from examples.resources import register_gallery_resources
from prismqml import register_types
from prismqml.python.core.incubation import install_incubation_controller


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
TRACKER_TIMER_SOURCE = TRACKER_SOURCE.with_name("PopupPositionUpdateTimer.qml")
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "popup-position-tracking.qml")
)
MENU_PAGE_URL = QUrl.fromLocalFile(str(ROOT / "examples" / "pages" / "MenuPage.qml"))
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
    readonly property int tipAutoCloseDuration: Enums.duration.fast
    readonly property int tipManualCloseDuration: Enums.duration.slow

    function openPopup() { popup.openAtControl(anchor) }
    function showTip() { tip.show() }
    function useFlyout() { tip.tipType = Enums.tip.type_flyout }
    function useTeachingTip() { tip.tipType = Enums.tip.type_teaching_tip }

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


class _RecordingShadowManager(QObject):
    def __init__(self, events):
        super().__init__()
        self._events = events

    @Property(bool, constant=True)
    def useNative(self):
        return True

    @Slot(QObject, result=bool)
    def enableShadowForWindow(self, window):
        self._events.append(("enable", window.isVisible(), window.opacity()))
        return True

    @Slot(QObject, result=bool)
    def disableShadowForWindow(self, window):
        self._events.append(("disable", window.isVisible(), window.opacity()))
        return True
ASYNC_MENU_SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: root
    objectName: "asyncMenuWindow"

    readonly property bool menuReady: menuLoader.status === Loader.Ready

    width: 900
    height: 700
    visible: true

    Loader {{
        id: menuLoader
        objectName: "menuLoader"
        anchors.fill: parent
        asynchronous: true
        source: "{MENU_PAGE_URL.toString()}"
    }}
}}
""".encode("utf-8")


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


def _popup_trackers(root: QObject) -> list[QObject]:
    return [
        obj
        for obj in root.findChildren(QObject)
        if obj.metaObject().className().startswith("PopupPositionTracker_")
    ]


def _tracker_connections(tracker: QObject) -> list[QObject]:
    return [
        obj
        for obj in tracker.findChildren(QObject)
        if obj.metaObject().className().startswith("QQmlConnections_")
    ]


def _create_scene(shadow_manager=None):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    if shadow_manager is not None:
        engine.rootContext().setContextProperty("ShadowManager", shadow_manager)
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


def _create_async_menu_scene():
    assert register_gallery_resources()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    install_incubation_controller(engine)
    component = QQmlComponent(engine)
    component.setData(ASYNC_MENU_SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    loader = window.findChild(QQuickItem, "menuLoader")
    assert loader is not None
    assert _wait_for(lambda: window.property("menuReady"), timeout_ms=5_000)
    return engine, component, window, loader, warnings


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
    assert popup.findChildren(QWindow) == []

    assert QMetaObject.invokeMethod(window, "openPopup")
    popup_windows = popup.findChildren(QWindow)
    assert len(popup_windows) == 1
    popup_window = popup_windows[0]

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
    assert tip.findChildren(QWindow) == []

    assert QMetaObject.invokeMethod(window, "showTip")
    assert _wait_for(lambda: tip.property("_isOpen"))
    tip_windows = tip.findChildren(QWindow)
    assert len(tip_windows) == 1
    popup_window = tip_windows[0]
    assert popup_window.width() == 220
    assert popup_window.height() == 90
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


def test_tip_popup_attaches_native_shadow_after_reveal_animation(qapp):
    shadow_events = []
    shadow_manager = _RecordingShadowManager(shadow_events)
    engine, component, window, items, warnings = _create_scene(shadow_manager)
    try:
        tip = items["tip"]
        assert QMetaObject.invokeMethod(window, "showTip")
        assert _wait_for(lambda: tip.property("_isOpen"))
        popup_window = tip.findChildren(QWindow)[0]

        _pump(20)
        assert shadow_events == []
        assert _wait_for(lambda: bool(shadow_events))

        assert shadow_events[0][0] == "enable"
        assert shadow_events[0][1] is True
        assert float(shadow_events[0][2]) == pytest.approx(1.0)

        assert QMetaObject.invokeMethod(tip, "close")
        assert _wait_for(lambda: not popup_window.isVisible())
        assert shadow_events[-1][0] == "disable"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_tip_popup_prewarm_creates_hidden_reusable_window(popup_scene):
    window, items, warnings, _windows_before = popup_scene
    tip = items["tip"]
    assert tip.findChildren(QWindow) == []

    assert QMetaObject.invokeMethod(tip, "prewarm")
    tip_windows = tip.findChildren(QWindow)
    assert len(tip_windows) == 1
    assert tip.property("_prewarmed")
    assert not tip_windows[0].isVisible()
    assert not tip.property("_isOpen")

    assert QMetaObject.invokeMethod(window, "showTip")
    assert _wait_for(lambda: tip.property("_isOpen") and tip_windows[0].isVisible())
    assert tip.findChildren(QWindow) == tip_windows
    assert warnings == []


def test_tip_popup_auto_close_timer_preserves_close_lifecycle(popup_scene):
    window, items, warnings, _windows_before = popup_scene
    tip = items["tip"]
    timer = tip.findChild(QObject, "tipPopupAutoCloseTimer")
    assert timer is not None
    assert timer.parent() is tip
    assert timer.property("host") == tip
    assert timer.property("repeat") is False
    assert timer.property("running") is False

    auto_close_duration = window.property("tipAutoCloseDuration")
    assert tip.setProperty("duration", auto_close_duration)
    assert timer.property("interval") == auto_close_duration
    assert QMetaObject.invokeMethod(window, "showTip")
    assert timer.property("running") is True
    assert _wait_for(lambda: not tip.property("_isOpen"))
    assert timer.property("running") is False

    manual_close_duration = window.property("tipManualCloseDuration")
    assert tip.setProperty("duration", manual_close_duration)
    assert QMetaObject.invokeMethod(window, "showTip")
    assert timer.property("running") is True
    assert QMetaObject.invokeMethod(tip, "close")
    assert timer.property("running") is False
    assert _wait_for(lambda: not tip.property("_isOpen"))
    assert warnings == []


def test_tip_popup_reuses_arrow_window_across_runtime_type_changes(popup_scene):
    window, items, warnings, _windows_before = popup_scene
    tip = items["tip"]

    assert QMetaObject.invokeMethod(tip, "prewarm")
    flyout_windows = tip.findChildren(QWindow)
    assert len(flyout_windows) == 1

    assert QMetaObject.invokeMethod(window, "useTeachingTip")
    assert QMetaObject.invokeMethod(tip, "prewarm")
    teaching_windows = tip.findChildren(QWindow)
    assert len(teaching_windows) == 2
    assert flyout_windows[0] in teaching_windows
    assert not any(candidate.isVisible() for candidate in teaching_windows)

    assert QMetaObject.invokeMethod(window, "useFlyout")
    assert QMetaObject.invokeMethod(window, "showTip")
    assert _wait_for(lambda: tip.property("_isOpen"))
    assert tip.findChildren(QWindow) == teaching_windows
    assert sum(candidate.isVisible() for candidate in teaching_windows) == 1
    assert QMetaObject.invokeMethod(tip, "close")
    assert _wait_for(lambda: not any(candidate.isVisible() for candidate in teaching_windows))
    assert warnings == []


def test_popup_tracking_source_is_event_driven():
    popup_source = POPUP_SOURCE.read_text(encoding="utf-8")
    tip_source = TIP_SOURCE.read_text(encoding="utf-8")
    tracker_source = TRACKER_SOURCE.read_text(encoding="utf-8")
    tracker_timer_source = TRACKER_TIMER_SOURCE.read_text(encoding="utf-8")
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")

    for source in (popup_source, tip_source):
        assert "PopupPositionTracker {" in source
        assert "id: positionTracker" not in source
        assert "interval: Enums.popupMetrics.trackerIntervalMs" not in source
    assert "referenceControlWidth" not in popup_source
    assert "centerOffset" not in popup_source
    assert "function onAfterAnimating()" in tracker_source
    assert "function scheduleUpdate()" in tracker_source
    assert "Qt.callLater" not in tracker_source
    assert "PopupInternal.PopupPositionUpdateTimer {" in tracker_source
    assert "\n    Timer {" not in tracker_source
    assert "repeat: false" in tracker_timer_source
    assert "repeat: true" not in tracker_timer_source
    assert "repeat: true" not in tracker_source
    assert "trackerIntervalMs" not in metrics_source


def test_popup_position_update_timer_preserves_lifecycle_contract(popup_scene):
    window, items, warnings, _windows_before = popup_scene
    popup = items["popup"]
    tracker = _popup_trackers(popup)[0]
    timer = tracker.findChild(QObject, "popupPositionUpdateTimer")
    assert timer is not None
    assert timer.parent() is tracker
    assert timer.property("host") is tracker
    assert timer.property("interval") == 0
    assert timer.property("repeat") is False
    assert timer.property("running") is False

    assert QMetaObject.invokeMethod(window, "openPopup")
    assert _wait_for(lambda: popup.property("isOpen"))
    timer.stop()
    assert QMetaObject.invokeMethod(tracker, "scheduleUpdate")
    assert timer.property("running") is True
    assert _wait_for(lambda: not timer.property("running"))
    assert warnings == []


def test_popup_tracking_connections_only_exist_while_tracking(popup_scene):
    window, items, warnings, _windows_before = popup_scene
    popup = items["popup"]
    tip = items["tip"]

    popup_trackers = _popup_trackers(popup)
    tip_trackers = _popup_trackers(tip)
    assert len(popup_trackers) == 1
    assert len(tip_trackers) == 1
    assert _tracker_connections(popup_trackers[0]) == []
    assert _tracker_connections(tip_trackers[0]) == []

    assert QMetaObject.invokeMethod(window, "openPopup")
    assert _wait_for(lambda: len(_tracker_connections(popup_trackers[0])) == 2)
    assert QMetaObject.invokeMethod(popup, "close")
    assert _wait_for(lambda: _tracker_connections(popup_trackers[0]) == [])

    assert QMetaObject.invokeMethod(window, "showTip")
    assert _wait_for(lambda: len(_tracker_connections(tip_trackers[0])) == 2)
    assert QMetaObject.invokeMethod(tip, "close")
    assert _wait_for(lambda: _tracker_connections(tip_trackers[0]) == [])
    assert warnings == []


def test_menu_page_async_incubation_keeps_closed_popup_connections_inactive(qapp):
    engine, component, window, _loader, warnings = _create_async_menu_scene()
    try:
        trackers = _popup_trackers(window)
        assert trackers
        assert all(_tracker_connections(tracker) == [] for tracker in trackers)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
