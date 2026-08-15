# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Appearance persistence composition. 外观持久化装配。"""

from ..core.theme import (
    Skin,
    Theme,
    _bind_appearance_persistence,
    getThemeManager,
)
from .configuration import get_config_manager


def _apply_config_appearance(field: str, value: str) -> None:
    """Apply one persisted value to the theme runtime. 应用单项持久化外观。"""
    manager = getThemeManager()
    applicators = {
        "theme": manager._apply_theme_from_qml,
        "skin": manager._apply_skin_from_qml,
        "accent_color": manager._apply_accent_color,
    }
    applicators[field](value)


def install_config_appearance_runtime(manager) -> None:
    """Bind config values to the theme runtime. 绑定配置值与主题运行时。"""
    manager._bind_appearance_runtime(_apply_config_appearance)


def _persist_appearance_change(field: str, value: str) -> None:
    """Route core appearance requests through config. 通过配置路由外观请求。"""
    manager = get_config_manager()
    setters = {
        "theme": manager.setTheme,
        "skin": manager.setSkin,
        "accent_color": manager.setAccentColor,
    }
    setters[field](value)


def install_appearance_persistence() -> None:
    """Install the runtime-owned persistence adapter. 安装运行时持久化适配器。"""
    _bind_appearance_persistence(_persist_appearance_change)


def _ensure_appearance_persistence() -> None:
    """Load the persistence adapter before public mutations. 公开修改前装配持久化端口。"""
    install_appearance_persistence()
    get_config_manager()


def setTheme(theme: Theme) -> None:
    """Set and persist the application theme. 设置并持久化应用主题。"""
    _ensure_appearance_persistence()
    getThemeManager().setTheme(theme)


def setSkin(skin: Skin) -> None:
    """Set and persist the design skin. 设置并持久化设计皮肤。"""
    _ensure_appearance_persistence()
    getThemeManager().setSkin(skin)


def setAccentColor(color: str) -> None:
    """Set and persist the accent color. 设置并持久化强调色。"""
    _ensure_appearance_persistence()
    getThemeManager().setAccentColor(color)
