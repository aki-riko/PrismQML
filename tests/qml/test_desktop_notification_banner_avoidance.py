# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Desktop notification banner avoidance regressions. 桌面通知横幅避让回归。

真实系统通知横幅无法在测试进程里移动位置，因此这里注入一个确定性假守卫，
分别验证底部与顶部锚定的桌面通知会按保留高度向屏幕内侧让位，并在保留量
归零后精确回位。期望值全部取自 Enums，与实现同源。
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]

# Measured banner window height on the reference display. 参考显示器上实测的横幅窗口高度。
BANNER_WINDOW_HEIGHT = 228

POSITION_BOTTOM_RIGHT = 8
POSITION_TOP_RIGHT = 2

SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host
    width: 400
    height: 300
    visible: false

    readonly property int bannerWindowInset: Enums.notification.layout.bannerWindowInset
    readonly property int bannerGap: Enums.notification.layout.bannerGap
    readonly property real devicePixelRatio: screen ? screen.devicePixelRatio : 1

    property var notification: null
    property var standalone: null

    function createAt(position) {
        notification = NotificationManager.desktop.success("标题", "消息", 0, position)
        return notification !== null
    }

    function createStandalone(position) {
        standalone = standaloneComponent.createObject(null, {
            "position": position,
            "duration": 0
        })
        if (!standalone) return false
        standalone.show()
        return true
    }

    function closeAll() {
        NotificationManager.closeAllDesktopNotifications()
        if (standalone) {
            standalone.hide()
            standalone.destroy()
            standalone = null
        }
    }

    Component {
        id: standaloneComponent
        DesktopNotification {}
    }
}
"""


class _FakeBannerGuard(QObject):
    """Deterministic stand-in for the injected guard. 注入守卫的确定性替身。"""

    reservationsChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._top = 0
        self._bottom = 0
        self._watchers = 0

    @Property(int, notify=reservationsChanged)
    def topReservedHeight(self) -> int:
        return self._top

    @Property(int, notify=reservationsChanged)
    def bottomReservedHeight(self) -> int:
        return self._bottom

    @Property(int, notify=reservationsChanged)
    def watcherCount(self) -> int:
        return self._watchers

    @Slot()
    def acquire(self) -> None:
        self._watchers += 1

    @Slot()
    def release(self) -> None:
        self._watchers = max(0, self._watchers - 1)

    def set_reservations(self, top: int, bottom: int) -> None:
        """Publish new reservations. 发布新的保留高度。"""
        self._top = top
        self._bottom = bottom
        self.reservationsChanged.emit()


def _wait_until(predicate, timeout_ms: int = 4000) -> bool:
    """Wait for one predicate. 等待一个谓词成立。"""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        if predicate():
            return True
        QTest.qWait(10)
    return bool(predicate())


def _create_scene(guard):
    """Build the host scene with one injected guard. 用注入的守卫构建宿主场景。"""
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    engine.rootContext().setContextProperty("NotificationBannerGuard", guard)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), QUrl.fromLocalFile(str(ROOT)))
    _wait_until(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root


def _overlay(host):
    """Return the visible desktop notification overlay window. 返回可见的桌面通知覆盖层窗口。"""
    for window in QGuiApplication.allWindows():
        if window is host or not window.isVisible():
            continue
        if window.width() > 0 and window.height() > 0:
            return window
    return None


def _expected_inset(root) -> float:
    """Compute the expected avoidance in logical pixels. 计算期望的逻辑像素避让量。"""
    ratio = float(root.property("devicePixelRatio") or 1)
    if ratio <= 0:
        ratio = 1.0
    inset = float(root.property("bannerWindowInset"))
    gap = float(root.property("bannerGap"))
    return BANNER_WINDOW_HEIGHT / ratio - inset + gap


def _dispose(engine, component, root) -> None:
    """Tear the scene down. 拆除场景。"""
    root.closeAll()
    QTest.qWait(60)
    root.deleteLater()
    del component
    engine.deleteLater()
    QGuiApplication.processEvents()


@pytest.mark.parametrize(
    "position, sign",
    ((POSITION_BOTTOM_RIGHT, -1), (POSITION_TOP_RIGHT, 1)),
)
def test_desktop_notification_avoids_banner_on_its_edge(qapp, position, sign):
    """Bottom-anchored notifications lift, top-anchored ones drop. 底部锚定上抬，顶部锚定下移。"""
    guard = _FakeBannerGuard()
    engine, component, root = _create_scene(guard)
    try:
        assert root.createAt(position)
        assert _wait_until(lambda: _overlay(root) is not None)
        QTest.qWait(500)
        baseline = _overlay(root).y()

        if sign < 0:
            guard.set_reservations(0, BANNER_WINDOW_HEIGHT)
        else:
            guard.set_reservations(BANNER_WINDOW_HEIGHT, 0)
        QTest.qWait(700)
        moved = _overlay(root).y()

        expected = _expected_inset(root)
        assert (moved - baseline) * sign == pytest.approx(expected, abs=2), (
            "baseline=%s moved=%s expected=%s" % (baseline, moved, expected)
        )

        guard.set_reservations(0, 0)
        QTest.qWait(700)
        assert _overlay(root).y() == baseline
    finally:
        _dispose(engine, component, root)


def test_banner_reservation_of_other_edge_does_not_move_notification(qapp):
    """A banner on the opposite edge must not move the notification. 对侧边缘的横幅不得移动通知。"""
    guard = _FakeBannerGuard()
    engine, component, root = _create_scene(guard)
    try:
        assert root.createAt(POSITION_BOTTOM_RIGHT)
        assert _wait_until(lambda: _overlay(root) is not None)
        QTest.qWait(500)
        baseline = _overlay(root).y()

        guard.set_reservations(BANNER_WINDOW_HEIGHT, 0)
        QTest.qWait(700)
        assert _overlay(root).y() == baseline
    finally:
        _dispose(engine, component, root)


def test_standalone_desktop_notification_avoids_banner(qapp):
    """Standalone DesktopNotification must reserve banner space too.

    独立桌面通知组件（DesktopNotification）也必须避让系统横幅。
    """
    guard = _FakeBannerGuard()
    engine, component, root = _create_scene(guard)
    try:
        assert root.createStandalone(POSITION_BOTTOM_RIGHT)
        assert _wait_until(lambda: _overlay(root) is not None), [
            (window.title(), window.isVisible(), window.width(), window.height())
            for window in QGuiApplication.allWindows()
        ]
        QTest.qWait(500)
        baseline = _overlay(root).y()

        guard.set_reservations(0, BANNER_WINDOW_HEIGHT)
        QTest.qWait(700)
        lifted = _overlay(root).y()

        expected = _expected_inset(root)
        assert baseline - lifted == pytest.approx(expected, abs=2), (
            "baseline=%s lifted=%s expected=%s" % (baseline, lifted, expected)
        )

        guard.set_reservations(0, 0)
        QTest.qWait(700)
        assert _overlay(root).y() == baseline
    finally:
        _dispose(engine, component, root)
