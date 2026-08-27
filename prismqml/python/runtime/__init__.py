# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML runtime composition. PrismQML 运行时装配。"""

from importlib import import_module as _import_module

__all__ = [
    "register_types",
    "register_icon_provider",
    "get_icon_provider",
    "enable_auto_update",
    "get_config_manager",
    "get_qrcode_generator",
    "get_qrcode_provider",
    "get_screen_eyedropper_manager",
    "get_svg_provider",
    "create_qml_engine",
    "publish_qml_engine",
    "is_published_qml_engine",
    "get_published_qml_engine",
    "register_qml_engine_binding",
    "release_qml_engine_bindings",
    "reset_qml_engine",
    "get_or_create_qml_engine",
    "configure_application_engine",
    "register_startup_window_context",
    "prepare_application_environment",
    "create_qt_application",
    "install_application_input_filter",
    "install_application_dwm_filter",
    "installDwmSyncFilter",
    "reset_application_input_filter",
    "reset_application_dwm_filter",
    "prepare_window_engine",
    "register_fast_splash_context",
    "getShadowManager",
    "get_window_helper",
    "get_mica_manager",
    "get_acrylic_helper",
    "get_native_window_hook",
    "get_clipboard_helper",
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
    "register_types": (".registry", "register_types"),
    "register_icon_provider": (".icon_registry", "register_icon_provider"),
    "get_icon_provider": (".icon_registry", "get_icon_provider"),
    "enable_auto_update": (".auto_update", "enable_auto_update"),
    "get_config_manager": (".configuration", "get_config_manager"),
    "get_qrcode_generator": (".provider_services", "get_qrcode_generator"),
    "get_qrcode_provider": (".provider_services", "get_qrcode_provider"),
    "get_screen_eyedropper_manager": (
        ".provider_services",
        "get_screen_eyedropper_manager",
    ),
    "get_svg_provider": (".provider_services", "get_svg_provider"),
    "create_qml_engine": (".engine", "create_qml_engine"),
    "publish_qml_engine": (".engine", "publish_qml_engine"),
    "is_published_qml_engine": (".engine", "is_published_qml_engine"),
    "get_published_qml_engine": (".engine", "get_published_qml_engine"),
    "register_qml_engine_binding": (
        ".engine",
        "register_qml_engine_binding",
    ),
    "release_qml_engine_bindings": (
        ".engine",
        "release_qml_engine_bindings",
    ),
    "reset_qml_engine": (".engine", "reset_qml_engine"),
    "get_or_create_qml_engine": (".engine", "get_or_create_qml_engine"),
    "configure_application_engine": (
        ".engine",
        "configure_application_engine",
    ),
    "register_startup_window_context": (
        ".engine",
        "register_startup_window_context",
    ),
    "prepare_application_environment": (
        ".application",
        "prepare_application_environment",
    ),
    "create_qt_application": (".application", "create_qt_application"),
    "install_application_input_filter": (
        ".application",
        "install_application_input_filter",
    ),
    "install_application_dwm_filter": (
        ".application",
        "install_application_dwm_filter",
    ),
    "installDwmSyncFilter": (".application", "installDwmSyncFilter"),
    "reset_application_input_filter": (
        ".application",
        "reset_application_input_filter",
    ),
    "reset_application_dwm_filter": (
        ".application",
        "reset_application_dwm_filter",
    ),
    "prepare_window_engine": (".window_registry", "prepare_window_engine"),
    "register_fast_splash_context": (".fast_splash_context", "register_fast_splash_context"),
    "getShadowManager": (".window_services", "getShadowManager"),
    "get_window_helper": (".window_services", "get_window_helper"),
    "get_mica_manager": (".window_services", "get_mica_manager"),
    "get_acrylic_helper": (".window_services", "get_acrylic_helper"),
    "get_native_window_hook": (".window_services", "get_native_window_hook"),
    "get_clipboard_helper": (".window_services", "get_clipboard_helper"),
    "NotificationPosition": (".notification", "Position"),
    "NotificationSeverity": (".notification", "Severity"),
    "showDesktopNotification": (".notification", "showDesktopNotification"),
    "showDesktopInfo": (".notification", "showDesktopInfo"),
    "showDesktopSuccess": (".notification", "showDesktopSuccess"),
    "showDesktopWarning": (".notification", "showDesktopWarning"),
    "showDesktopError": (".notification", "showDesktopError"),
    "showDesktopInfoBar": (".notification", "showDesktopInfoBar"),
    "closeAllDesktopNotifications": (
        ".notification",
        "closeAllDesktopNotifications",
    ),
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
