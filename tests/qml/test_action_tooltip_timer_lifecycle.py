# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Action tooltip timer lifecycle regressions. Action 提示计时器生命周期回归。"""

from __future__ import annotations

import os
from pathlib import Path
from time import perf_counter

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "menus" / "Action.qml"
)
TOOLTIP_SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Tooltip"
    / "TooltipCore.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "action-tooltip-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 360
    height: 180
    visible: true
    color: Enums.backgroundColor

    Action {
        objectName: "action"
        x: 40
        y: 40
        width: 240
        text: "Action"
        icon: Enums.icon.info
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


def _timers(action: QQuickItem) -> list[QObject]:
    return [
        child
        for child in action.findChildren(QObject)
        if child.metaObject().className() == "QQmlTimer"
    ]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
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
    action = window.findChild(QQuickItem, "action")
    assert action is not None
    loader = window.findChild(QQuickItem, "actionTooltipLoader")
    assert loader is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, action, loader, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _flush_deferred(qapp) -> None:
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    _pump()


def test_action_tooltip_preserves_delay_and_timer_lifecycle(qapp):
    """Dynamic tooltips must keep hover delay while avoiding idle churn.

    动态提示必须保持悬停延迟，同时避免空闲对象常驻。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, action, loader, warnings = _create_scene()
    try:
        assert loader.property("item") is None
        initial_timers = _timers(action)
        initial_objects = len(action.findChildren(QObject))

        assert action.setProperty("toolTip", "Dynamic tooltip")
        assert _wait_for(lambda: loader.property("item") is not None)
        tooltip = loader.property("item")
        loaded_timers = _timers(action)
        loaded_objects = len(action.findChildren(QObject))

        started = perf_counter()
        QTest.mouseMove(
            window,
            QPoint(
                round(action.x() + action.width() / 2),
                round(action.y() + action.height() / 2),
            ),
        )
        assert _wait_for(lambda: bool(tooltip.property("_windowVisible")), 1_400)
        elapsed_ms = (perf_counter() - started) * 1_000
        assert elapsed_ms >= 500
        shown_timers = _timers(action)
        shown_objects = len(action.findChildren(QObject))

        QTest.mouseMove(window, QPoint(window.width() - 5, window.height() - 5))
        assert _wait_for(lambda: not bool(tooltip.property("_windowVisible")), 1_000)

        assert action.setProperty("toolTip", "")
        assert _wait_for(lambda: loader.property("item") is None)
        _flush_deferred(qapp)
        restored_timers = _timers(action)
        restored_objects = len(action.findChildren(QObject))

        print(
            "ACTION_TOOLTIP_TIMER",
            f"timers={len(initial_timers)}/{len(loaded_timers)}/"
            f"{len(shown_timers)}/"
            f"{len(restored_timers)}",
            f"objects={initial_objects}/{loaded_objects}/{shown_objects}/"
            f"{restored_objects}",
            f"show_ms={elapsed_ms:.1f}",
        )

        assert len(initial_timers) == 0
        assert len(loaded_timers) == 1
        assert len(shown_timers) == 2
        assert len(restored_timers) == 0
        assert restored_timers == initial_timers
        assert (initial_objects, loaded_objects, shown_objects, restored_objects) == (
            30,
            36,
            58,
            30,
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_action_source_loads_timer_with_tooltip():
    """The delay timer must share the tooltip lifecycle. 延迟计时器必须跟随提示生命周期。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "id: tipTimer" not in source
    assert "id: actionTooltip" in source
    assert 'running: control.toolTip !== "" && itemArea.containsMouse' in source
    assert "onTriggered: actionTooltip.show()" in source


def test_tooltip_source_loads_follow_timer_with_window_host():
    """The follow timer must share the native host lifecycle. 跟随计时器必须跟随原生宿主生命周期。"""
    source = TOOLTIP_SOURCE_PATH.read_text(encoding="utf-8")
    assert "running: control.followAnchor && control._windowVisible" not in source
    assert "running: control.followAnchor && windowHost.windowVisible" in source
