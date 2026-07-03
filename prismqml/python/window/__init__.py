# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""PrismQML Window - 窗口模块 Window module"""

# Windows: Set AppUserModelID at module import (earliest possible)
# Windows: 在模块导入时设置 AppUserModelID(最早时机)
#
# AUMID 决定 Windows 任务栏如何分组窗口。多个基于 PrismQML 的应用若共用同一
# AUMID,会被任务栏合并成一个图标组。因此按以下优先级派生唯一 AUMID:
#   1) 环境变量 PRISMQML_APP_USER_MODEL_ID(应用显式指定,最高优先)
#   2) 由可执行文件名派生(打包态:Gitora.exe -> "PrismQML.Gitora",自动区分)
#   3) 回退默认 "PrismQML.App"(开发态裸跑 python.exe 时)
#
# AUMID determines how the Windows taskbar groups windows. Multiple PrismQML-based
# apps sharing one AUMID get merged into a single taskbar icon group. We derive a
# unique AUMID by the priority above.
from importlib import import_module as _import_module
import os
import sys


def _derive_app_user_model_id() -> str:
    explicit = os.environ.get("PRISMQML_APP_USER_MODEL_ID")
    if explicit:
        return explicit
    try:
        exe = os.path.basename(sys.executable or "")
        stem = os.path.splitext(exe)[0]
        # 裸跑解释器(python/pythonw/py)无法区分应用,落到默认值
        if stem and stem.lower() not in ("python", "pythonw", "py"):
            return "PrismQML." + stem
    except Exception:
        pass
    return "PrismQML.App"


APP_USER_MODEL_ID = _derive_app_user_model_id()

if sys.platform == "win32":
    import ctypes

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        # 设置失败不应阻断应用启动,仅放弃任务栏分组定制
        pass

__all__ = [
    "App",
    "Window",
    "WindowCloseEvent",
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

_LAZY_EXPORTS = {
    "App": (".app", "App"),
    "Window": (".fluent_window", "Window"),
    "WindowCloseEvent": (".window_base", "WindowCloseEvent"),
    "WindowCore": (".window_base", "WindowCore"),
    "WindowType": (".window_base", "WindowType"),
    "NavigationItem": (".window_base", "NavigationItem"),
    # Mica/Acrylic
    "MicaManager": (".mica_window", "MicaManager"),
    "get_mica_manager": (".mica_window", "get_mica_manager"),
    "AcrylicHelper": (".mica_window", "AcrylicHelper"),
    "AcrylicImageProvider": (".mica_window", "AcrylicImageProvider"),
    "get_acrylic_helper": (".mica_window", "get_acrylic_helper"),
    # SystemTray
    "SystemTrayIcon": (".system_tray", "SystemTrayIcon"),
    "MessageIcon": (".system_tray", "MessageIcon"),
    "ActivationReason": (".system_tray", "ActivationReason"),
    "createSystemTrayIcon": (".system_tray", "createSystemTrayIcon"),
    # NativeWindow
    "NativeWindowHook": (".native_window", "NativeWindowHook"),
    "get_native_window_hook": (".native_window", "get_native_window_hook"),
}


def __getattr__(name):
    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(_import_module(module_name, __name__), attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
