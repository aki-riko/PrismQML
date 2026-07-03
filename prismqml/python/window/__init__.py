# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PrismQML Window - 窗口模块 Window module"""

# Windows: Set AppUserModelID at module import (earliest possible)
# Windows: 在模块导入时设置 AppUserModelID(最早时机)
#
# AUMID 决定 Windows 任务栏如何分组窗口。多个基于 PrismQML 的应用若共用同一
# AUMID,会被任务栏合并成一个图标组。因此按以下优先级派生唯一 AUMID:
#   1) 环境变量 PRISMQML_APP_USER_MODEL_ID(应用显式指定,最高优先)
#   2) 由可执行文件名派生(打包态:Gitora.exe -> "PrismQML.Gitora",自动区分)
#   3) 由入口脚本路径派生(开发态裸跑 python.exe 时仍可自动区分)
#   4) 回退默认 "PrismQML.App"(交互式/无入口脚本)
#
# AUMID determines how the Windows taskbar groups windows. Multiple PrismQML-based
# apps sharing one AUMID get merged into a single taskbar icon group. We derive a
# unique AUMID by the priority above.
import hashlib
import os
import re
import sys
from typing import Mapping, Optional


_APP_USER_MODEL_ID_PREFIX = "PrismQML"
_DEFAULT_APP_USER_MODEL_ID = f"{_APP_USER_MODEL_ID_PREFIX}.App"
_HOST_EXECUTABLE_STEMS = {"python", "pythonw", "py"}
_MAX_APP_USER_MODEL_ID_LENGTH = 128
_AUTO_ID_HASH_LENGTH = 10


def _sanitize_app_user_model_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value)


def _path_hash(path: str) -> str:
    normalized = os.path.normcase(os.path.abspath(path))
    digest = hashlib.sha1(normalized.encode("utf-8", "surrogatepass")).hexdigest()
    return digest[:_AUTO_ID_HASH_LENGTH]


def _make_app_user_model_id(
    *parts: str, identity_path: Optional[str] = None
) -> str:
    clean_parts = [_sanitize_app_user_model_part(part) for part in parts if part]
    clean_parts = [part for part in clean_parts if part]
    if not clean_parts:
        clean_parts = ["App"]
    if identity_path:
        clean_parts.append(_path_hash(identity_path))

    app_id = ".".join([_APP_USER_MODEL_ID_PREFIX, *clean_parts])
    if len(app_id) <= _MAX_APP_USER_MODEL_ID_LENGTH:
        return app_id

    digest = clean_parts[-1] if identity_path else ""
    suffix_length = len(digest) + (1 if digest else 0)
    prefix_length = len(_APP_USER_MODEL_ID_PREFIX) + 1
    available = _MAX_APP_USER_MODEL_ID_LENGTH - prefix_length - suffix_length
    collapsed = _sanitize_app_user_model_part("".join(clean_parts[:-1]))
    collapsed = (collapsed or "App")[: max(1, available)]

    if digest:
        return f"{_APP_USER_MODEL_ID_PREFIX}.{collapsed}.{digest}"
    return f"{_APP_USER_MODEL_ID_PREFIX}.{collapsed}"[:_MAX_APP_USER_MODEL_ID_LENGTH]


def _derive_script_app_user_model_id(argv0: str) -> Optional[str]:
    if not argv0 or argv0 == "-c":
        return None

    script_path = os.path.abspath(argv0)
    script_stem = os.path.splitext(os.path.basename(script_path))[0]
    parent_stem = os.path.basename(os.path.dirname(script_path))
    parts = [parent_stem]
    if script_stem != "__main__":
        parts.append(script_stem)

    if not any(_sanitize_app_user_model_part(part) for part in parts):
        return None
    return _make_app_user_model_id(*parts, identity_path=script_path)


def _derive_app_user_model_id(
    executable: Optional[str] = None,
    argv0: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    env = os.environ if environ is None else environ
    explicit = env.get("PRISMQML_APP_USER_MODEL_ID")
    if explicit:
        return explicit

    try:
        executable = sys.executable if executable is None else executable
        exe = os.path.basename(executable or "")
        stem = os.path.splitext(exe)[0]
        # Packaged apps can usually be separated by their executable name.
        # 打包应用通常可由可执行文件名区分。
        if stem and stem.lower() not in _HOST_EXECUTABLE_STEMS:
            return _make_app_user_model_id(stem)
    except (OSError, TypeError, ValueError) as e:
        from ..core.logger import debug

        debug(f"Failed to derive AppUserModelID from executable: {e}")

    try:
        if argv0 is None:
            argv0 = sys.argv[0] if sys.argv else ""
        script_app_id = _derive_script_app_user_model_id(argv0)
        if script_app_id:
            return script_app_id
    except (OSError, TypeError, ValueError) as e:
        from ..core.logger import debug

        debug(f"Failed to derive AppUserModelID from script path: {e}")

    return _DEFAULT_APP_USER_MODEL_ID


def _apply_app_user_model_id(app_user_model_id: str) -> bool:
    if sys.platform != "win32":
        return False

    import ctypes

    try:
        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            app_user_model_id
        )
        if result != 0:
            from ..core.logger import debug

            debug(
                "SetCurrentProcessExplicitAppUserModelID returned "
                f"HRESULT 0x{result & 0xFFFFFFFF:08X}"
            )
            return False
        return True
    except (AttributeError, OSError) as e:
        from ..core.logger import debug

        debug(f"SetCurrentProcessExplicitAppUserModelID failed: {e}")
        return False


APP_USER_MODEL_ID = _derive_app_user_model_id()
_apply_app_user_model_id(APP_USER_MODEL_ID)

from .fluent_window import (
    Window,
    WindowCloseEvent,
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
