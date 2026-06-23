# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
"""配置子系统 — 入口模块

模块结构 Module Structure:
- validators.py     : Validator + ValidationKind
- config_item.py    : SettingEntry / RangedEntry / EnumEntry
- settings_base.py  : SettingsCore (持久化容器基类)
- app_config.py     : AppConfig (FluentQML 自带的应用级条目)
- config_manager.py : ConfigManager (QML 友好接口 + 单例)
- dpi.py            : DPI 缩放工具
"""

from .validators import Validator, ValidationKind
from .config_item import SettingEntry, RangedEntry, EnumEntry
from .settings_base import SettingsCore
from .app_config import AppConfig, DEFAULT_CONFIG_DIR, DEFAULT_APP_CONFIG
from .config_manager import ConfigManager, getConfigManager
from .dpi import getSystemDpiScale, applyDpiScale

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
