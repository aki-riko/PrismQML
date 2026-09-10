# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Windows notification banner detection. Windows 通知横幅检测。

系统通知横幅由 ShellExperienceHost.exe 的 Windows.UI.Core.CoreWindow 承载，
位于 window band 4（ZBID_IMMERSIVE_NOTIFICATION）。普通应用窗口最高只能进入
band 1（ZBID_DESKTOP），且普通进程无法提升自身 band（CreateWindowInBand /
SetWindowBand 对 band >= 2 一律返回 ERROR_ACCESS_DENIED），因此自绘的桌面
通知无法压在系统横幅之上，只能读取其占用高度后避让。

本模块保持纯 Win32：只返回物理像素高度，不做任何 Qt 换算。
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import List, Optional, Tuple

from .logger import debug

# Window band used by Action Center and toast banners. 系统通知横幅所用层带。
ZBID_IMMERSIVE_NOTIFICATION = 4

_GA_ROOT = 2
_MONITOR_DEFAULTTONEAREST = 2

# Bottom-right sampling offsets in physical pixels. 右下角采样偏移（物理像素）。
_SAMPLE_INSET_X = (40, 140, 260, 400, 540)
_SAMPLE_INSET_Y = (40, 100, 160, 210)

# Reservation ceiling as a ratio of the monitor work area height.
# 保留高度上限，按显示器工作区高度的比例钳制，避免通知堆叠时把窗口顶出屏幕。
MAX_RESERVATION_RATIO = 0.6

_MONITOR_ENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HANDLE,
    wintypes.HDC,
    ctypes.POINTER(wintypes.RECT),
    wintypes.LPARAM,
)


class _MONITORINFO(ctypes.Structure):
    """MONITORINFO layout. 显示器信息结构。"""

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class _User32BannerApi:
    """Pointer-width user32 bindings for banner probing. 横幅探测所需的 user32 绑定。"""

    def __init__(self) -> None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)

        self.window_from_point = user32.WindowFromPoint
        self.window_from_point.argtypes = [wintypes.POINT]
        self.window_from_point.restype = wintypes.HWND

        self.get_ancestor = user32.GetAncestor
        self.get_ancestor.argtypes = [wintypes.HWND, wintypes.UINT]
        self.get_ancestor.restype = wintypes.HWND

        self.get_window_rect = user32.GetWindowRect
        self.get_window_rect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.get_window_rect.restype = wintypes.BOOL

        # Undocumented but exported by user32 since Windows 8.
        # 未文档化，但自 Windows 8 起由 user32 导出。
        self.get_window_band = user32.GetWindowBand
        self.get_window_band.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.get_window_band.restype = wintypes.BOOL

        self.monitor_from_window = user32.MonitorFromWindow
        self.monitor_from_window.argtypes = [wintypes.HWND, wintypes.DWORD]
        self.monitor_from_window.restype = wintypes.HANDLE

        self.get_monitor_info = user32.GetMonitorInfoW
        self.get_monitor_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MONITORINFO)]
        self.get_monitor_info.restype = wintypes.BOOL

        self.enum_display_monitors = user32.EnumDisplayMonitors
        self.enum_display_monitors.argtypes = [
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            _MONITOR_ENUMPROC,
            wintypes.LPARAM,
        ]
        self.enum_display_monitors.restype = wintypes.BOOL


_API: Optional[_User32BannerApi] = None
_MONITOR_RECTS: List[Tuple[int, int, int, int]] = []


def _api() -> Optional[_User32BannerApi]:
    """Return bound bindings, or None off Windows. 返回绑定对象，非 Windows 返回 None。"""
    global _API
    if sys.platform != "win32":
        return None
    if _API is None:
        try:
            _API = _User32BannerApi()
        except (AttributeError, OSError) as exc:
            debug(f"通知横幅探测不可用: {exc}")
            return None
    return _API


def _collect_monitor(_monitor, _hdc, rect_pointer, _lparam) -> bool:
    """Collect one monitor rectangle. 收集一个显示器矩形。"""
    rect = rect_pointer.contents
    _MONITOR_RECTS.append((rect.left, rect.top, rect.right, rect.bottom))
    return True


def _sample_points() -> List[Tuple[int, int]]:
    """Return bottom-right sampling points for every monitor. 返回每个显示器右下角采样点。"""
    api = _api()
    if api is None:
        return []
    del _MONITOR_RECTS[:]
    api.enum_display_monitors(None, None, _MONITOR_ENUMPROC(_collect_monitor), 0)
    points: List[Tuple[int, int]] = []
    for left, top, right, bottom in _MONITOR_RECTS:
        for inset_y in _SAMPLE_INSET_Y:
            for inset_x in _SAMPLE_INSET_X:
                x = right - inset_x
                y = bottom - inset_y
                if x > left and y > top:
                    points.append((x, y))
    return points


def _window_band(api: _User32BannerApi, hwnd: int) -> Optional[int]:
    """Read one window band. 读取一个窗口的层带。"""
    value = wintypes.DWORD(0)
    ctypes.set_last_error(0)
    if not api.get_window_band(hwnd, ctypes.byref(value)):
        return None
    return int(value.value)


def notification_banner_handles() -> List[int]:
    """Return handles of live band-4 notification banners. 返回活动通知横幅句柄。"""
    api = _api()
    if api is None:
        return []
    handles: List[int] = []
    for x, y in _sample_points():
        hwnd = api.window_from_point(wintypes.POINT(x, y))
        if not hwnd:
            continue
        root = api.get_ancestor(hwnd, _GA_ROOT) or hwnd
        if root in handles:
            continue
        if _window_band(api, root) == ZBID_IMMERSIVE_NOTIFICATION:
            handles.append(root)
    return handles


def clamp_reservation(reserved: int, work_height: int) -> int:
    """Clamp one reservation to the allowed ratio. 按允许比例钳制保留高度。

    通知堆叠时横幅可以占掉半个屏幕，钳制可避免把底部锚定窗口顶出屏幕。
    """
    if reserved <= 0 or work_height <= 0:
        return 0
    return min(reserved, int(work_height * MAX_RESERVATION_RATIO))


def notification_banner_reservation() -> int:
    """Return the physical height reserved at the work-area bottom.

    返回工作区底部被系统通知横幅占用的物理像素高度；无横幅时返回 0。

    只使用横幅矩形顶边与该显示器工作区底边之差，不涉及任何绝对坐标，
    因此调用方无需关心屏幕原点或多屏排列。
    """
    api = _api()
    if api is None:
        return 0
    reserved = 0
    work_height = 0
    for hwnd in notification_banner_handles():
        rect = wintypes.RECT()
        if not api.get_window_rect(hwnd, ctypes.byref(rect)):
            continue
        monitor = api.monitor_from_window(hwnd, _MONITOR_DEFAULTTONEAREST)
        if not monitor:
            continue
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        if not api.get_monitor_info(monitor, ctypes.byref(info)):
            continue
        occupied = int(info.rcWork.bottom) - int(rect.top)
        if occupied > reserved:
            reserved = occupied
            work_height = int(info.rcWork.bottom) - int(info.rcWork.top)
    return clamp_reservation(reserved, work_height)
