# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML - A QML-based Fluent Design component library"""

from importlib import import_module as _import_module

try:
    from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
    from importlib.metadata import version as _get_version

    __version__ = _get_version("prismqml")  # PyPI 分发名为 prismqml
except _PackageNotFoundError:
    __version__ = "0.3.1.45"  # 回退值：开发模式或未安装时
__author__ = "aki-riko"

__all__ = [
    # Theme
    "Theme",
    "Skin",
    "setTheme",
    "getTheme",
    "setSkin",
    "getSkin",
    "isDark",
    "setAccentColor",
    "getAccentColor",
    "accentQColor",
    "getThemeManager",
    # Icons
    "Icon",
    "IconCore",
    "resolveIconColor",
    "make_icon",
    "make_theme_icon",
    "paint_icon",
    "IconProvider",
    "register_icon_provider",
    "get_icon_provider",
    # Shadow
    "ShadowManager",
    "getShadowManager",
    "installDwmSyncFilter",
    # Single Instance
    "SingleInstance",
    "Updater",
    # Window
    "App",
    "Window",
    "WindowCloseEvent",
    "WindowCore",
    "WindowType",
    "NavigationItem",
    "AsyncQmlPage",
    # Logger
    "Logger",
    "getLogger",
    "debug",
    "info",
    "warning",
    "error",
    "exception",
    # Utils
    "qml_path",
    "configure_qml_environment",
    "register_types",
    "init_style",
    # State
    "Store",
    # QRCode
    "QRCodeGenerator",
    "QRCodeImageProvider",
    "get_qrcode_generator",
    "get_qrcode_provider",
    # Mica & Acrylic
    "MicaManager",
    "get_mica_manager",
    "AcrylicHelper",
    "AcrylicImageProvider",
    "get_acrylic_helper",
    # Screen Eyedropper
    "ScreenEyedropperManager",
    "get_screen_eyedropper_manager",
    # Clipboard
    "ClipboardHelper",
    "get_clipboard_helper",
    # SVG
    "SvgImageProvider",
    "get_svg_provider",
    # SystemTray
    "SystemTrayIcon",
    "MessageIcon",
    "ActivationReason",
    "createSystemTrayIcon",
    # Models
    "TableListModel",
    "SqlListModel",
    "DbRouter",
    "is_rust_accelerated",
    # Background tasks
    "PoolSubmitPolicy",
    "PoolTaskOptions",
    "TaskCancelledError",
    "TaskContext",
    "TaskFailure",
    "TaskHandle",
    "TaskRejectedError",
    "TaskShutdownReport",
    "TaskShutdownTimeoutError",
    "TaskState",
    "TaskThreadPool",
    "current_task",
    "global_task_pool",
    "run_in_pool",
    "run_in_thread",
    "shutdown_tasks",
]

_LAZY_EXPORTS = {
    # Theme
    "Theme": (".python.core.theme", "Theme"),
    "Skin": (".python.core.theme", "Skin"),
    "setTheme": (".python.core.theme", "setTheme"),
    "getTheme": (".python.core.theme", "getTheme"),
    "setSkin": (".python.core.theme", "setSkin"),
    "getSkin": (".python.core.theme", "getSkin"),
    "isDark": (".python.core.theme", "isDark"),
    "setAccentColor": (".python.core.theme", "setAccentColor"),
    "getAccentColor": (".python.core.theme", "getAccentColor"),
    "accentQColor": (".python.core.theme", "accentQColor"),
    "getThemeManager": (".python.core.theme", "getThemeManager"),
    # Icons
    "Icon": (".python.core.icons", "Icon"),
    "IconCore": (".python.core.icon_core", "IconCore"),
    "resolveIconColor": (".python.core.icon_core", "resolveIconColor"),
    "make_icon": (".python.core.icon_core", "make_icon"),
    "make_theme_icon": (".python.core.icon_core", "make_theme_icon"),
    "paint_icon": (".python.core.icon_core", "paint_icon"),
    "IconProvider": (".python.core.icon_provider", "IconProvider"),
    "register_icon_provider": (".python.core.icon_provider", "register_icon_provider"),
    "get_icon_provider": (".python.core.icon_provider", "get_icon_provider"),
    # Shadow
    "ShadowManager": (".python.core.shadow", "ShadowManager"),
    "getShadowManager": (".python.core.shadow", "getShadowManager"),
    "installDwmSyncFilter": (".python.core.shadow", "installDwmSyncFilter"),
    # Single Instance / Updater
    "SingleInstance": (".python.core.single_instance", "SingleInstance"),
    "Updater": (".python.core.updater", "Updater"),
    # Window
    "App": (".python.window.app", "App"),
    "Window": (".python.window.fluent_window", "Window"),
    "WindowCloseEvent": (".python.window.window_core", "WindowCloseEvent"),
    "WindowCore": (".python.window.window_core", "WindowCore"),
    "WindowType": (".python.window.window_core", "WindowType"),
    "NavigationItem": (".python.window.window_core", "NavigationItem"),
    "AsyncQmlPage": (".python.window.async_qml_page", "AsyncQmlPage"),
    # Logger
    "Logger": (".python.core.logger", "Logger"),
    "getLogger": (".python.core.logger", "getLogger"),
    "debug": (".python.core.logger", "debug"),
    "info": (".python.core.logger", "info"),
    "warning": (".python.core.logger", "warning"),
    "error": (".python.core.logger", "error"),
    "exception": (".python.core.logger", "exception"),
    # Utils
    "qml_path": (".python.core.utils", "qml_path"),
    "configure_qml_environment": (
        ".python.core.utils",
        "configure_qml_environment",
    ),
    "register_types": (".python.core.utils", "register_types"),
    "init_style": (".python.core.utils", "init_style"),
    # State
    "Store": (".python.state.store", "Store"),
    # QRCode
    "QRCodeGenerator": (".python.providers.qrcode_generator", "QRCodeGenerator"),
    "QRCodeImageProvider": (".python.providers.qrcode_generator", "QRCodeImageProvider"),
    "get_qrcode_generator": (".python.providers.qrcode_generator", "get_qrcode_generator"),
    "get_qrcode_provider": (".python.providers.qrcode_generator", "get_qrcode_provider"),
    # Mica & Acrylic
    "MicaManager": (".python.window.mica_window", "MicaManager"),
    "get_mica_manager": (".python.window.mica_window", "get_mica_manager"),
    "AcrylicHelper": (".python.window.mica_window", "AcrylicHelper"),
    "AcrylicImageProvider": (".python.window.mica_window", "AcrylicImageProvider"),
    "get_acrylic_helper": (".python.window.mica_window", "get_acrylic_helper"),
    # Screen Eyedropper
    "ScreenEyedropperManager": (".python.providers.screen_eyedropper", "ScreenEyedropperManager"),
    "get_screen_eyedropper_manager": (".python.providers.screen_eyedropper", "get_screen_eyedropper_manager"),
    # Clipboard
    "ClipboardHelper": (".python.providers.clipboard", "ClipboardHelper"),
    "get_clipboard_helper": (".python.providers.clipboard", "get_clipboard_helper"),
    # SVG
    "SvgImageProvider": (".python.providers.svg_provider", "SvgImageProvider"),
    "get_svg_provider": (".python.providers.svg_provider", "get_svg_provider"),
    # SystemTray
    "SystemTrayIcon": (".python.window.system_tray", "SystemTrayIcon"),
    "MessageIcon": (".python.window.system_tray", "MessageIcon"),
    "ActivationReason": (".python.window.system_tray", "ActivationReason"),
    "createSystemTrayIcon": (".python.window.system_tray", "createSystemTrayIcon"),
    # Models
    "TableListModel": (".python.models.table_models", "TableListModel"),
    "SqlListModel": (".python.models.sql_list_model", "SqlListModel"),
    "DbRouter": (".python.models.sql_list_model", "DbRouter"),
    "is_rust_accelerated": (".python.models.sql_list_model", "is_rust_accelerated"),
    # Background tasks
    "PoolSubmitPolicy": (".python.core.task_runner", "PoolSubmitPolicy"),
    "PoolTaskOptions": (".python.core.task_runner", "PoolTaskOptions"),
    "TaskCancelledError": (".python.core.task_runner", "TaskCancelledError"),
    "TaskContext": (".python.core.task_runner", "TaskContext"),
    "TaskFailure": (".python.core.task_runner", "TaskFailure"),
    "TaskHandle": (".python.core.task_runner", "TaskHandle"),
    "TaskRejectedError": (".python.core.task_runner", "TaskRejectedError"),
    "TaskShutdownReport": (".python.core.task_runner", "TaskShutdownReport"),
    "TaskShutdownTimeoutError": (
        ".python.core.task_runner",
        "TaskShutdownTimeoutError",
    ),
    "TaskState": (".python.core.task_runner", "TaskState"),
    "TaskThreadPool": (".python.core.task_runner", "TaskThreadPool"),
    "current_task": (".python.core.task_runner", "current_task"),
    "global_task_pool": (".python.core.task_runner", "global_task_pool"),
    "run_in_pool": (".python.core.task_runner", "run_in_pool"),
    "run_in_thread": (".python.core.task_runner", "run_in_thread"),
    "shutdown_tasks": (".python.core.task_runner", "shutdown_tasks"),
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
