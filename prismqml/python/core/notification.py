# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.

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
    from prismqml.python.core.notification import (
        showDesktopWarning, showDesktopInfo, Position, Severity,
    )
    showDesktopWarning("标题", "消息内容")
    # 或者
    showDesktopWarning("标题", "消息内容", duration=3000, position=Position.TopRight)
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional

from PySide6.QtCore import QObject, QUrl, Qt, QMetaObject, Q_ARG, Slot
from PySide6.QtQml import QQmlComponent

from .engine import EngineManager
from .logger import getLogger

_logger = getLogger("notification")


class Position(IntEnum):
    """通知位置, 跟 FluentEnums.notification.posX 对齐"""
    TopLeft = 0
    Top = 1
    TopRight = 2
    BottomLeft = 3
    Bottom = 4
    BottomRight = 5


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
    function desktopShow(severity, title, message, duration, position) {
        switch (severity) {
            case "info":      return NotificationManager.desktop.info(title, message, duration, position)
            case "success":   return NotificationManager.desktop.success(title, message, duration, position)
            case "warning":   return NotificationManager.desktop.warning(title, message, duration, position)
            case "error":     return NotificationManager.desktop.error(title, message, duration, position)
            default:          return NotificationManager.desktop.infoBar(severity, title, message, duration, position)
        }
    }
    function desktopInfoBar(severity, title, message, duration, position) {
        return NotificationManager.desktop.infoBar(severity, title, message, duration, position)
    }
    function closeAllDesktop() {
        NotificationManager.closeAllDesktopNotifications()
    }
}
"""


def _get_helper() -> Optional[QObject]:
    """lazy 创建 helper QML 对象, 单例缓存"""
    global _helper
    if _helper is not None:
        # 防御 _helper 的 C++ 端被 GC 销毁 (Python 持引用 ≠ C++ 存活)
        try:
            _ = _helper.objectName()
        except RuntimeError:
            _logger.warning("helper QML 对象 C++ 端已销毁, 重新创建")
            _helper = None
        else:
            return _helper

    try:
        engine = EngineManager.get_engine()
    except RuntimeError:
        _logger.warning("Engine 未初始化, 通知 helper 不可用")
        return None
    if engine is None:
        return None

    component = QQmlComponent(engine)
    component.setData(_HELPER_QML.encode("utf-8"), QUrl())
    if component.isError():
        _logger.error(f"Notification helper QML 编译失败: {component.errorString()}")
        return None

    # 关键: create(context) 让 helper 挂在 engine 的 root context 上,
    # 避免 component.create() 不持有 ownership 导致 QObject 立刻被 GC
    # Python 端 _helper 变量保 Python ref, parent=engine 保 C++ ref, 双保险。
    obj = component.create(engine.rootContext())
    if obj is None:
        _logger.error("Notification helper QML 实例化失败")
        return None
    obj.setParent(engine)  # 显式 parent → engine 生命周期内不会被销毁

    _helper = obj
    return _helper


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
) -> bool:
    """通用桌面通知入口

    severity: 见 Severity 类常量
    duration: 毫秒, 默认 5000
    position: 见 Position 枚举, 默认 BottomRight
    返回是否成功 dispatch (不代表用户已看到)
    """
    return _invoke("desktopShow", severity, title, message, int(duration), int(position))


def showDesktopInfo(title: str, message: str = "", duration: int = 5000, position: int = Position.BottomRight) -> bool:
    return showDesktopNotification(Severity.INFO, title, message, duration, position)


def showDesktopSuccess(title: str, message: str = "", duration: int = 5000, position: int = Position.BottomRight) -> bool:
    return showDesktopNotification(Severity.SUCCESS, title, message, duration, position)


def showDesktopWarning(title: str, message: str = "", duration: int = 5000, position: int = Position.BottomRight) -> bool:
    return showDesktopNotification(Severity.WARNING, title, message, duration, position)


def showDesktopError(title: str, message: str = "", duration: int = 5000, position: int = Position.BottomRight) -> bool:
    return showDesktopNotification(Severity.ERROR, title, message, duration, position)


def showDesktopInfoBar(severity: str, title: str, message: str = "", duration: int = 5000, position: int = Position.TopRight) -> bool:
    """桌面级 InfoBar (横长条样式)"""
    return _invoke("desktopInfoBar", severity, title, message, int(duration), int(position))


def closeAllDesktopNotifications() -> bool:
    return _invoke("closeAllDesktop")
