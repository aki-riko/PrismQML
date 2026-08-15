# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML runtime composition. PrismQML 运行时装配。"""

from importlib import import_module as _import_module

__all__ = [
    "register_types",
    "register_icon_provider",
    "enable_auto_update",
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
    "enable_auto_update": (".auto_update", "enable_auto_update"),
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
