# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Win32 popup owner repair helpers. Win32 弹层 owner 修复辅助。"""

import ctypes
import os
import sys
from typing import Optional

from .logger import debug


_GW_OWNER = 4
_GWLP_HWNDPARENT = -8
_HWND_TOP = 0
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOACTIVATE = 0x0010
_SWP_NOOWNERZORDER = 0x0200
_KEY_DOWN_MASK = 0x8000
_VK_MOUSE_BUTTONS = (0x01, 0x02, 0x04, 0x05, 0x06)
_POPUP_RAISE_FLAGS = (
    _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOACTIVATE | _SWP_NOOWNERZORDER
)


def _bind_user32_function(user32, name: str, argtypes, restype):
    """Bind one typed user32 function. 绑定一个带类型的 user32 函数。"""
    function = getattr(user32, name)
    function.argtypes = argtypes
    function.restype = restype
    return function


class _WindowsPopupOwnerApi:
    """Pointer-width Win32 calls used by the popup owner repair. 弹层修复所需 Win32 调用。"""

    def __init__(self) -> None:
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        bind = _bind_user32_function
        self._get_window = bind(
            user32, "GetWindow", [wintypes.HWND, wintypes.UINT], wintypes.HWND
        )
        self._get_window_process_id = bind(
            user32, "GetWindowThreadProcessId",
            [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD,
        )
        self._get_capture = bind(user32, "GetCapture", [], wintypes.HWND)
        self._get_async_key_state = bind(
            user32, "GetAsyncKeyState", [ctypes.c_int], ctypes.c_short
        )
        self._release_capture = bind(user32, "ReleaseCapture", [], wintypes.BOOL)
        self._set_window_owner = bind(
            user32, "SetWindowLongPtrW",
            [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t], ctypes.c_ssize_t,
        )
        self._set_window_pos = bind(
            user32, "SetWindowPos",
            [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
             ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.BOOL,
        )

    def process_id(self, hwnd: int) -> int:
        """Return the process owning one HWND. 返回 HWND 所属进程。"""
        from ctypes import wintypes

        process_id = wintypes.DWORD()
        thread_id = self._get_window_process_id(hwnd, ctypes.byref(process_id))
        return int(process_id.value) if thread_id else 0

    def owner(self, hwnd: int) -> int:
        """Return the current native owner. 返回当前原生 owner。"""
        return int(self._get_window(hwnd, _GW_OWNER) or 0)

    def capture(self) -> int:
        """Return the HWND holding mouse capture. 返回持有鼠标捕获的 HWND。"""
        return int(self._get_capture() or 0)

    def mouse_button_down(self) -> bool:
        """Return whether any physical mouse button is down. 返回是否有物理鼠标键按下。"""
        return any(
            int(self._get_async_key_state(button)) & _KEY_DOWN_MASK
            for button in _VK_MOUSE_BUTTONS
        )

    def release_capture(self) -> bool:
        """Release capture owned by the calling UI thread. 释放当前 UI 线程持有的捕获。"""
        return bool(self._release_capture())

    def set_owner(self, popup_hwnd: int, owner_hwnd: int) -> bool:
        """Assign a top-level owner with zero-return error handling. 设置顶层窗口 owner。"""
        ctypes.set_last_error(0)
        previous = self._set_window_owner(
            popup_hwnd,
            _GWLP_HWNDPARENT,
            owner_hwnd,
        )
        return bool(previous or ctypes.get_last_error() == 0)

    def raise_popup(self, popup_hwnd: int) -> bool:
        """Raise without activating or reordering the owner. 无激活抬升且不改变 owner 顺序。"""
        return bool(
            self._set_window_pos(
                popup_hwnd,
                _HWND_TOP,
                0,
                0,
                0,
                0,
                _POPUP_RAISE_FLAGS,
            )
        )


_popup_owner_api: Optional[_WindowsPopupOwnerApi] = None


def _ensure_popup_owner_with_api(
    api,
    popup_hwnd: int,
    owner_hwnd: int,
    expected_process_id: int,
) -> bool:
    """Validate, repair, verify, then raise one popup. 校验、修复、复验并抬升弹层。"""
    if not popup_hwnd or not owner_hwnd or popup_hwnd == owner_hwnd:
        return False
    if (
        api.process_id(popup_hwnd) != expected_process_id
        or api.process_id(owner_hwnd) != expected_process_id
    ):
        return False
    if api.owner(popup_hwnd) != owner_hwnd:
        if not api.set_owner(popup_hwnd, owner_hwnd):
            return False
        if api.owner(popup_hwnd) != owner_hwnd:
            return False
    return api.raise_popup(popup_hwnd)


def _clear_popup_owner_with_api(
    api,
    popup_hwnd: int,
    owner_hwnd: int,
    expected_process_id: int,
) -> bool:
    """Clear one matching same-process popup owner. 清除匹配的同进程弹层 owner。"""
    if not popup_hwnd or not owner_hwnd or popup_hwnd == owner_hwnd:
        return False
    if (
        api.process_id(popup_hwnd) != expected_process_id
        or api.process_id(owner_hwnd) != expected_process_id
    ):
        return False
    current_owner = api.owner(popup_hwnd)
    if not current_owner:
        return True
    if current_owner != owner_hwnd:
        return False
    if not api.set_owner(popup_hwnd, 0):
        return False
    return api.owner(popup_hwnd) == 0


def _release_stale_popup_capture_with_api(
    api,
    popup_hwnd: int,
    owner_hwnd: int,
    expected_process_id: int,
) -> bool:
    """Release an idle owner capture blocking its popup. 释放阻塞弹层的空闲宿主捕获。"""
    if not popup_hwnd or not owner_hwnd or popup_hwnd == owner_hwnd:
        return False
    if (
        api.process_id(popup_hwnd) != expected_process_id
        or api.process_id(owner_hwnd) != expected_process_id
        or api.owner(popup_hwnd) != owner_hwnd
        or api.capture() != owner_hwnd
        or api.mouse_button_down()
    ):
        return False
    if not api.release_capture():
        return False
    return api.capture() == 0


def ensure_popup_window_owner(popup_hwnd: int, owner_hwnd: int) -> bool:
    """Repair a same-process popup owner on Windows. 修复 Windows 同进程弹层 owner。"""
    if sys.platform != "win32":
        return False
    global _popup_owner_api
    try:
        if _popup_owner_api is None:
            _popup_owner_api = _WindowsPopupOwnerApi()
        return _ensure_popup_owner_with_api(
            _popup_owner_api,
            popup_hwnd,
            owner_hwnd,
            os.getpid(),
        )
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        debug(f"Win32弹层 owner 修复不可用: {exc}")
        return False


def clear_popup_window_owner(popup_hwnd: int, owner_hwnd: int) -> bool:
    """Clear a matching popup owner on Windows. 清除 Windows 弹层的匹配 owner。"""
    if sys.platform != "win32":
        return False
    global _popup_owner_api
    try:
        if _popup_owner_api is None:
            _popup_owner_api = _WindowsPopupOwnerApi()
        return _clear_popup_owner_with_api(
            _popup_owner_api,
            popup_hwnd,
            owner_hwnd,
            os.getpid(),
        )
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        debug(f"Win32弹层 owner 清理不可用: {exc}")
        return False


def release_stale_popup_capture(popup_hwnd: int, owner_hwnd: int) -> bool:
    """Release a stale owner capture after a Qt popup opens. 释放 Qt 弹层打开后的陈旧宿主捕获。"""
    if sys.platform != "win32":
        return False
    global _popup_owner_api
    try:
        if _popup_owner_api is None:
            _popup_owner_api = _WindowsPopupOwnerApi()
        return _release_stale_popup_capture_with_api(
            _popup_owner_api,
            popup_hwnd,
            owner_hwnd,
            os.getpid(),
        )
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        debug(f"Win32弹层鼠标捕获释放不可用: {exc}")
        return False
