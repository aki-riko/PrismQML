# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""
跨平台窗口阴影管理器

支持平台：
- Windows: DWM原生阴影
- macOS: NSWindow.hasShadow
- Linux/其他: QML MultiEffect兜底
"""

import sys
import ctypes
from enum import Enum
from typing import Optional
from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    Slot,
    QAbstractNativeEventFilter,
    QByteArray,
)
from PySide6.QtGui import QWindow
from PySide6.QtWidgets import QApplication

from .logger import info, warning, error, exception


# Windows MARGINS 结构体（DWM阴影 API 需要）
if sys.platform == "win32":
    class MARGINS(ctypes.Structure):
        """DWM MARGINS 结构体"""
        _fields_ = [
            ("cxLeftWidth", ctypes.c_int),
            ("cxRightWidth", ctypes.c_int),
            ("cyTopHeight", ctypes.c_int),
            ("cyBottomHeight", ctypes.c_int),
        ]


class ShadowMode(Enum):
    """阴影模式"""

    NATIVE = "native"  # Native shadow (Windows DWM / macOS NSWindow) 原生阴影
    FALLBACK = "fallback"  # Fallback (QML MultiEffect) 兜底方案
    NONE = "none"  # No shadow 无阴影


class ShadowManager(QObject):
    """
    跨平台窗口阴影管理器

    使用示例：
        from prismqml.python.shadow import ShadowManager

        shadow = ShadowManager()
        shadow.enableShadow(window.winId())
    """

    shadowModeChanged = Signal(str)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._mode = self._detectPlatformMode()
        self._initialized = True

    def _detectPlatformMode(self) -> ShadowMode:
        """检测当前平台支持的阴影模式"""
        if sys.platform == "win32":
            return ShadowMode.NATIVE
        elif sys.platform == "darwin":
            return ShadowMode.NATIVE
        else:
            return ShadowMode.FALLBACK

    @Property(str, notify=shadowModeChanged)
    def mode(self) -> str:
        """当前阴影模式"""
        return self._mode.value

    @Property(bool, notify=shadowModeChanged)
    def useNative(self) -> bool:
        """是否使用原生阴影"""
        return self._mode == ShadowMode.NATIVE

    @Property(bool, notify=shadowModeChanged)
    def useFallback(self) -> bool:
        """是否使用兜底方案"""
        return self._mode == ShadowMode.FALLBACK

    @Slot(int, result=bool)
    def enableShadow(self, window_id: int) -> bool:
        """
        为窗口启用原生阴影

        Args:
            window_id: 窗口句柄（QWindow.winId()）

        Returns:
            是否成功启用原生阴影
        """
        if self._mode != ShadowMode.NATIVE:
            return False

        if sys.platform == "win32":
            return self._enableDwmShadow(window_id)
        elif sys.platform == "darwin":
            return self._enableMacShadow(window_id)

        return False

    @Slot("QVariant", result=bool)
    def enableShadowForWindow(self, window) -> bool:
        """
        为QQuickWindow启用原生阴影

        Args:
            window: QQuickWindow对象

        Returns:
            是否成功启用原生阴影
        """
        if self._mode != ShadowMode.NATIVE:
            return False

        try:
            # Get winId from QWindow 从QWindow获取winId
            hwnd = int(window.winId())
            info(f"获取窗口句柄: {hwnd}")
            return self.enableShadow(hwnd)
        except Exception as e:
            error(f"获取窗口句柄失败: {e}")
            return False

    @Slot(int, result=bool)
    def disableShadow(self, window_id: int) -> bool:
        """禁用窗口阴影"""
        if sys.platform == "win32":
            return self._disableDwmShadow(window_id)
        elif sys.platform == "darwin":
            return self._disableMacShadow(window_id)
        return False

    @Slot("QVariant", result=bool)
    def disableShadowForWindow(self, window) -> bool:
        """
        为QQuickWindow禁用原生阴影
        Disable native shadow for QQuickWindow

        Args:
            window: QQuickWindow对象

        Returns:
            是否成功禁用原生阴影
        """
        try:
            hwnd = int(window.winId())
            info(f"禁用窗口阴影: {hwnd}")
            return self.disableShadow(hwnd)
        except Exception as e:
            error(f"禁用窗口阴影失败: {e}")
            return False

    # ==================== Windows DWM ====================

    def _enableDwmShadow(self, hwnd: int) -> bool:
        """
        启用Windows DWM阴影

        方案：使用DWMWA_NCRENDERING_POLICY启用非客户区渲染
        """
        try:
            from ctypes import wintypes

            dwmapi = ctypes.windll.dwmapi
            user32 = ctypes.windll.user32

            # DWMWINDOWATTRIBUTE枚举
            DWMWA_NCRENDERING_POLICY = 2
            DWMNCRP_ENABLED = 2

            # Enable non-client area rendering 启用非客户区渲染
            policy = ctypes.c_int(DWMNCRP_ENABLED)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_NCRENDERING_POLICY,
                ctypes.byref(policy),
                ctypes.sizeof(policy),
            )

            # 使用模块级 MARGINS 结构体

            # Set function signature 设置函数签名
            DwmExtendFrameIntoClientArea = dwmapi.DwmExtendFrameIntoClientArea
            DwmExtendFrameIntoClientArea.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(MARGINS),
            ]
            DwmExtendFrameIntoClientArea.restype = ctypes.HRESULT

            # Extend frame - use 1px to trigger shadow 扩展边框触发阴影
            margins = MARGINS(1, 1, 1, 1)
            result = DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

            # Force redraw 强制重绘
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER,
            )

            info(f"DWM阴影已启用 (hwnd={hwnd}, result={result})")
            return result == 0
        except Exception as e:
            error(f"DWM阴影启用失败: {e}")
            return False

    def _disableDwmShadow(self, hwnd: int) -> bool:
        """禁用Windows DWM阴影"""
        try:
            from ctypes import wintypes

            dwmapi = ctypes.windll.dwmapi

            # 重置 NCRENDERING_POLICY 为默认值 Reset NCRENDERING_POLICY to default
            DWMWA_NCRENDERING_POLICY = 2
            DWMNCRP_USEWINDOWSTYLE = 0  # 使用默认窗口样式
            policy = ctypes.c_int(DWMNCRP_USEWINDOWSTYLE)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_NCRENDERING_POLICY,
                ctypes.byref(policy),
                ctypes.sizeof(policy),
            )

            # Set function signature 设置函数签名
            DwmExtendFrameIntoClientArea = dwmapi.DwmExtendFrameIntoClientArea
            DwmExtendFrameIntoClientArea.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(MARGINS),
            ]
            DwmExtendFrameIntoClientArea.restype = ctypes.HRESULT

            margins = MARGINS(0, 0, 0, 0)
            DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
            return True
        except Exception as e:
            error(f"DWM阴影禁用失败: {e}")
            return False

    # ==================== macOS NSWindow ====================

    def _enableMacShadow(self, window_id: int) -> bool:
        """启用macOS原生阴影"""
        try:
            # Access NSWindow via PyObjC 使用PyObjC访问NSWindow
            import objc
            from AppKit import NSApp

            # Find corresponding NSWindow 查找对应的NSWindow
            for ns_window in NSApp.windows():
                if ns_window.windowNumber() == window_id:
                    ns_window.setHasShadow_(True)
                    return True

            # If not found, try getting via window_id 如果找不到则通过window_id获取
            from Cocoa import NSWindow

            ns_window = objc.objc_object(c_void_p=window_id)
            if ns_window and hasattr(ns_window, "setHasShadow_"):
                ns_window.setHasShadow_(True)
                return True

            return False
        except ImportError:
            warning("macOS需要安装pyobjc: pip install pyobjc")
            return False
        except Exception as e:
            error(f"macOS阴影启用失败: {e}")
            return False

    def _disableMacShadow(self, window_id: int) -> bool:
        """禁用macOS阴影"""
        try:
            import objc
            from AppKit import NSApp

            for ns_window in NSApp.windows():
                if ns_window.windowNumber() == window_id:
                    ns_window.setHasShadow_(False)
                    return True
            return False
        except Exception as e:
            error(f"macOS阴影禁用失败: {e}")
            return False


# ==================== DWM Sync Event Filter DWM同步事件过滤器 ====================


class DwmSyncFilter(QAbstractNativeEventFilter):
    """
    原生事件过滤器 - 在WM_SIZING/WM_SIZE时调用DwmFlush
    Native event filter - calls DwmFlush during WM_SIZING/WM_SIZE

    这是解决无边框窗口resize撕裂的关键
    """

    # Windows消息常量
    WM_SIZE = 0x0005
    WM_SIZING = 0x0214
    WM_MOVING = 0x0216
    WM_ENTERSIZEMOVE = 0x0231
    WM_EXITSIZEMOVE = 0x0232

    # Windows MSG 结构体（类级别定义，避免高频调用时重复创建）
    # Defined at class level to avoid re-creation on every native event
    _MSG = None

    @classmethod
    def _get_msg_class(cls):
        """懒加载 MSG 结构体类"""
        if cls._MSG is None:
            from ctypes import wintypes
            class MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("message", wintypes.UINT),
                    ("wParam", wintypes.WPARAM),
                    ("lParam", wintypes.LPARAM),
                    ("time", wintypes.DWORD),
                    ("pt", wintypes.POINT),
                ]
            cls._MSG = MSG
        return cls._MSG

    def __init__(self):
        super().__init__()
        self._in_resize = False
        self._dwmapi = None
        if sys.platform == "win32":
            try:
                self._dwmapi = ctypes.windll.dwmapi
            except OSError:
                # DWM API not available 无法加载DWM API
                pass

    def nativeEventFilter(self, eventType: QByteArray, message: int) -> tuple:
        """
        过滤Windows原生消息
        Filter Windows native messages
        """
        try:
            if self._dwmapi is None:
                return False, 0

            # 解析MSG结构（使用类级别缓存的结构体定义）
            MSG = self._get_msg_class()
            msg = MSG.from_address(int(message))

            # 在resize/sizing时调用DwmFlush
            if msg.message in (self.WM_SIZING, self.WM_SIZE, self.WM_MOVING):
                self._dwmapi.DwmFlush()
            elif msg.message == self.WM_ENTERSIZEMOVE:
                self._in_resize = True
            elif msg.message == self.WM_EXITSIZEMOVE:
                self._in_resize = False

        except (OSError, ctypes.ArgumentError):
            # Invalid message structure 无效消息结构
            pass
        except BaseException as e:
            # Catch KeyboardInterrupt or any other fatal exceptions to prevent crashing C++ event loop 拦截诸如 KeyboardInterrupt 的异常防止闪退
            warning(f"DwmSyncFilter nativeEventFilter error intercepted: {type(e).__name__}: {e}")

        return False, 0  # 不拦截消息，继续传递


# 全局过滤器实例
_dwm_sync_filter: Optional[DwmSyncFilter] = None


def installDwmSyncFilter():
    """
    安装DWM同步过滤器（应在QApplication创建后调用）
    Install DWM sync filter (call after QApplication creation)
    """
    global _dwm_sync_filter

    if sys.platform != "win32":
        return False

    if _dwm_sync_filter is not None:
        return True  # 已安装

    app = QApplication.instance()
    if app is None:
        warning("QApplication未创建")
        return False

    try:
        _dwm_sync_filter = DwmSyncFilter()
        app.installNativeEventFilter(_dwm_sync_filter)
        info("DWM同步过滤器已安装")
        return True
    except Exception as e:
        error(f"安装失败: {e}")
        return False


# Global singleton 全局单例
def getShadowManager() -> ShadowManager:
    """获取阴影管理器实例"""
    return ShadowManager()
