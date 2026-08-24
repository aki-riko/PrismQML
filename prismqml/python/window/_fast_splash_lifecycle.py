# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Fast splash handoff and native ownership helpers. 快速启动页交接辅助。"""

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QTimer, Qt

from ..core.logger import info


def finish_embedded_handoff(controller) -> None:
    if (
        controller._closed
        or controller._handoff_done
        or controller._splash is None
        or controller._main_window is None
    ):
        return
    controller._handoff_done = True
    controller._splash.setFlag(Qt.WindowType.WindowTransparentForInput, True)
    controller._splash.setVisible(False)

    def activate_main() -> None:
        if controller._closed or controller._main_window is None:
            return
        info("FastSplash 自定义 Splash 已绘制, 交接主窗口")
        controller._main_window.raise_()
        controller._main_window.requestActivate()

    QTimer.singleShot(0, activate_main)


def finish_reveal(controller) -> None:
    if (
        controller._closed
        or controller._handoff_done
        or controller._splash is None
        or controller._main_window is None
    ):
        return
    splash = controller._splash
    gate = {"hidden_frame": False, "closed": False}

    def handoff() -> None:
        if controller._closed or controller._handoff_done or gate["closed"] or not gate["hidden_frame"]:
            return
        gate["closed"] = True
        controller._handoff_done = True
        try:
            splash.frameSwapped.disconnect(on_hidden_frame)
        except (AttributeError, RuntimeError, TypeError):
            pass
        splash.setFlag(Qt.WindowType.WindowTransparentForInput, True)
        splash.setVisible(False)

        def activate_main() -> None:
            if controller._closed or controller._main_window is None:
                return
            info("FastSplash 揭幕完成, 交接主窗口")
            controller._main_window.raise_()
            controller._main_window.requestActivate()

        QTimer.singleShot(0, activate_main)

    def on_hidden_frame() -> None:
        gate["hidden_frame"] = True
        handoff()

    splash.frameSwapped.connect(on_hidden_frame)
    splash.requestUpdate()

    def handoff_timeout() -> None:
        if gate["closed"]:
            return
        gate["hidden_frame"] = True
        handoff()

    QTimer.singleShot(250, handoff_timeout)


def bind_owner(splash, main) -> bool:
    splash.setTransientParent(main)
    if sys.platform != "win32":
        return splash.transientParent() == main
    splash_hwnd = int(splash.winId())
    main_hwnd = int(main.winId())
    if not splash_hwnd or not main_hwnd:
        return False
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    set_owner = user32.SetWindowLongPtrW
    set_owner.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    set_owner.restype = ctypes.c_ssize_t
    ctypes.set_last_error(0)
    set_owner(splash_hwnd, -8, main_hwnd)
    if ctypes.get_last_error():
        return False
    get_owner = user32.GetWindow
    get_owner.argtypes = [wintypes.HWND, wintypes.UINT]
    get_owner.restype = wintypes.HWND
    return int(get_owner(splash_hwnd, 4) or 0) == main_hwnd


def raise_owned_splash(splash, main) -> None:
    if sys.platform != "win32":
        splash.raise_()
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
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
    flags = 0x0001 | 0x0002 | 0x0010  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    set_window_pos(int(splash.winId()), wintypes.HWND(0), 0, 0, 0, 0, flags)


def close(controller) -> None:
    """Hide the retained QQuickWindow during application teardown."""
    controller._closed = True
    controller._handoff_done = True
    if controller._ready_timer is not None:
        controller._ready_timer.stop()
    if controller._main_window is not None:
        try:
            controller._main_window.frameSwapped.disconnect(controller._on_main_frame)
        except (AttributeError, RuntimeError, TypeError):
            pass
    if controller._splash is not None:
        try:
            controller._splash.frameSwapped.disconnect(controller._on_splash_frame)
            controller._splash.setVisible(False)
        except (AttributeError, RuntimeError, TypeError):
            pass
