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
    "setTheme",
    "getTheme",
    "setSkin",
    "getSkin",
    "isDark",
    "setAccentColor",
    "getAccentColor",
    "accentQColor",
    "getThemeManager",
    # Shadow
    "ShadowManager",
    "getShadowManager",
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
    "register_types",
    "init_style",
    "EngineManager",
    "PrismIncubationController",
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
    "register_icon_provider",
    "get_icon_provider",
    # Notification (Python helper, 不需要业务方手撸 NotificationBridge.qml 胶水)
    "NotificationPosition",
    "NotificationSeverity",
    "showDesktopNotification",
    "showDesktopInfo",
    "showDesktopSuccess",
    "showDesktopWarning",
    "showDesktopError",
    "showDesktopInfoBar",
    "closeAllDesktopNotifications",
]

_LAZY_EXPORTS = {
    # Theme
    "Theme": (".theme", "Theme"),
    "Skin": (".theme", "Skin"),
    "ThemeManager": (".theme", "ThemeManager"),
    "setTheme": (".theme", "setTheme"),
    "getTheme": (".theme", "getTheme"),
    "setSkin": (".theme", "setSkin"),
    "getSkin": (".theme", "getSkin"),
    "isDark": (".theme", "isDark"),
    "setAccentColor": (".theme", "setAccentColor"),
    "getAccentColor": (".theme", "getAccentColor"),
    "accentQColor": (".theme", "accentQColor"),
    "getThemeManager": (".theme", "getThemeManager"),
    # Shadow
    "ShadowManager": (".shadow", "ShadowManager"),
    "getShadowManager": (".shadow", "getShadowManager"),
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
    "register_types": (".utils", "register_types"),
    "init_style": (".utils", "init_style"),
    "EngineManager": (".engine", "EngineManager"),
    "PrismIncubationController": (".incubation", "PrismIncubationController"),
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
    "register_icon_provider": (".icon_provider", "register_icon_provider"),
    "get_icon_provider": (".icon_provider", "get_icon_provider"),
    # Notification
    "NotificationPosition": (".notification", "Position"),
    "NotificationSeverity": (".notification", "Severity"),
    "showDesktopNotification": (".notification", "showDesktopNotification"),
    "showDesktopInfo": (".notification", "showDesktopInfo"),
    "showDesktopSuccess": (".notification", "showDesktopSuccess"),
    "showDesktopWarning": (".notification", "showDesktopWarning"),
    "showDesktopError": (".notification", "showDesktopError"),
    "showDesktopInfoBar": (".notification", "showDesktopInfoBar"),
    "closeAllDesktopNotifications": (".notification", "closeAllDesktopNotifications"),
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
