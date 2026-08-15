# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML Core - 核心模块 Core module"""

from importlib import import_module as _import_module

__all__ = [
    # Theme
    "Theme",
    "Skin",
    "ThemeManager",
    # Shadow
    "ShadowManager",
    "installDwmSyncFilter",
    # Logger
    "Logger",
    "getLogger",
    "debug",
    "info",
    "warning",
    "error",
    "exception",
    "log_time",
    "install_qt_message_handler",
    # Utils
    "qml_path",
    "configure_qml_environment",
    "init_style",
    "EngineManager",
    "PrismIncubationController",
    "install_default_incubation_controller",
    "install_incubation_controller",
    # Single Instance
    "SingleInstance",
    "ensure_single_instance",
    # Updater
    "Updater",
    # Icons
    "Icon",
    "IconCore",
    "resolveIconColor",
    "make_icon",
    "make_theme_icon",
    "paint_icon",
    "IconProvider",
    "prepare_windows_icon",
    "nuitka_icon_options",
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
    "Theme": (".theme", "Theme"),
    "Skin": (".theme", "Skin"),
    "ThemeManager": (".theme", "ThemeManager"),
    # Shadow
    "ShadowManager": (".shadow", "ShadowManager"),
    "installDwmSyncFilter": (".shadow", "installDwmSyncFilter"),
    # Logger
    "Logger": (".logger", "Logger"),
    "getLogger": (".logger", "getLogger"),
    "debug": (".logger", "debug"),
    "info": (".logger", "info"),
    "warning": (".logger", "warning"),
    "error": (".logger", "error"),
    "exception": (".logger", "exception"),
    "log_time": (".logger", "log_time"),
    "install_qt_message_handler": (".logger", "install_qt_message_handler"),
    # Utils
    "qml_path": (".utils", "qml_path"),
    "configure_qml_environment": (".utils", "configure_qml_environment"),
    "init_style": (".utils", "init_style"),
    "EngineManager": (".engine", "EngineManager"),
    "PrismIncubationController": (".incubation", "PrismIncubationController"),
    "install_default_incubation_controller": (
        ".incubation", "install_default_incubation_controller"
    ),
    "install_incubation_controller": (".incubation", "install_incubation_controller"),
    # Single Instance
    "SingleInstance": (".single_instance", "SingleInstance"),
    "ensure_single_instance": (".single_instance", "ensure_single_instance"),
    # Updater
    "Updater": (".updater", "Updater"),
    # Icons
    "Icon": (".icons", "Icon"),
    "IconCore": (".icon_core", "IconCore"),
    "resolveIconColor": (".icon_core", "resolveIconColor"),
    "make_icon": (".icon_core", "make_icon"),
    "make_theme_icon": (".icon_core", "make_theme_icon"),
    "paint_icon": (".icon_core", "paint_icon"),
    "IconProvider": (".icon_provider", "IconProvider"),
    "prepare_windows_icon": (".application_icon", "prepare_windows_icon"),
    "nuitka_icon_options": (".application_icon", "nuitka_icon_options"),
    # Background tasks
    "PoolSubmitPolicy": (".task_runner", "PoolSubmitPolicy"),
    "PoolTaskOptions": (".task_runner", "PoolTaskOptions"),
    "TaskCancelledError": (".task_runner", "TaskCancelledError"),
    "TaskContext": (".task_runner", "TaskContext"),
    "TaskFailure": (".task_runner", "TaskFailure"),
    "TaskHandle": (".task_runner", "TaskHandle"),
    "TaskRejectedError": (".task_runner", "TaskRejectedError"),
    "TaskShutdownReport": (".task_runner", "TaskShutdownReport"),
    "TaskShutdownTimeoutError": (
        ".task_runner",
        "TaskShutdownTimeoutError",
    ),
    "TaskState": (".task_runner", "TaskState"),
    "TaskThreadPool": (".task_runner", "TaskThreadPool"),
    "current_task": (".task_runner", "current_task"),
    "global_task_pool": (".task_runner", "global_task_pool"),
    "run_in_pool": (".task_runner", "run_in_pool"),
    "run_in_thread": (".task_runner", "run_in_thread"),
    "shutdown_tasks": (".task_runner", "shutdown_tasks"),
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
