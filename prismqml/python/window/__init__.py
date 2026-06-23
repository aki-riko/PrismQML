# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""FluentQML Window - 窗口模块 Window module"""

# Windows: Set AppUserModelID at module import (earliest possible)
# Windows: 在模块导入时设置AppUserModelID（最早时机）
# 应用程序可在导入本模块前设置此变量以自定义 AppUserModelID
# Applications can set this variable before importing this module to customize AppUserModelID
import sys

APP_USER_MODEL_ID = "FluentQML.App"

if sys.platform == "win32":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)

from .fluent_window import (
    Window,
    WindowCore,
    WindowType,
    NavigationItem,
)
from .app import App
from .mica_window import (
    MicaManager,
    get_mica_manager,
    AcrylicHelper,
    AcrylicImageProvider,
    get_acrylic_helper,
)
from .system_tray import (
    SystemTrayIcon,
    MessageIcon,
    ActivationReason,
    createSystemTrayIcon,
)
from .native_window import (
    NativeWindowHook,
    get_native_window_hook,
)

__all__ = [
    "App",
    "Window",
    "WindowCore",
    "WindowType",
    "NavigationItem",
    # Mica/Acrylic
    "MicaManager",
    "get_mica_manager",
    "AcrylicHelper",
    "AcrylicImageProvider",
    "get_acrylic_helper",
    # SystemTray
    "SystemTrayIcon",
    "MessageIcon",
    "ActivationReason",
    "createSystemTrayIcon",
    # NativeWindow (Frameless + DWM 原生动画)
    "NativeWindowHook",
    "get_native_window_hook",
]
