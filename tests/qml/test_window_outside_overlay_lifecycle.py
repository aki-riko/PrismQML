# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window-outside notification lifecycle contracts. 窗口外通知生命周期合同。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
OVERLAY_SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Notification"
    / "_internal"
    / "WindowOutsideOverlay.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(OVERLAY_SOURCE_PATH.parent / "window-outside-overlay-lifecycle-test.qml")
)
HOST_SOURCE = b"""
import QtQuick
import QtQuick.Window

Window {
    objectName: "windowOutsideLifecycleHost"
    x: 120
    y: 160
    width: 480
    height: 320
    visible: true
}
"""


class _AttachmentHelper(QObject):
    """Deterministic QML attachment service for lifecycle assertions."""

    windowFollowerReservationsChanged = Signal()

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.registrations: list[dict[str, float | int | str]] = []
        self.geometry_calls: list[dict[str, float | int]] = []
        self.unregistrations: list[str] = []

    @staticmethod
    def _window_rect(window: QObject) -> tuple[int, int, int, int]:
        geometry = window.frameGeometry()
        return geometry.x(), geometry.y(), geometry.width(), geometry.height()

    @staticmethod
    def _geometry(
        host_window: QObject,
        position: int,
        width: float,
        height: float,
        gap: float,
        stack_offset: float,
    ) -> dict[str, int]:
        host_x, host_y, host_width, host_height = _AttachmentHelper._window_rect(
            host_window
        )
        target_width = max(1, round(width))
        target_height = max(1, round(height))
        edge_gap = max(0, round(gap))
        offset = max(0, round(stack_offset))
        if position in (0, 3, 6):
            left = host_x - edge_gap - target_width
        elif position in (2, 5, 8):
            left = host_x + host_width + edge_gap
        else:
            left = host_x + (host_width - target_width) // 2

        if position == 1:
            top = host_y - edge_gap - target_height - offset
        elif position == 7:
            top = host_y + host_height + edge_gap + offset
        elif position in (0, 2):
            top = host_y + offset
        elif position in (6, 8):
            top = host_y + host_height - target_height - offset
        else:
            top = host_y + (host_height - target_height) // 2 + offset
        return {
            "x": left,
            "y": top,
            "width": target_width,
            "height": target_height,
        }

    @Slot("QVariant", "QVariant", int, float, float, float, float, result=bool)
    def registerWindowAttachment(
        self,
        host_window: QObject,
        attached_window: QObject,
        position: int,
        width: float,
        height: float,
        gap: float,
        stack_offset: float,
    ) -> bool:
        self.registrations.append(
            {
                "attached": attached_window.objectName(),
                "position": position,
                "width": width,
                "height": height,
                "gap": gap,
                "stack_offset": stack_offset,
            }
        )
        return True

    @Slot("QVariant", int, float, float, float, float, result="QVariantMap")
    def windowAttachmentGeometry(
        self,
        host_window: QObject,
        position: int,
        width: float,
        height: float,
        gap: float,
        stack_offset: float,
    ) -> dict[str, int]:
        geometry = self._geometry(
            host_window, position, width, height, gap, stack_offset
        )
        self.geometry_calls.append(dict(geometry))
        return geometry

    @Slot("QVariant", result=bool)
    def unregisterWindowAttachment(self, attached_window: QObject) -> bool:
        self.unregistrations.append(attached_window.objectName())
        return True


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


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene(
    position: int = 5, show_duration: int = 0, hide_duration: int = 0
):
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    helper = _AttachmentHelper(engine)
    engine.rootContext().setContextProperty("WindowHelper", helper)

    host_component = QQmlComponent(engine)
    host_component.setData(HOST_SOURCE, QUrl.fromLocalFile(str(ROOT / "host.qml")))
    assert host_component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in host_component.errors()
    ]
    host = host_component.create(engine.rootContext())
    assert isinstance(host, QQuickWindow), [
        error.toString() for error in host_component.errors()
    ]

    overlay_component = QQmlComponent(engine, QUrl.fromLocalFile(str(OVERLAY_SOURCE_PATH)))
    assert _wait_for(lambda: overlay_component.status() != QQmlComponent.Status.Loading)
    assert overlay_component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in overlay_component.errors()
    ]
    overlay = overlay_component.createWithInitialProperties(
        {"hostWindow": host, "position": position}, engine.rootContext()
    )
    assert isinstance(overlay, QQuickWindow), [
        error.toString() for error in overlay_component.errors()
    ]
    animator = next(
        (
            child
            for child in overlay.findChildren(QObject)
            if child.metaObject().indexOfProperty("showDuration") >= 0
            and child.metaObject().indexOfProperty("hideDuration") >= 0
        ),
        None,
    )
    assert animator is not None
    animator.setProperty("showDuration", show_duration)
    animator.setProperty("hideDuration", hide_duration)
    content = overlay.property("content")
    assert isinstance(content, QQuickItem)
    notification = QQuickItem(content)
    notification.setObjectName("windowOutsideNotificationItem")
    notification.setImplicitWidth(220)
    notification.setImplicitHeight(72)
    overlay.setProperty("notificationItem", notification)
    assert _wait_for(lambda: bool(overlay.property("width")))
    return (
        engine,
        host_component,
        overlay_component,
        host,
        overlay,
        notification,
        helper,
        warnings,
    )


def _dispose_scene(engine, host_component, overlay_component, host, overlay) -> None:
    if shiboken6.isValid(overlay):
        overlay.setVisible(False)
        overlay.deleteLater()
    if shiboken6.isValid(host):
        host.setVisible(False)
        host.deleteLater()
    host_component.deleteLater()
    overlay_component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.mark.parametrize(
    ("position", "axis", "host_direction"),
    [
        (3, "x", 1),
        (5, "x", -1),
        (1, "y", 1),
        (7, "y", -1),
    ],
)
def test_window_outside_overlay_enters_from_host_side(
    position, axis, host_direction, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene(
        position=position, show_duration=120, hide_duration=120
    )
    (
        engine,
        host_component,
        overlay_component,
        host,
        overlay,
        _notification,
        helper,
        warnings,
    ) = scene
    try:
        assert QMetaObject.invokeMethod(overlay, "show")
        assert overlay.isVisible()
        assert helper.geometry_calls

        final_geometry = helper.geometry_calls[-1]
        start_coordinate = overlay.x() if axis == "x" else overlay.y()
        final_coordinate = final_geometry[axis]
        assert (start_coordinate - final_coordinate) * host_direction > 0

        assert _wait_for(
            lambda: (overlay.x(), overlay.y())
            == (final_geometry["x"], final_geometry["y"])
        )
        assert QMetaObject.invokeMethod(overlay, "hide")
        assert _wait_for(lambda: not overlay.isVisible())

        hide_coordinate = overlay.x() if axis == "x" else overlay.y()
        assert (hide_coordinate - final_coordinate) * host_direction < 0
    finally:
        _dispose_scene(engine, host_component, overlay_component, host, overlay)

    assert warnings == []
    assert _new_visible_windows(windows_before) == []


def test_window_outside_overlay_registers_repositions_and_releases_once(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, host_component, overlay_component, host, overlay, notification, helper, warnings = scene
    try:
        assert not overlay.isVisible()
        assert helper.registrations == []
        assert overlay.property("transientParent") is None

        closed = []
        overlay.closed.connect(lambda: closed.append(True))
        assert QMetaObject.invokeMethod(overlay, "show")
        assert _wait_for(overlay.isVisible)
        assert helper.registrations
        assert helper.registrations[-1]["position"] == 5
        assert helper.registrations[-1]["width"] == overlay.width()
        assert helper.registrations[-1]["height"] == overlay.height()
        assert _wait_for(lambda: bool(helper.geometry_calls))
        assert (overlay.x(), overlay.y()) == (
            helper.geometry_calls[-1]["x"],
            helper.geometry_calls[-1]["y"],
        )

        registration_count = len(helper.registrations)
        host.setX(host.x() + 40)
        assert _wait_for(lambda: len(helper.registrations) > registration_count)
        assert _wait_for(
            lambda: overlay.x() == helper.geometry_calls[-1]["x"]
            and overlay.y() == helper.geometry_calls[-1]["y"]
        )

        notification.setImplicitWidth(notification.implicitWidth() + 40)
        assert _wait_for(
            lambda: helper.registrations[-1]["width"] == overlay.width()
        )
        overlay.setProperty("stackOffset", 30)
        assert _wait_for(lambda: helper.registrations[-1]["stack_offset"] == 30)
        helper.windowFollowerReservationsChanged.emit()
        assert _wait_for(lambda: len(helper.registrations) > registration_count + 2)

        assert QMetaObject.invokeMethod(overlay, "hide")
        assert _wait_for(lambda: not overlay.isVisible())
        assert closed == [True]
        assert helper.unregistrations == ["windowOutsideNotificationOverlay"]
    finally:
        _dispose_scene(engine, host_component, overlay_component, host, overlay)

    assert warnings == []
    assert _new_visible_windows(windows_before) == []


@pytest.mark.parametrize("close_path", ["host_hidden", "host_minimized"])
def test_window_outside_overlay_host_lifecycle_releases_attachment(close_path, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, host_component, overlay_component, host, overlay, _notification, helper, warnings = scene
    try:
        assert QMetaObject.invokeMethod(overlay, "show")
        assert _wait_for(overlay.isVisible)
        if close_path == "host_hidden":
            host.setVisible(False)
        else:
            host.setVisibility(QWindow.Visibility.Minimized)
        assert _wait_for(lambda: not overlay.isVisible())
        assert helper.unregistrations == ["windowOutsideNotificationOverlay"]
    finally:
        _dispose_scene(engine, host_component, overlay_component, host, overlay)

    assert warnings == []
    assert _new_visible_windows(windows_before) == []
