# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Qt-native Win32 hook for frameless-window DWM animations.

Qt 原生 Win32 钩子，用于无边框窗口的 DWM 动画。
"""

import sys
import ctypes
from ctypes import wintypes
from typing import Dict, Optional

import shiboken6
from PySide6.QtCore import QObject, Slot, QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtGui import QWindow

from ..core.logger import exception, info


# ============================================================================
# Win32 常量
# ============================================================================

WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000

GWL_STYLE = -16
ERROR_INVALID_WINDOW_HANDLE = 1400

WM_NCCALCSIZE = 0x0083
WM_SYSCOMMAND = 0x0112

SC_MAXIMIZE = 0xF030
SC_RESTORE = 0xF120

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
FRAME_CHANGED_FLAGS = (
    SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
)


user32 = None


def _ignore_last_error(_value: int) -> None:
    """No-op LastError setter outside Windows. 非 Windows 的 LastError 空操作。"""


def _zero_last_error() -> int:
    """Return a neutral LastError outside Windows. 非 Windows 返回中性错误码。"""
    return 0


_set_last_error = _ignore_last_error
_get_last_error = _zero_last_error

if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _set_last_error = ctypes.set_last_error
    _get_last_error = ctypes.get_last_error

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

    user32.PostMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.PostMessageW.restype = wintypes.BOOL


def _raise_winapi_failure(operation: str, error_code: int) -> None:
    """Raise one deterministic WinAPI failure. 抛出确定性的 WinAPI 失败。"""
    if error_code:
        raise OSError(error_code, f"{operation} failed")
    raise OSError(f"{operation} failed without a LastError code")


def _get_window_style(hwnd: int) -> int:
    """Read GWL_STYLE with the documented zero-result rule. 按零返回合同读取样式。"""
    _set_last_error(0)
    style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
    error_code = _get_last_error()
    if style == 0 and error_code != 0:
        _raise_winapi_failure("GetWindowLongPtrW", error_code)
    return int(style)


def _set_window_style(hwnd: int, style: int) -> int:
    """Write GWL_STYLE and return the actual previous value. 写入并返回真实旧样式。"""
    _set_last_error(0)
    previous_style = user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
    error_code = _get_last_error()
    if previous_style == 0 and error_code != 0:
        _raise_winapi_failure("SetWindowLongPtrW", error_code)
    return int(previous_style)


def _request_frame_changed(hwnd: int) -> None:
    """Apply SWP_FRAMECHANGED or raise. 应用 SWP_FRAMECHANGED，失败即抛出。"""
    _set_last_error(0)
    succeeded = user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, FRAME_CHANGED_FLAGS)
    error_code = _get_last_error()
    if not succeeded:
        _raise_winapi_failure("SetWindowPos", error_code)


def _post_system_command(hwnd: int, command: int) -> None:
    """Post a native system command or raise. 投递原生系统命令，失败即抛出。"""
    _set_last_error(0)
    succeeded = user32.PostMessageW(hwnd, WM_SYSCOMMAND, command, 0)
    error_code = _get_last_error()
    if not succeeded:
        _raise_winapi_failure("PostMessageW", error_code)


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
        except Exception as exc:
            exception(
                "NativeWindow message filter failed: "
                f"{type(exc).__name__}: {exc}"
            )
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

    def __new__(
        cls,
        parent=None,
        *,
        _isolated: bool = False,
        _install_filter: bool = True,
    ):
        if _isolated:
            instance = super().__new__(cls)
            instance._initialized = False
            return instance
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        parent=None,
        *,
        _isolated: bool = False,
        _install_filter: bool = True,
    ):
        if getattr(self, "_initialized", False):
            return
        super().__init__(parent)
        self._initialized = True
        self._hwnds = set()  # 已 attach 的 hwnd 集合
        self._framechanged_hwnds = set()
        self._restore_pending_hwnds = set()
        self._original_styles: Dict[int, int] = {}
        self._owner_generations: Dict[int, object] = {}
        self._owner_keys: Dict[object, int] = {}
        self._owner_hwnds: Dict[object, int] = {}
        self._hwnd_owners: Dict[int, object] = {}
        self._retired_owner_hwnds: Dict[object, int] = {}
        self._wrapper_owner_keys: Dict[int, int] = {}
        self._owner_wrapper_ids: Dict[int, set] = {}
        self._filter = None

        if sys.platform == "win32" and _install_filter:
            self._filter = _MsgFilter(self._hwnds)
            app = QCoreApplication.instance()
            if app:
                app.installNativeEventFilter(self._filter)

    @Slot(QWindow, result=bool)
    def attach(self, window: QWindow) -> bool:
        """加 WS_CAPTION + 注册 hwnd 到 filter 集合。"""
        return self._attach_boundary(window, "attach")

    @Slot(QWindow, result=bool)
    def finalizeAttach(self, window: QWindow) -> bool:
        """补执行 SWP_FRAMECHANGED。未 attach 时退化为完整 attach。"""
        return self._attach_boundary(window, "finalizeAttach")

    @Slot(QWindow, result=bool)
    def requestMaximize(self, window: QWindow) -> bool:
        """Use the native maximize command for DWM animation. 使用原生最大化命令触发 DWM 动画。"""
        return self._request_system_command(
            window, SC_MAXIMIZE, "requestMaximize"
        )

    @Slot(QWindow, result=bool)
    def requestRestore(self, window: QWindow) -> bool:
        """Use the native restore command for DWM animation. 使用原生还原命令触发 DWM 动画。"""
        return self._request_system_command(
            window, SC_RESTORE, "requestRestore"
        )

    def _request_system_command(
        self, window: QWindow, command: int, operation: str
    ) -> bool:
        """Post one guarded system command. 投递一个受保护的系统命令。"""
        if sys.platform != "win32":
            return False
        try:
            hwnd = self._window_handle(window)
            if not hwnd:
                return False
            _post_system_command(hwnd, command)
            return True
        except Exception as exc:
            exception(
                f"NativeWindowHook.{operation} failed: "
                f"{type(exc).__name__}: {exc}"
            )
            return False

    def _attach_boundary(self, window: QWindow, operation: str) -> bool:
        """Run one public attach boundary. 执行公开 attach 异常边界。"""
        if sys.platform != "win32":
            return True
        try:
            return self._attach(window, apply_framechanged=True)
        except Exception as exc:
            exception(
                f"NativeWindowHook.{operation} failed: {type(exc).__name__}: {exc}"
            )
            return False

    @staticmethod
    def _window_handle(window: QWindow) -> int:
        """Return a validated native handle. 返回校验后的原生句柄。"""
        if not window:
            return 0
        return int(window.winId())

    def _owner_identity(self, window: QWindow) -> int:
        """Return stable C++ QObject identity across wrappers. 返回稳定底层对象标识。"""
        wrapper_id = id(window)
        try:
            pointers = shiboken6.getCppPointer(window)
        except TypeError:
            owner_key = wrapper_id
        except RuntimeError:
            owner_key = self._wrapper_owner_keys.get(wrapper_id, wrapper_id)
        else:
            if not pointers or not pointers[0]:
                raise RuntimeError("missing C++ QObject pointer")
            owner_key = int(pointers[0])
        return owner_key

    def _register_owner_wrapper(self, window: QWindow, owner_key: int) -> None:
        """Cache a wrapper only after a tracked generation exists. 仅登记已跟踪包装器。"""
        wrapper_id = id(window)
        self._wrapper_owner_keys[wrapper_id] = owner_key
        self._owner_wrapper_ids.setdefault(owner_key, set()).add(wrapper_id)

    def _connect_owner_generation(self, window: QWindow, owner_key: int) -> object:
        """Connect destroyed before committing generation state. 提交前连接析构。"""
        token = object()
        destroyed = getattr(window, "destroyed", None)
        if destroyed is None:
            raise RuntimeError("native owner has no destroyed signal")
        destroyed.connect(
            lambda *_args, key=owner_key, generation=token: self._release_owner(
                key, generation
            )
        )
        return token

    def _new_owner_generation(self, window: QWindow, owner_key: int) -> object:
        """Create one destroyed-guarded native generation. 创建析构保护代际。"""
        token = self._connect_owner_generation(window, owner_key)
        self._owner_generations[owner_key] = token
        self._owner_keys[token] = owner_key
        self._register_owner_wrapper(window, owner_key)
        return token

    def _discard_owner_identity(self, owner_key: int) -> None:
        """Clear wrapper caches after owner completion or rollback. 清理包装器标识缓存。"""
        for wrapper_id in self._owner_wrapper_ids.pop(owner_key, set()):
            if self._wrapper_owner_keys.get(wrapper_id) == owner_key:
                self._wrapper_owner_keys.pop(wrapper_id, None)

    def _owner_token(self, window: QWindow) -> object:
        """Return one generation token for a live owner. 返回活窗口代际令牌。"""
        owner_key = self._owner_identity(window)
        token = self._owner_generations.get(owner_key)
        if token is not None:
            self._register_owner_wrapper(window, owner_key)
            return token
        return self._new_owner_generation(window, owner_key)

    def _rotate_owner_generation(self, window: QWindow, owner_key: int) -> object:
        """Replace one native-handle generation. 切换原生句柄代际。"""
        previous = self._owner_generations.get(owner_key)
        token = self._connect_owner_generation(window, owner_key)
        if previous is not None:
            self._owner_keys.pop(previous, None)
            self._owner_hwnds.pop(previous, None)
            self._retired_owner_hwnds.pop(previous, None)
        self._owner_generations[owner_key] = token
        self._owner_keys[token] = owner_key
        self._register_owner_wrapper(window, owner_key)
        return token

    def _tracked_owner_token(self, window: QWindow) -> Optional[object]:
        """Return the current token only for the same live owner. 返回当前活对象令牌。"""
        owner_key = self._owner_identity(window)
        token = self._owner_generations.get(owner_key)
        if token is not None:
            self._register_owner_wrapper(window, owner_key)
        return token

    def _prepare_owner(self, window: QWindow, hwnd: int) -> bool:
        """Bind owner generation and invalidate stale HWND state. 绑定并清理旧代状态。"""
        owner_key = self._owner_identity(window)
        token = self._owner_token(window)
        retired_hwnd = self._retired_owner_hwnds.get(token)
        if retired_hwnd is not None:
            if retired_hwnd == hwnd:
                return False
            self._retired_owner_hwnds.pop(token, None)

        previous_hwnd = self._owner_hwnds.get(token)
        if previous_hwnd is not None and previous_hwnd != hwnd:
            self._forget_hwnd(previous_hwnd)
            token = self._rotate_owner_generation(window, owner_key)

        previous_owner = self._hwnd_owners.get(hwnd)
        if previous_owner is not None and previous_owner is not token:
            self._forget_hwnd(hwnd, retire_owner=True)

        self._owner_hwnds[token] = hwnd
        self._hwnd_owners[hwnd] = token
        return True

    def _release_owner(self, owner_key: int, token: object) -> None:
        """Forget only the matching generation. 仅清理匹配代际。"""
        if self._owner_generations.get(owner_key) is not token:
            return
        hwnd = self._owner_hwnds.get(token)
        if hwnd is not None and self._hwnd_owners.get(hwnd) is token:
            self._forget_hwnd(hwnd)
        self._retired_owner_hwnds.pop(token, None)
        self._owner_generations.pop(owner_key, None)
        self._owner_keys.pop(token, None)
        self._owner_hwnds.pop(token, None)
        self._discard_owner_identity(owner_key)

    def _forget_hwnd(self, hwnd: int, *, retire_owner: bool = False) -> None:
        """Drop stale native and owner state without calling WinAPI. 遗忘失效状态。"""
        token = self._hwnd_owners.pop(hwnd, None)
        if token is not None:
            self._owner_hwnds.pop(token, None)
            if retire_owner:
                self._retired_owner_hwnds[token] = hwnd
            elif self._retired_owner_hwnds.get(token) == hwnd:
                self._retired_owner_hwnds.pop(token, None)
        self._hwnds.discard(hwnd)
        self._framechanged_hwnds.discard(hwnd)
        self._restore_pending_hwnds.discard(hwnd)
        self._original_styles.pop(hwnd, None)

    def _attach(self, window: QWindow, apply_framechanged: bool) -> bool:
        """加 WS_CAPTION + 注册 hwnd 到 filter 集合。"""
        hwnd = self._window_handle(window)
        if not hwnd:
            return False
        if not self._prepare_owner(window, hwnd):
            return False
        if hwnd in self._restore_pending_hwnds:
            return self._reattach_restored(hwnd, apply_framechanged)
        if hwnd in self._hwnds:
            return not apply_framechanged or self._apply_framechanged(hwnd)
        observed_style = _get_window_style(hwnd)
        new_style = self._native_style(observed_style)
        previous_style = _set_window_style(hwnd, new_style)
        self._hwnds.add(hwnd)
        self._original_styles[hwnd] = previous_style
        if apply_framechanged and not self._apply_framechanged(hwnd):
            return False
        info(
            f"NativeWindowHook v4: attached hwnd={hwnd}, "
            f"style 0x{previous_style:08x} → 0x{new_style:08x}, "
            f"framechanged={apply_framechanged}"
        )
        return True

    def _reattach_restored(self, hwnd: int, apply_framechanged: bool) -> bool:
        """Repair a detach frame failure or reused HWND. 修复恢复待刷新或复用句柄。"""
        observed_style = _get_window_style(hwnd)
        new_style = self._native_style(observed_style)
        previous_style = _set_window_style(hwnd, new_style)
        self._original_styles[hwnd] = previous_style
        self._restore_pending_hwnds.discard(hwnd)
        self._framechanged_hwnds.discard(hwnd)
        return not apply_framechanged or self._apply_framechanged(hwnd)

    @staticmethod
    def _native_style(style: int) -> int:
        """Add all styles required by DWM animations. 添加 DWM 动画所需样式。"""
        return (
            style
            | WS_CAPTION
            | WS_THICKFRAME
            | WS_MINIMIZEBOX
            | WS_MAXIMIZEBOX
            | WS_SYSMENU
        )

    def _apply_framechanged(self, hwnd: int) -> bool:
        if hwnd in self._framechanged_hwnds:
            return True
        _request_frame_changed(hwnd)
        self._framechanged_hwnds.add(hwnd)
        return True

    @Slot(QWindow, result=bool)
    def detach(self, window: QWindow) -> bool:
        if sys.platform != "win32":
            return True
        try:
            token = self._tracked_owner_token(window)
            if token is None:
                return True
            hwnd = self._owner_hwnds.get(token)
            if hwnd is None:
                return True
            if hwnd not in self._hwnds:
                return True
            return self._detach(hwnd)
        except Exception as exc:
            exception(
                "NativeWindowHook.detach failed: "
                f"{type(exc).__name__}: {exc}"
            )
            return False

    def _detach(self, hwnd: int) -> bool:
        """Restore one tracked HWND and commit cleanup last. 恢复句柄并最后提交清理。"""
        try:
            if hwnd in self._restore_pending_hwnds:
                _request_frame_changed(hwnd)
                return self._commit_detach(hwnd)
            original_style = self._original_styles.get(hwnd)
            if original_style is None:
                raise RuntimeError(f"missing original style for hwnd={hwnd}")
            _set_window_style(hwnd, original_style)
            self._framechanged_hwnds.discard(hwnd)
            self._restore_pending_hwnds.add(hwnd)
            _request_frame_changed(hwnd)
            return self._commit_detach(hwnd)
        except OSError as exc:
            if exc.errno != ERROR_INVALID_WINDOW_HANDLE:
                raise
            self._forget_hwnd(hwnd)
            info(f"NativeWindowHook: discarded destroyed hwnd={hwnd}")
            return True

    def _commit_detach(self, hwnd: int) -> bool:
        """Clear state only after native restoration completes. 原生恢复完成后才清状态。"""
        self._forget_hwnd(hwnd)
        info(f"NativeWindowHook: detached hwnd={hwnd}")
        return True


_native_window_hook_singleton: Optional[NativeWindowHook] = None


def get_native_window_hook() -> NativeWindowHook:
    global _native_window_hook_singleton
    if _native_window_hook_singleton is None:
        _native_window_hook_singleton = NativeWindowHook()
    return _native_window_hook_singleton
