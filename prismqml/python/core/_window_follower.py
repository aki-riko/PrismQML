# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Native host/follower synchronization internals. 原生宿主与附属窗口同步内部实现。"""
import ctypes
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional

from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray, QRect

from .logger import debug, error, exception


# Window edge values mirror Enums.position. 窗口边缘值与 Enums.position 保持一致。
WINDOW_EDGE_LEFT = 0
WINDOW_EDGE_RIGHT = 1
WINDOW_EDGE_TOP = 2
WINDOW_EDGE_BOTTOM = 3
_WINDOW_EDGES = frozenset(
    (WINDOW_EDGE_LEFT, WINDOW_EDGE_RIGHT, WINDOW_EDGE_TOP, WINDOW_EDGE_BOTTOM)
)

_WM_SIZING = 0x0214
_WM_MOVING = 0x0216
_WM_MOUSEACTIVATE = 0x0021
_WM_WINDOWPOSCHANGING = 0x0046
_MA_NOACTIVATE = 0x0003
_SWP_NOSIZE, _SWP_NOMOVE = 0x0001, 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_NOOWNERZORDER = 0x0200
_SWP_PROMOTE_FLAGS = _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOACTIVATE | _SWP_NOOWNERZORDER
_DEFAULT_DEVICE_PIXEL_RATIO = 1.0
_MINIMUM_NATIVE_EXTENT = 1


@dataclass(frozen=True)
class _WindowFollowerBinding:
    """One native host/follower edge relation. 一条原生宿主/附属窗口边缘关系。"""

    host_hwnd: int
    follower_hwnd: int
    edge: int
    outward_extent: int


@dataclass(frozen=True)
class _WindowRect:
    """Platform-neutral window edges. 平台无关窗口边缘。"""

    left: int
    top: int
    right: int
    bottom: int


def _follower_rect(
    host_rect: Any,
    follower_width: int,
    follower_height: int,
    edge: int,
) -> tuple[int, int, int, int]:
    """Calculate a physical-pixel follower RECT. 计算物理像素附属窗口 RECT。"""
    if edge == WINDOW_EDGE_LEFT:
        return (host_rect.left - follower_width, host_rect.top,
                host_rect.left, host_rect.bottom)
    if edge == WINDOW_EDGE_RIGHT:
        return (host_rect.right, host_rect.top,
                host_rect.right + follower_width, host_rect.bottom)
    if edge == WINDOW_EDGE_TOP:
        return (host_rect.left, host_rect.top - follower_height,
                host_rect.right, host_rect.top)
    if edge == WINDOW_EDGE_BOTTOM:
        return (host_rect.left, host_rect.bottom,
                host_rect.right, host_rect.bottom + follower_height)
    raise ValueError(f"Unsupported window follower edge: {edge}")


def _follower_rect_for_extent(
    host_rect: Any,
    extent: int,
    edge: int,
) -> tuple[int, int, int, int]:
    """Calculate one complete follower RECT. 计算一个完整附属窗口 RECT。"""
    host_width = host_rect.right - host_rect.left
    host_height = host_rect.bottom - host_rect.top
    follower_width = (
        extent if edge in (WINDOW_EDGE_LEFT, WINDOW_EDGE_RIGHT) else host_width
    )
    follower_height = (
        extent if edge in (WINDOW_EDGE_TOP, WINDOW_EDGE_BOTTOM) else host_height
    )
    return _follower_rect(host_rect, follower_width, follower_height, edge)


def _window_rect_from_pos(
    window_pos: Any, current_rect: Optional[Any] = None
) -> Optional[_WindowRect]:
    """Build a proposed host RECT from WM_WINDOWPOSCHANGING. 从原生候选几何构造宿主矩形。"""
    if window_pos.flags & _SWP_NOMOVE:
        return None
    width = (
        int(current_rect.right - current_rect.left)
        if window_pos.flags & _SWP_NOSIZE and current_rect is not None
        else int(window_pos.cx)
    )
    height = (
        int(current_rect.bottom - current_rect.top)
        if window_pos.flags & _SWP_NOSIZE and current_rect is not None
        else int(window_pos.cy)
    )
    if width <= 0 or height <= 0:
        return None
    return _WindowRect(
        int(window_pos.x),
        int(window_pos.y),
        int(window_pos.x + width),
        int(window_pos.y + height),
    )


def _window_device_pixel_ratio(window: Any) -> float:
    """Read a valid QWindow device scale. 读取有效的 QWindow 设备缩放。"""
    try:
        ratio_getter = getattr(window, "devicePixelRatio", None)
        ratio = float(ratio_getter()) if callable(ratio_getter) else _DEFAULT_DEVICE_PIXEL_RATIO
    except (RuntimeError, TypeError, ValueError):
        return _DEFAULT_DEVICE_PIXEL_RATIO
    return ratio if ratio > 0 else _DEFAULT_DEVICE_PIXEL_RATIO


def _set_qt_follower_geometry(
    host_window: Any,
    follower_window: Any,
    edge: int,
    logical_extent: float,
) -> bool:
    """Fallback to one Qt geometry commit. 回退为一次 Qt 几何提交。"""
    try:
        host_geometry = host_window.frameGeometry()
        host_rect = _WindowRect(
            host_geometry.left(),
            host_geometry.top(),
            host_geometry.right() + 1,
            host_geometry.bottom() + 1,
        )
        extent = max(_MINIMUM_NATIVE_EXTENT, round(logical_extent))
        left, top, right, bottom = _follower_rect_for_extent(
            host_rect, extent, edge
        )
        follower_window.setGeometry(
            QRect(left, top, right - left, bottom - top)
        )
        return True
    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
        error(f"Qt附属窗口几何更新失败: {exc}")
        return False


def _load_user32_window_functions():
    """Load pointer-width Win32 window functions. 加载指针宽度 Win32 窗口函数。"""
    if sys.platform != "win32":
        return None
    try:
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        get_window_rect = user32.GetWindowRect
        get_window_rect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        get_window_rect.restype = wintypes.BOOL
        set_window_pos = user32.SetWindowPos
        set_window_pos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        set_window_pos.restype = wintypes.BOOL
        set_foreground_window = user32.SetForegroundWindow
        set_foreground_window.argtypes = [wintypes.HWND]
        set_foreground_window.restype = wintypes.BOOL
        return get_window_rect, set_window_pos, set_foreground_window
    except (AttributeError, OSError) as exc:
        debug(f"Win32窗口跟随 API 不可用: {exc}")
        return None


def _read_native_window_rect(get_window_rect, hwnd: int):
    """Read one Win32 window RECT. 读取一个 Win32 窗口 RECT。"""
    from ctypes import wintypes

    rect = wintypes.RECT()
    if not get_window_rect(hwnd, ctypes.byref(rect)):
        return None
    return rect


def _set_native_window_geometry(
    set_window_pos,
    hwnd: int,
    geometry,
    insert_after: int,
) -> bool:
    """Apply one physical-pixel follower geometry. 应用物理像素附属窗口几何。"""
    left, top, right, bottom = geometry
    flags = _SWP_NOACTIVATE | _SWP_NOOWNERZORDER
    return bool(
        set_window_pos(
            hwnd,
            insert_after,
            left,
            top,
            right - left,
            bottom - top,
            flags,
        )
    )


class _WindowFollowerFilter(QAbstractNativeEventFilter):
    """Synchronize followers inside WM_MOVING/WM_SIZING. 在原生移动循环同步附属窗口。"""

    _MSG = None
    _WINDOWPOS = None

    def __init__(
        self,
        read_rect: Optional[Callable[[int], Any]] = None,
        set_geometry: Optional[
            Callable[[int, tuple[int, int, int, int], int], bool]
        ] = None,
        promote_window: Optional[Callable[[int, Optional[int]], bool]] = None,
        activate_window: Optional[Callable[[int], bool]] = None,
    ) -> None:
        super().__init__()
        functions = _load_user32_window_functions()
        if read_rect is None and functions is not None:
            read_rect = lambda hwnd: _read_native_window_rect(functions[0], hwnd)
        if set_geometry is None and functions is not None:
            set_geometry = lambda hwnd, geometry, insert_after: (
                _set_native_window_geometry(
                    functions[1], hwnd, geometry, insert_after
                )
            )
        if promote_window is None and functions is not None:
            promote_window = lambda hwnd, after: bool(
                functions[1](hwnd, after, 0, 0, 0, 0, _SWP_PROMOTE_FLAGS))
        if activate_window is None and functions is not None:
            activate_window = lambda hwnd: bool(functions[2](hwnd))
        self._read_rect = read_rect
        self._set_geometry = set_geometry
        self._promote_window = promote_window
        self._activate_window = activate_window
        self._bindings: dict[int, _WindowFollowerBinding] = {}

    @property
    def binding_count(self) -> int:
        """Return active binding count. 返回活动绑定数量。"""
        return len(self._bindings)

    @classmethod
    def _get_msg_class(cls):
        """Lazily build a pointer-width MSG type. 延迟构建指针宽度 MSG 类型。"""
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

    @classmethod
    def _get_window_pos_class(cls):
        """Lazily build a pointer-width WINDOWPOS type. 延迟构建 WINDOWPOS 类型。"""
        if cls._WINDOWPOS is None:
            from ctypes import wintypes

            class WINDOWPOS(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("hwndInsertAfter", wintypes.HWND),
                    ("x", ctypes.c_int),
                    ("y", ctypes.c_int),
                    ("cx", ctypes.c_int),
                    ("cy", ctypes.c_int),
                    ("flags", wintypes.UINT),
                ]

            cls._WINDOWPOS = WINDOWPOS
        return cls._WINDOWPOS

    def register(
        self,
        host_hwnd: int,
        follower_hwnd: int,
        edge: int,
        extent: int,
    ) -> bool:
        """Register or update one follower. 注册或更新一个附属窗口。"""
        registration = self._registration_geometry(host_hwnd, edge, extent)
        if registration is None:
            return False
        if not self._set_geometry(follower_hwnd, registration, host_hwnd):
            debug(f"附属窗口初次原生同步失败: hwnd={follower_hwnd}")
            return False
        self._bindings[follower_hwnd] = _WindowFollowerBinding(
            host_hwnd, follower_hwnd, edge, extent
        )
        return True

    def _registration_geometry(
        self,
        host_hwnd: int,
        edge: int,
        extent: int,
    ):
        """Resolve the initial native follower geometry. 解析初始原生跟随几何。"""
        if (
            edge not in _WINDOW_EDGES
            or extent < _MINIMUM_NATIVE_EXTENT
            or self._read_rect is None
            or self._set_geometry is None
        ):
            return None
        host_rect = self._read_rect(host_hwnd)
        if host_rect is None:
            return None
        return _follower_rect_for_extent(host_rect, extent, edge)

    def update_geometry(
        self,
        host_hwnd: int,
        follower_hwnd: int,
        edge: int,
        extent: int,
    ) -> bool:
        """Submit one complete animation-frame RECT. 提交一帧完整动画 RECT。"""
        if (
            edge not in _WINDOW_EDGES
            or extent < _MINIMUM_NATIVE_EXTENT
            or self._read_rect is None
            or self._set_geometry is None
        ):
            return False
        host_rect = self._read_rect(host_hwnd)
        if host_rect is None:
            return False
        geometry = _follower_rect_for_extent(host_rect, extent, edge)
        return self._set_geometry(follower_hwnd, geometry, host_hwnd)

    def unregister(self, follower_hwnd: int) -> bool:
        """Remove one follower binding. 移除一个附属窗口绑定。"""
        return self._bindings.pop(follower_hwnd, None) is not None

    def sync_host_rect(self, host_hwnd: int, host_rect: Any) -> None:
        """Synchronize followers to a proposed host RECT. 同步到宿主候选 RECT。"""
        if self._set_geometry is None:
            return
        for binding in tuple(self._bindings.values()):
            if binding.host_hwnd != host_hwnd:
                continue
            geometry = _follower_rect_for_extent(
                host_rect,
                binding.outward_extent,
                binding.edge,
            )
            if not self._set_geometry(
                binding.follower_hwnd, geometry, binding.host_hwnd
            ):
                debug(f"附属窗口原生同步失败: hwnd={binding.follower_hwnd}")

    def enforce_follower_z_order(self, follower_hwnd: int, window_pos) -> None:
        """Promote the host, then keep its follower behind. 提升宿主后保持附属窗口在下层。"""
        binding = self._bindings.get(follower_hwnd)
        if binding is None:
            return
        if (
            not window_pos.flags & _SWP_NOZORDER
            and window_pos.hwndInsertAfter != binding.host_hwnd
            and self._promote_window is not None
            and not self._promote_window(binding.host_hwnd, window_pos.hwndInsertAfter)
        ):
            debug(f"宿主窗口原生抬升失败: hwnd={binding.host_hwnd}")
        window_pos.hwndInsertAfter = binding.host_hwnd
        window_pos.flags &= ~_SWP_NOZORDER
        window_pos.flags |= _SWP_NOOWNERZORDER

    def _resolve_window_group(
        self, window_hwnd: int
    ) -> tuple[int, tuple[int, ...]]:
        """Resolve either a host or follower to its complete group. 将宿主或附属窗口解析为完整窗口组。"""
        clicked_binding = self._bindings.get(window_hwnd)
        host_hwnd = (
            clicked_binding.host_hwnd
            if clicked_binding is not None
            else window_hwnd
        )
        follower_hwnds = tuple(
            binding.follower_hwnd
            for binding in self._bindings.values()
            if binding.host_hwnd == host_hwnd
        )
        if not follower_hwnds:
            return 0, ()
        return host_hwnd, follower_hwnds

    def promote_window_group(
        self, host_hwnd: int, follower_hwnds: tuple[int, ...]
    ) -> None:
        """Place the host first, followed by every follower. 先放置宿主，再连续放置全部附属窗口。"""
        if self._promote_window is None:
            return
        insert_after = 0
        for hwnd in (host_hwnd, *follower_hwnds):
            if not self._promote_window(hwnd, insert_after):
                window_role = "宿主" if hwnd == host_hwnd else "附属"
                debug(f"{window_role}窗口原生抬升失败: hwnd={hwnd}")
            insert_after = hwnd

    def activate_window_group(self, window_hwnd: int) -> bool:
        """Activate a host/follower group without delaying the click. 激活窗口组且不延迟点击。"""
        host_hwnd, follower_hwnds = self._resolve_window_group(window_hwnd)
        if (
            not host_hwnd
            or self._activate_window is None
            or self._promote_window is None
        ):
            return False
        if not self._activate_window(host_hwnd):
            debug(f"宿主窗口原生激活失败: hwnd={host_hwnd}")
            return False
        self.promote_window_group(host_hwnd, follower_hwnds)
        return True

    def _handle_window_pos_changing(self, msg: Any) -> tuple[bool, int]:
        """Sync one proposed WINDOWPOS update. 同步一次候选 WINDOWPOS 更新。"""
        window_pos = self._get_window_pos_class().from_address(int(msg.lParam))
        window_hwnd = int(msg.hwnd)
        self.enforce_follower_z_order(window_hwnd, window_pos)
        if window_hwnd not in self._bindings:
            current_rect = (
                self._read_rect(window_hwnd)
                if window_pos.flags & _SWP_NOSIZE
                and self._read_rect is not None
                else None
            )
            proposed_rect = _window_rect_from_pos(window_pos, current_rect)
            if proposed_rect is not None:
                self.sync_host_rect(window_hwnd, proposed_rect)
        return False, 0

    def _handle_native_message(self, msg: Any) -> tuple[bool, int]:
        """Dispatch one native follower message. 分派一条原生窗口跟随消息。"""
        if msg.message == _WM_MOUSEACTIVATE:
            if self.activate_window_group(int(msg.hwnd)):
                return True, _MA_NOACTIVATE
            return False, 0
        if msg.message == _WM_WINDOWPOSCHANGING and msg.lParam:
            return self._handle_window_pos_changing(msg)
        if msg.message not in (_WM_MOVING, _WM_SIZING) or not msg.lParam:
            return False, 0
        from ctypes import wintypes

        host_rect = wintypes.RECT.from_address(int(msg.lParam))
        self.sync_host_rect(int(msg.hwnd), host_rect)
        return False, 0

    def nativeEventFilter(self, eventType: QByteArray, message: int) -> tuple:
        """Consume proposed move/size RECTs without blocking Qt. 消费候选 RECT 但不拦截 Qt。"""
        del eventType
        try:
            msg = self._get_msg_class().from_address(int(message))
            return self._handle_native_message(msg)
        except (OSError, ValueError, ctypes.ArgumentError) as exc:
            debug(f"窗口跟随过滤器收到无效原生消息: {exc}")
        except Exception as exc:
            exception(
                "Window follower nativeEventFilter failed: "
                f"{type(exc).__name__}: {exc}"
            )
        return False, 0
