# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Widget tooltip timer lifecycle regressions. Widget 工具提示计时器生命周期回归。"""

from __future__ import annotations

import hashlib
import os
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


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "_internal"
    / "WidgetToolTipPopup.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "widget-tooltip-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 420
    height: 240
    visible: true
    color: Enums.backgroundColor

    Widget {
        id: widget
        objectName: "widget"
        x: 130
        y: 100
        width: 160
        height: 48
        backgroundColor: Enums.cardColor
        backgroundRadius: Enums.radius.large
        toolTipText: "Timer lifecycle"
        toolTipShowDelay: 120
        toolTipHideDelay: 200
        toolTipDuration: 1000
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


def _timers(root: QObject) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if child.metaObject().className() == "QQmlTimer"
    ]


def _running_timers(root: QObject) -> list[QObject]:
    return [timer for timer in _timers(root) if timer.property("running")]


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
    raise AssertionError("Widget tooltip pixels did not stabilize")


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
    widget = window.findChild(QQuickItem, "widget")
    assert widget is not None
    assert _wait_for(window.isExposed)
    assert _wait_for(lambda: widget.findChild(QObject, "_hoverArea") is not None)
    return engine, component, window, widget, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_widget_tooltip_timer_and_native_window_lifecycle(qapp):
    """Show, hide, and auto-hide timers keep independent lifecycle contracts.

    显示、隐藏与自动隐藏计时器必须保持独立生命周期合同。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, widget, warnings = _create_scene()
    try:
        initial_hash = _stable_hash(window)
        assert widget.findChild(QObject, "_toolTip") is None

        assert QMetaObject.invokeMethod(widget, "_startToolTipShowTimer")
        assert _wait_for(
            lambda: widget.findChild(QObject, "_toolTip") is not None
        )
        tooltip = widget.findChild(QObject, "_toolTip")
        assert tooltip is not None
        scheduled_timer_count = len(_timers(tooltip))
        scheduled_object_count = len(tooltip.findChildren(QObject))
        assert len(_running_timers(tooltip)) == 1

        assert _wait_for(lambda: tooltip.property("visible") is True)
        assert _wait_for(
            lambda: len(_new_visible_windows(windows_before, window)) == 1
        )
        popup_window = _new_visible_windows(windows_before, window)[0]
        assert isinstance(popup_window, QQuickWindow)
        visible_timer_count = len(_timers(tooltip))
        visible_object_count = len(tooltip.findChildren(QObject))
        assert len(_running_timers(tooltip)) == 1
        tooltip_hash = _stable_hash(popup_window)

        assert QMetaObject.invokeMethod(tooltip, "startHideTimer")
        closing_timer_count = len(_timers(tooltip))
        assert len(_running_timers(tooltip)) == 2
        assert _wait_for(lambda: tooltip.property("visible") is False)
        assert _wait_for(
            lambda: _new_visible_windows(windows_before, window) == []
        )
        hidden_timer_count = len(_timers(tooltip))
        hidden_object_count = len(tooltip.findChildren(QObject))
        assert len(_running_timers(tooltip)) == 1

        assert QMetaObject.invokeMethod(tooltip, "cancelTimers")
        settled_timer_count = len(_timers(tooltip))
        settled_object_count = len(tooltip.findChildren(QObject))
        assert _running_timers(tooltip) == []
        restored_hash = _stable_hash(window)

        print(
            "WIDGET_TOOLTIP_TIMER",
            f"timers={scheduled_timer_count}/{visible_timer_count}/"
            f"{closing_timer_count}/{hidden_timer_count}/{settled_timer_count}",
            f"objects={scheduled_object_count}/{visible_object_count}/"
            f"{hidden_object_count}/{settled_object_count}",
            f"hashes={initial_hash}/{tooltip_hash}/{restored_hash}",
        )

        assert (
            scheduled_timer_count,
            visible_timer_count,
            closing_timer_count,
            hidden_timer_count,
            settled_timer_count,
        ) == (3, 3, 3, 3, 3)
        assert (
            scheduled_object_count,
            visible_object_count,
            hidden_object_count,
            settled_object_count,
        ) == (14, 17, 20, 20)
        assert (initial_hash, tooltip_hash, restored_hash) == (
            "3bfa5ae50834d18c64f7389dc7a5e29640b1a026a35a2ee1c3ae12590dac6ff7",
            "0b0059793c978ab0cbcd6ead78a0e597d601b8b768dbc43dd779377927fcac0f",
            "3bfa5ae50834d18c64f7389dc7a5e29640b1a026a35a2ee1c3ae12590dac6ff7",
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_widget_tooltip_source_keeps_three_independent_timers():
    """Baseline keeps the three timer roles separate. 基线保持三个计时器角色独立。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("Timer {") == 3
    assert "id: _showTimer" in source
    assert "id: _hideTimer" in source
    assert "id: _autoHideTimer" in source
    assert "_showTimer.restart()" in source
    assert "_hideTimer.start()" in source
    assert "_autoHideTimer.start()" in source
