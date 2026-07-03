# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""配置子系统 — 入口模块

模块结构 Module Structure:
- validators.py     : Validator + ValidationKind
- config_item.py    : SettingEntry / RangedEntry / EnumEntry
- settings_base.py  : SettingsCore (持久化容器基类)
- app_config.py     : AppConfig (PrismQML 自带的应用级条目)
- config_manager.py : ConfigManager (QML 友好接口 + 单例)
- dpi.py            : DPI 缩放工具
"""

from importlib import import_module as _import_module

__all__ = [
    # Validators
    "Validator",
    "ValidationKind",
    # Setting entries
    "SettingEntry",
    "RangedEntry",
    "EnumEntry",
    # Container base
    "SettingsCore",
    # App-level config
    "AppConfig",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_APP_CONFIG",
    # Manager
    "ConfigManager",
    "getConfigManager",
    # DPI
    "getSystemDpiScale",
    "applyDpiScale",
]

_LAZY_EXPORTS = {
    # Validators
    "Validator": (".validators", "Validator"),
    "ValidationKind": (".validators", "ValidationKind"),
    # Setting entries
    "SettingEntry": (".config_item", "SettingEntry"),
    "RangedEntry": (".config_item", "RangedEntry"),
    "EnumEntry": (".config_item", "EnumEntry"),
    # Container base
    "SettingsCore": (".settings_base", "SettingsCore"),
    # App-level config
    "AppConfig": (".app_config", "AppConfig"),
    "DEFAULT_CONFIG_DIR": (".app_config", "DEFAULT_CONFIG_DIR"),
    "DEFAULT_APP_CONFIG": (".app_config", "DEFAULT_APP_CONFIG"),
    # Manager
    "ConfigManager": (".config_manager", "ConfigManager"),
    "getConfigManager": (".config_manager", "getConfigManager"),
    # DPI
    "getSystemDpiScale": (".dpi", "getSystemDpiScale"),
    "applyDpiScale": (".dpi", "applyDpiScale"),
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
