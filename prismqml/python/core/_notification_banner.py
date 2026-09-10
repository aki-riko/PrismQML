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

横幅默认出现在工作区右下角并紧贴边缘，但任务栏位置、RTL 镜像或多显示器
配置都可能把它移到别的角落，因此本模块在**四个角**采样，并按横幅实际
贴靠的上/下边缘分别上报保留高度。

四角覆盖的依据：Windows 11 正在重新引入任务栏位置切换（Microsoft 发布说明
Build 26100.9267 起："You can now choose whether the taskbar appears at the
bottom, top, left, or right side of your screen"），而任务栏置于四边时横幅
与其同位。在尚未启用该功能的版本上实测（Windows 10 IoT Enterprise LTSC 2024
/ 26100.9168）：改写 StuckRects3 的 Settings[12] 并重启 shell 后，任务栏仍
固定在底部，横幅只出现在右下角。

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

# Work-area edges a banner can be anchored to. 横幅可贴靠的工作区边缘。
EDGE_TOP = 0
EDGE_BOTTOM = 1

_GA_ROOT = 2
_MONITOR_DEFAULTTONEAREST = 2

# Corner sampling offsets in physical pixels. 四角采样偏移（物理像素）。
_SAMPLE_INSET_X = (40, 200, 360, 520)
_SAMPLE_INSET_Y = (40, 120, 200)

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
    """Return sampling points at all four corners of every monitor.

    返回每个显示器四个角的采样点。横幅默认在右下角，但任务栏位置、RTL 镜像
    或显示器配置都可能把它移到别的角落，因此四角都要覆盖。
    """
    api = _api()
    if api is None:
        return []
    del _MONITOR_RECTS[:]
    api.enum_display_monitors(None, None, _MONITOR_ENUMPROC(_collect_monitor), 0)
    points: List[Tuple[int, int]] = []
    for left, top, right, bottom in _MONITOR_RECTS:
        for inset_y in _SAMPLE_INSET_Y:
            for inset_x in _SAMPLE_INSET_X:
                for x in (right - inset_x, left + inset_x):
                    for y in (bottom - inset_y, top + inset_y):
                        if left < x < right and top < y < bottom:
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


def banner_edge_and_height(
    rect: Tuple[int, int, int, int],
    work: Tuple[int, int, int, int],
) -> Tuple[int, int]:
    """Classify one banner rect against a work area. 按工作区判定横幅贴靠的边缘与占用高度。

    取横幅较窄的一侧间隙判定贴靠边：贴近底部时占用高度从工作区底边量到
    横幅顶边，贴近顶部时从工作区顶边量到横幅底边。
    """
    left, top, right, bottom = rect
    work_left, work_top, work_right, work_bottom = work
    gap_top = top - work_top
    gap_bottom = work_bottom - bottom
    if gap_bottom <= gap_top:
        return EDGE_BOTTOM, work_bottom - top
    return EDGE_TOP, bottom - work_top


def clamp_reservation(reserved: int, work_height: int) -> int:
    """Clamp one reservation to the allowed ratio. 按允许比例钳制保留高度。

    通知堆叠时横幅可以占掉半个屏幕，钳制可避免把边缘锚定窗口顶出屏幕。
    """
    if reserved <= 0 or work_height <= 0:
        return 0
    return min(reserved, int(work_height * MAX_RESERVATION_RATIO))


def notification_banner_reservations() -> Tuple[int, int]:
    """Return (top, bottom) reserved physical heights. 返回 (顶部, 底部) 保留高度。

    两者都是物理像素；对应边缘没有横幅时为 0。只使用横幅矩形与工作区边缘
    之间的距离，不涉及屏幕原点，因此调用方无需关心多屏排列。
    """
    api = _api()
    if api is None:
        return 0, 0
    reserved = {EDGE_TOP: 0, EDGE_BOTTOM: 0}
    work_height = {EDGE_TOP: 0, EDGE_BOTTOM: 0}
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
        edge, height = banner_edge_and_height(
            (rect.left, rect.top, rect.right, rect.bottom),
            (
                info.rcWork.left,
                info.rcWork.top,
                info.rcWork.right,
                info.rcWork.bottom,
            ),
        )
        if height > reserved[edge]:
            reserved[edge] = height
            work_height[edge] = int(info.rcWork.bottom) - int(info.rcWork.top)
    return (
        clamp_reservation(reserved[EDGE_TOP], work_height[EDGE_TOP]),
        clamp_reservation(reserved[EDGE_BOTTOM], work_height[EDGE_BOTTOM]),
    )
