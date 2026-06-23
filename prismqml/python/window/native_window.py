# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""
NativeWindowHook v4 — 用 Qt 标准 QAbstractNativeEventFilter 拦消息

之前 v1/v2/v3 都失败的根本原因: 用 ctypes SetWindowLongPtr 替换 WndProc
跟 Qt 的内部消息处理打架。Qt 自己有 nativeEvent / installNativeEventFilter
机制,跟 PySide6 完全集成。改用这个,避免与 Qt 状态冲突。

实现策略基于 Win32 DWM API 与 Qt 原生事件过滤的组合,常见 frameless 窗口
方案均围绕这套接口展开。

策略:
1. attach 时 SetWindowLong 加回 WS_CAPTION (DWM 看到才会做动画)
2. 装 QAbstractNativeEventFilter 拦 WM_NCCALCSIZE (掩盖 caption 视觉)
3. 不动 WndProc
"""

import sys
import ctypes
from ctypes import wintypes
from typing import Dict, Optional

from PySide6.QtCore import QObject, Slot, QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtGui import QWindow

from ..core.logger import info, warning, error, debug


# ============================================================================
# Win32 常量
# ============================================================================

WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000

GWL_STYLE = -16

WM_NCCALCSIZE = 0x0083

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020


if sys.platform == "win32":
    user32 = ctypes.windll.user32

    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t

    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL

    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.IsZoomed.restype = wintypes.BOOL


# ============================================================================
# Native Event Filter
# ============================================================================

class _MsgFilter(QAbstractNativeEventFilter):
    """拦截 hook 过的 hwnd 上的 WM_NCCALCSIZE,客户区扩展到整个窗口。"""

    def __init__(self, hwnd_set):
        super().__init__()
        self._hwnds = hwnd_set  # set[int],引用 NativeWindowHook 的集合

    def nativeEventFilter(self, eventType, message):
        if eventType != b"windows_generic_MSG" and eventType != "windows_generic_MSG":
            return False, 0

        try:
            # message 是 PyCapsule,转 MSG 结构体
            msg = ctypes.cast(int(message), ctypes.POINTER(_MSG)).contents
            if msg.message != WM_NCCALCSIZE:
                return False, 0
            if msg.hwnd not in self._hwnds:
                return False, 0
            if not msg.wParam:
                return False, 0

            # NCCALCSIZE_PARAMS 模式: 直接返回 0 让客户区 = 整个窗口
            # 最大化时扣 8 像素防超出工作区
            if user32.IsZoomed(msg.hwnd):
                rect_ptr = ctypes.cast(msg.lParam, ctypes.POINTER(wintypes.RECT))
                rect_ptr.contents.left += 8
                rect_ptr.contents.top += 8
                rect_ptr.contents.right -= 8
                rect_ptr.contents.bottom -= 8
            return True, 0
        except Exception as e:
            error(f"_MsgFilter 异常: {e}")
            return False, 0


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", ctypes.c_long),
        ("pt_y", ctypes.c_long),
    ]


# ============================================================================
# NativeWindowHook
# ============================================================================

class NativeWindowHook(QObject):
    """单例: 给 frameless 窗口加 WS_CAPTION + 通过 Qt nativeEventFilter 拦
    NCCALCSIZE,让 DWM 接管 minimize/maximize/restore 动画但视觉无标题栏。"""

    _instance: Optional["NativeWindowHook"] = None

    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent=None):
        if getattr(self, "_initialized", False):
            return
        super().__init__(parent)
        self._initialized = True
        self._hwnds = set()  # 已 attach 的 hwnd 集合
        self._original_styles: Dict[int, int] = {}
        self._filter = None

        if sys.platform == "win32":
            self._filter = _MsgFilter(self._hwnds)
            app = QCoreApplication.instance()
            if app:
                app.installNativeEventFilter(self._filter)

    @Slot(QWindow)
    def attach(self, window: QWindow):
        """加 WS_CAPTION + 注册 hwnd 到 filter 集合。"""
        if sys.platform != "win32" or not window:
            return
        try:
            hwnd = int(window.winId())
            if not hwnd or hwnd in self._hwnds:
                return

            original_style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
            new_style = (
                original_style
                | WS_CAPTION
                | WS_THICKFRAME
                | WS_MINIMIZEBOX
                | WS_MAXIMIZEBOX
                | WS_SYSMENU
            )
            user32.SetWindowLongPtrW(hwnd, GWL_STYLE, new_style)

            self._hwnds.add(hwnd)
            self._original_styles[hwnd] = original_style

            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )

            info(f"NativeWindowHook v4: attached hwnd={hwnd}, "
                 f"style 0x{original_style:08x} → 0x{new_style:08x}")
        except Exception as e:
            error(f"NativeWindowHook.attach 失败: {e}")

    @Slot(QWindow)
    def detach(self, window: QWindow):
        if sys.platform != "win32" or not window:
            return
        try:
            hwnd = int(window.winId())
            if hwnd not in self._hwnds:
                return
            user32.SetWindowLongPtrW(hwnd, GWL_STYLE, self._original_styles[hwnd])
            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )
            self._hwnds.discard(hwnd)
            del self._original_styles[hwnd]
            info(f"NativeWindowHook: detached hwnd={hwnd}")
        except Exception as e:
            error(f"NativeWindowHook.detach 失败: {e}")


_native_window_hook_singleton: Optional[NativeWindowHook] = None


def get_native_window_hook() -> NativeWindowHook:
    global _native_window_hook_singleton
    if _native_window_hook_singleton is None:
        _native_window_hook_singleton = NativeWindowHook()
    return _native_window_hook_singleton
