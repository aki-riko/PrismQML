# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML 通知 Python helper

让 Python 端直接调 NotificationManager.desktop / .infoBar / .toast,不需要业务方
自己写 NotificationBridge.qml 胶水 + 靠 getattr 撞运气访问 QML function。

工作原理
========
QML 端 NotificationManager 是 singleton, 但 Python 端 PySide6 不能直接访问 QML
function (PyObject getattr 拿不到, QMetaObject.invokeMethod 也对 namespace QtObject
不友好)。 我们创建一个**临时的 inline QML helper Item**, 它持 NotificationManager
引用并暴露 Q_INVOKABLE / function, Python 用 invokeMethod 调它就好了。

helper 全局单例缓存, 第一次调用时按需 lazy load。

接入示例
========
    from prismqml.python.runtime.notification import (
        showDesktopWarning, showDesktopInfo, Position, Severity,
    )
    showDesktopWarning("标题", "消息内容")
    # 或者
    showDesktopWarning("标题", "消息内容", duration=3000, position=Position.TopRight)
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Mapping, Optional

from PySide6.QtCore import QObject, QUrl, Qt, QMetaObject, Q_ARG, Slot
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from ..core.logger import getLogger
from .engine import get_published_qml_engine

_logger = getLogger("notification")


class Position(IntEnum):
    """通知位置, 跟 PrismEnums.notification.posX 对齐"""
    TopLeft = 0
    Top = 1
    TopRight = 2
    Left = 3
    Center = 4
    Right = 5
    BottomLeft = 6
    Bottom = 7
    BottomRight = 8


class Severity:
    """通知 severity 字符串, 跟 NotificationManager 内部对齐"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ATTENTION = "attention"
    PROCESSING = "processing"


# 单例缓存的 helper QML 对象
_helper: Optional[QObject] = None


_HELPER_QML = """
import QtQuick
import PrismQML

QtObject {
    function desktopShow(severity, title, message, duration, position, options) {
        switch (severity) {
            case "info":      return NotificationManager.desktop.info(title, message, duration, position, options)
            case "success":   return NotificationManager.desktop.success(title, message, duration, position, options)
            case "warning":   return NotificationManager.desktop.warning(title, message, duration, position, options)
            case "error":     return NotificationManager.desktop.error(title, message, duration, position, options)
            default:          return NotificationManager.desktop.infoBar(severity, title, message, duration, position, options)
        }
    }
    function desktopInfoBar(severity, title, message, duration, position, options) {
        return NotificationManager.desktop.infoBar(severity, title, message, duration, position, options)
    }
    function closeAllDesktop() {
        NotificationManager.closeAllDesktopNotifications()
    }
}
"""


def _cached_helper_for(engine: QQmlApplicationEngine) -> Optional[QObject]:
    """Return a live helper owned by this engine. 返回当前引擎持有的存活 helper。"""
    global _helper
    if _helper is None:
        return None

    try:
        _ = _helper.objectName()
        helper_parent = _helper.parent()
    except RuntimeError:
        _logger.warning("helper QML 对象 C++ 端已销毁, 重新创建")
        _helper = None
        return None
    if helper_parent is engine:
        return _helper
    _helper = None
    _logger.warning("通知 helper 所属 Engine 已变化, 重新创建")
    return None


def _create_helper(engine: QQmlApplicationEngine) -> Optional[QObject]:
    """Create and publish one engine-owned helper. 创建并发布引擎持有的 helper。"""
    global _helper
    component = QQmlComponent(engine)
    component.setData(_HELPER_QML.encode("utf-8"), QUrl())
    if component.isError():
        _logger.error(f"Notification helper QML 编译失败: {component.errorString()}")
        return None

    # Attach the helper to the engine root context. 将 helper 挂到引擎根上下文。
    obj = component.create(engine.rootContext())
    if obj is None:
        _logger.error("Notification helper QML 实例化失败")
        return None
    # Keep both Python and C++ ownership. 同时保留 Python 与 C++ 所有权。
    obj.setParent(engine)

    _helper = obj
    return _helper


def _get_helper() -> Optional[QObject]:
    """Lazy-create the cached helper. 懒创建并缓存通知 helper。"""
    try:
        engine = get_published_qml_engine()
    except RuntimeError:
        _logger.warning("Engine 未初始化, 通知 helper 不可用")
        return None
    if engine is None:
        return None

    helper = _cached_helper_for(engine)
    if helper is not None:
        return helper
    return _create_helper(engine)


def _invoke(method_name: str, *args) -> bool:
    """通过 QMetaObject.invokeMethod 调 helper 的 QML function (变长参数)"""
    helper = _get_helper()
    if helper is None:
        return False
    qargs = [Q_ARG("QVariant", a) for a in args]
    ok = QMetaObject.invokeMethod(
        helper, method_name, Qt.DirectConnection, *qargs
    )
    if not ok:
        _logger.warning(f"invokeMethod {method_name} 返回 False")
    return ok


def showDesktopNotification(
    severity: str,
    title: str,
    message: str = "",
    duration: int = 5000,
    position: int = Position.BottomRight,
    options: Optional[Mapping[str, Any]] = None,
) -> bool:
    """通用桌面通知入口

    severity: 见 Severity 类常量
    duration: 毫秒, 默认 5000
    position: 见 Position 枚举, 默认 BottomRight
    options: 创建前应用的通知属性, 如 orient/closable/feature/progress
    返回是否成功 dispatch (不代表用户已看到)
    """
    return _invoke(
        "desktopShow",
        severity,
        title,
        message,
        int(duration),
        int(position),
        dict(options or {}),
    )


def showDesktopInfo(
    title: str,
    message: str = "",
    duration: int = 5000,
    position: int = Position.BottomRight,
    options: Optional[Mapping[str, Any]] = None,
) -> bool:
    return showDesktopNotification(
        Severity.INFO, title, message, duration, position, options
    )


def showDesktopSuccess(
    title: str,
    message: str = "",
    duration: int = 5000,
    position: int = Position.BottomRight,
    options: Optional[Mapping[str, Any]] = None,
) -> bool:
    return showDesktopNotification(
        Severity.SUCCESS, title, message, duration, position, options
    )


def showDesktopWarning(
    title: str,
    message: str = "",
    duration: int = 5000,
    position: int = Position.BottomRight,
    options: Optional[Mapping[str, Any]] = None,
) -> bool:
    return showDesktopNotification(
        Severity.WARNING, title, message, duration, position, options
    )


def showDesktopError(
    title: str,
    message: str = "",
    duration: int = 5000,
    position: int = Position.BottomRight,
    options: Optional[Mapping[str, Any]] = None,
) -> bool:
    return showDesktopNotification(
        Severity.ERROR, title, message, duration, position, options
    )


def showDesktopInfoBar(
    severity: str,
    title: str,
    message: str = "",
    duration: int = 5000,
    position: int = Position.TopRight,
    options: Optional[Mapping[str, Any]] = None,
) -> bool:
    """桌面级 InfoBar (横长条样式)"""
    return _invoke(
        "desktopInfoBar",
        severity,
        title,
        message,
        int(duration),
        int(position),
        dict(options or {}),
    )


def closeAllDesktopNotifications() -> bool:
    return _invoke("closeAllDesktop")
