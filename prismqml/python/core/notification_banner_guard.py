# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Notification banner guard exposed to QML. 暴露给 QML 的通知横幅避让守卫。

QML 读取 reservedHeight（物理像素），除以所在屏幕的 devicePixelRatio 即得
逻辑像素避让量。轮询只在至少一个桌面通知在屏幕上时才运行。
"""

from __future__ import annotations

import ctypes
from typing import Optional

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from ._notification_banner import notification_banner_reservation
from .logger import debug, exception

# Poll interval while desktop notifications are on screen. 桌面通知在场时的轮询间隔。
_POLL_INTERVAL_MS = 250


class NotificationBannerGuard(QObject):
    """Track the height reserved by Windows notification banners. 跟踪系统通知横幅占用高度。

    QML 用法 In QML:
        NotificationBannerGuard.reservedHeight / screen.devicePixelRatio
    """

    _instance: Optional["NotificationBannerGuard"] = None

    reservedHeightChanged = Signal()

    def __new__(cls, parent: Optional[QObject] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None):
        if self._initialized:
            return
        super().__init__(parent)
        self._reserved_height = 0
        self._watchers = 0
        self._timer = QTimer(self)
        self._timer.setInterval(_POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._refresh)
        self._initialized = True

    @Property(int, notify=reservedHeightChanged)
    def reservedHeight(self) -> int:
        """Physical pixel height reserved by system notification banners. 系统通知横幅占用的物理像素高度。"""
        return self._reserved_height

    @Property(int, notify=reservedHeightChanged)
    def watcherCount(self) -> int:
        """Number of desktop notifications holding a watch. 持有监视的桌面通知数量。"""
        return self._watchers

    @Slot()
    def acquire(self) -> None:
        """Start watching; each desktop notification holds one reference. 开始监视，每个桌面通知持有一个引用。"""
        self._watchers += 1
        if self._watchers == 1:
            self._refresh()
            self._timer.start()

    @Slot()
    def release(self) -> None:
        """Release one reference. 释放一个引用。"""
        if self._watchers > 0:
            self._watchers -= 1
        if self._watchers == 0:
            self._timer.stop()
            self._publish(0)

    @Slot()
    def refresh(self) -> None:
        """Re-read the reservation immediately. 立即重新读取保留高度。"""
        self._refresh()

    def _refresh(self) -> None:
        """Read and publish the current reservation. 读取并发布当前保留高度。"""
        try:
            reserved = notification_banner_reservation()
        except (OSError, ctypes.ArgumentError) as exc:
            debug(f"通知横幅保留高度读取失败: {exc}")
            return
        except Exception as exc:
            exception(f"通知横幅保留高度未知错误: {type(exc).__name__}: {exc}")
            return
        self._publish(reserved)

    def _publish(self, reserved: int) -> None:
        """Publish one reservation value when it changed. 仅在变化时发布保留高度。"""
        if reserved == self._reserved_height:
            return
        self._reserved_height = reserved
        self.reservedHeightChanged.emit()


def get_notification_banner_guard() -> NotificationBannerGuard:
    """Return the notification banner guard singleton. 获取通知横幅守卫单例。"""
    return NotificationBannerGuard()
