# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Appearance runtime composition. 外观运行时装配。"""

from ..core.theme import Skin, Theme, getThemeManager


def _ensure_appearance_persistence() -> None:
    """Load the persistence adapter before public mutations. 公开修改前装配持久化端口。"""
    from ..config import getConfigManager

    getConfigManager()


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
