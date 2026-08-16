# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window-outside notification lifecycle contracts. 窗口外通知生命周期合同。"""

from __future__ import annotations

from pathlib import Path
import time

import pytest
from PySide6.QtCore import QObject, QRect, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QSignalSpy, QTest
from shiboken6 import isValid

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "window-outside-notification.qml")
)
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host

    property var notification: null
    property var secondNotification: null

    function createToast(requestedPosition) {
        notification = NotificationManager.toast.info(
            host, "提示", "窗口外 Toast", 0, requestedPosition,
            Enums.notification.mode_window_outside
        )
    }

    function createInfoBar(requestedPosition) {
        notification = NotificationManager.infoBar.info(
            host, "提示", "窗口外 InfoBar", 0, requestedPosition,
            Enums.notification.mode_window_outside
        )
    }

    function createStacked(requestedPosition) {
        notification = NotificationManager.toast.info(
            host, "第一条", "窗口外堆叠", 0, requestedPosition,
            Enums.notification.mode_window_outside
        )
        secondNotification = NotificationManager.toast.info(
            host, "第二条", "窗口外堆叠", 0, requestedPosition,
            Enums.notification.mode_window_outside
        )
    }

    function closeOutside() {
        NotificationManager.closeAllWindowOutsideNotifications(host)
    }

    width: 640
    height: 480
    x: 180
    y: 160
    visible: false
}
""".encode("utf-8")


class _FakeWindowHelper(QObject):
    """Deterministic attachment provider for QML lifecycle tests."""

    windowFollowerReservationsChanged = Signal()

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.reserved_extent = 0
        self.register_calls = []
        self.unregister_calls = []

    @staticmethod
    def _host_rect(host_window):
        rect = host_window.frameGeometry()
        return rect.left(), rect.top(), rect.right() + 1, rect.bottom() + 1

    @Slot("QVariant", int, float, float, float, float, result="QVariantMap")
    def windowAttachmentGeometry(
        self, host_window, position, width, height, gap, stack_offset
    ):
        left, top, right, bottom = self._host_rect(host_window)
        host_width = right - left
        host_height = bottom - top
        outward = self.reserved_extent + round(gap)
        width = round(width)
        height = round(height)
        if position in (0, 3, 6):
            x = left - outward - width
        elif position in (2, 5, 8):
            x = right + outward
        else:
            x = left + (host_width - width) // 2
        if position == 1:
            y = top - outward - height - round(stack_offset)
        elif position == 7:
            y = bottom + outward + round(stack_offset)
        elif position in (0, 2):
            y = top + round(stack_offset)
        elif position in (6, 8):
            y = bottom - height - round(stack_offset)
        else:
            y = top + (host_height - height) // 2 + round(stack_offset)
        return {"x": x, "y": y, "width": width, "height": height}

    @Slot("QVariant", "QVariant", int, float, float, float, float, result=bool)
    def registerWindowAttachment(
        self, host_window, attached_window, position, width, height, gap, stack_offset
    ):
        geometry = self.windowAttachmentGeometry(
            host_window, position, width, height, gap, stack_offset
        )
        attached_window.setGeometry(
            QRect(geometry["x"], geometry["y"], geometry["width"], geometry["height"])
        )
        self.register_calls.append((host_window, attached_window, geometry))
        return True

    @Slot("QVariant", result=bool)
    def unregisterWindowAttachment(self, attached_window):
        self.unregister_calls.append(attached_window)
        return True


def _wait_until(predicate, timeout_ms: int = 1800) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        QGuiApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    assert predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    helper = _FakeWindowHelper(engine)
    engine.rootContext().setContextProperty("WindowHelper", helper)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    _wait_until(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root, helper


def _dispose(engine, component, root):
    root.closeOutside()
    QTest.qWait(350)
    root.close()
    root.deleteLater()
    del component
    engine.deleteLater()
    QGuiApplication.processEvents()


@pytest.mark.parametrize("kind", ["toast", "infoBar"])
@pytest.mark.parametrize("position", [0, 1, 2, 6, 7, 8])
def test_window_outside_notification_tracks_host_and_drawer_reservation(
    qapp, kind, position
):
    engine, component, root, helper = _create_scene()
    try:
        root.show()
        getattr(root, f"create{kind[0].upper()}{kind[1:]}")(position)
        notification = root.property("notification")
        assert notification is not None
        overlay = notification.window()
        assert isinstance(overlay, QQuickWindow)
        closed_spy = QSignalSpy(overlay.closed)
        _wait_until(overlay.isVisible)
        QTest.qWait(350)

        assert overlay.property("hostWindow") == root
        assert overlay.property("position") == position
        assert overlay.property("_attached") is True
        assert helper.register_calls
        first_geometry = helper.register_calls[-1][2]

        root.setX(root.x() + 47)
        _wait_until(lambda: len(helper.register_calls) >= 2)
        moved_geometry = helper.register_calls[-1][2]
        assert moved_geometry["x"] == first_geometry["x"] + 47

        helper.reserved_extent = 120
        helper.windowFollowerReservationsChanged.emit()
        axis = "x" if position in (0, 2, 6, 8) else "y"
        _wait_until(lambda: helper.register_calls[-1][2][axis] != moved_geometry[axis])
        if position in (0, 6):
            assert helper.register_calls[-1][2]["x"] == moved_geometry["x"] - 120
        elif position in (2, 8):
            assert helper.register_calls[-1][2]["x"] == moved_geometry["x"] + 120
        elif position == 1:
            assert helper.register_calls[-1][2]["y"] == moved_geometry["y"] - 120
        elif position == 7:
            assert helper.register_calls[-1][2]["y"] == moved_geometry["y"] + 120

        root.closeOutside()
        _wait_until(lambda: closed_spy.count() == 1)
        QTest.qWait(40)
        assert len(helper.unregister_calls) == 1
        assert not isValid(overlay)
    finally:
        _dispose(engine, component, root)


@pytest.mark.parametrize("position, axis, direction", [(0, "y", 1), (1, "y", -1), (7, "y", 1), (2, "y", 1)])
def test_window_outside_stack_is_scoped_to_host_and_position(qapp, position, axis, direction):
    engine, component, root, helper = _create_scene()
    try:
        root.show()
        root.createStacked(position)
        first = root.property("notification")
        second = root.property("secondNotification")
        first_overlay = first.window()
        second_overlay = second.window()
        _wait_until(lambda: first_overlay.isVisible() and second_overlay.isVisible())
        QTest.qWait(350)

        assert second_overlay.property("stackOffset") > 0
        first_coordinate = first_overlay.y() if axis == "y" else first_overlay.x()
        second_coordinate = second_overlay.y() if axis == "y" else second_overlay.x()
        assert (second_coordinate - first_coordinate) * direction > 0
        assert len({call[1] for call in helper.register_calls}) >= 2
    finally:
        _dispose(engine, component, root)
