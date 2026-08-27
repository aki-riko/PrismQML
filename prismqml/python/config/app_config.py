# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML 应用级设置 — 落盘到 ~/.prismqml/app.json

这是 PrismQML 自带的 SettingsCore 子类,承载窗口、DPI、主题、皮肤、语言与
主题色等进程级偏好。下游业务可自行继承 SettingsCore 定义业务条目。
"""

from pathlib import Path
from typing import ClassVar

from . import _app_config_schema as _schema
from .config_item import EnumEntry, SettingEntry
from .settings_core import SettingsCore


# ---------- 默认存放路径 ----------

DEFAULT_CONFIG_DIR: Path = _schema.DEFAULT_CONFIG_DIR
DEFAULT_APP_CONFIG: Path = _schema.DEFAULT_APP_CONFIG


# ---------- AppConfig ----------
# SettingEntry 类属性仅定义 schema prototype；SettingsCore 为每个实例克隆绑定条目。
class AppConfig(SettingsCore):
    """PrismQML app-level settings persisted under ~/.prismqml/app.json."""

    # ── Window appearance ──
    lazy_loading: ClassVar[SettingEntry] = SettingEntry(
        group="Window",
        name="LazyLoading",
        default=True,
        validator=_schema.LAZY_LOADING_VALIDATOR,
    )

    lazy_animation_type: ClassVar[EnumEntry] = EnumEntry(
        group="Window",
        name="LazyAnimationType",
        default=_schema.LAZY_ANIMATION_TYPE_DEFAULT,
        validator=_schema.LAZY_ANIMATION_TYPE_VALIDATOR,
    )

    dwm_shadow: ClassVar[SettingEntry] = SettingEntry(
        group="Window",
        name="DwmShadow",
        default=True,
        validator=_schema.DWM_SHADOW_VALIDATOR,
    )

    mica_enabled: ClassVar[SettingEntry] = SettingEntry(
        group="Window",
        name="MicaEnabled",
        default=False,
        validator=_schema.MICA_ENABLED_VALIDATOR,
    )

    # ── DPI & window type ──
    # DPI scale: 0=跟随系统; 100/125/150/175/200=固定百分比
    dpi_scale: ClassVar[EnumEntry] = EnumEntry(
        group="Window",
        name="DpiScale",
        default=0,
        validator=_schema.DPI_SCALE_VALIDATOR,
        restart=True,
    )

    # Window type: 0=展开式侧边导航, 1=紧凑底栏导航, 2=填充分割式导航
    window_type: ClassVar[EnumEntry] = EnumEntry(
        group="Window",
        name="WindowType",
        default=1,
        validator=_schema.WINDOW_TYPE_VALIDATOR,
        restart=True,
    )

    # ── Appearance ──
    theme: ClassVar[EnumEntry] = EnumEntry(
        group="Appearance",
        name="Theme",
        default="auto",
        validator=_schema.THEME_VALIDATOR,
    )

    skin: ClassVar[EnumEntry] = EnumEntry(
        group="Appearance",
        name="Skin",
        default="fluent",
        validator=_schema.SKIN_VALIDATOR,
    )

    language: ClassVar[EnumEntry] = EnumEntry(
        group="Appearance",
        name="Language",
        default="auto",
        validator=_schema.LANGUAGE_VALIDATOR,
    )

    accent_color: ClassVar[SettingEntry] = SettingEntry(
        group="Appearance",
        name="AccentColor",
        default=_schema.DEFAULT_ACCENT,
        validator=_schema.ACCENT_COLOR_VALIDATOR,
    )


def validate_app_window_mapping(window) -> bool:
    """严格校验 AppConfig 已声明的 Window 字段；未知字段保持可扩展。"""
    return _schema.validate_app_window_mapping(window)


def validate_app_appearance_mapping(appearance) -> bool:
    """严格校验 AppConfig 已声明的 Appearance 字段。"""
    return _schema.validate_app_appearance_mapping(appearance)


__all__ = [
    "AppConfig",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_APP_CONFIG",
    "validate_app_window_mapping",
    "validate_app_appearance_mapping",
]
