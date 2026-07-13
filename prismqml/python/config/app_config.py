# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML 应用级设置 — 落盘到 ~/.prismqml/app.json

这是 PrismQML 自带的 SettingsCore 子类,承载窗口外观、DPI、窗口类型等
进程级偏好。下游业务可自行继承 SettingsCore 定义业务条目,
这里只放引擎自身需要的 5 项。
"""

from pathlib import Path
from typing import ClassVar

from .config_item import EnumEntry, SettingEntry
from .settings_core import SettingsCore
from .validators import Validator


# ---------- 默认存放路径 ----------

DEFAULT_CONFIG_DIR: Path = Path.home() / ".prismqml"
DEFAULT_APP_CONFIG: Path = DEFAULT_CONFIG_DIR / "app.json"


# ---------- AppConfig ----------
# SettingEntry 类属性仅定义 schema prototype；SettingsCore 为每个实例克隆绑定条目。
class AppConfig(SettingsCore):
    """PrismQML app-level settings persisted under ~/.prismqml/app.json."""

    # ── Window appearance ──
    lazy_loading: ClassVar[SettingEntry] = SettingEntry(
        group="Window",
        name="LazyLoading",
        default=True,
        validator=Validator.boolean(),
    )

    dwm_shadow: ClassVar[SettingEntry] = SettingEntry(
        group="Window",
        name="DwmShadow",
        default=True,
        validator=Validator.boolean(),
    )

    mica_enabled: ClassVar[SettingEntry] = SettingEntry(
        group="Window",
        name="MicaEnabled",
        default=False,
        validator=Validator.boolean(),
    )

    # ── DPI & window type ──
    # DPI scale: 0=跟随系统; 100/125/150/175/200=固定百分比
    dpi_scale: ClassVar[EnumEntry] = EnumEntry(
        group="Window",
        name="DpiScale",
        default=0,
        validator=Validator.choice([0, 100, 125, 150, 175, 200]),
        restart=True,
    )

    # Window type: 0=展开式侧边导航, 1=紧凑底栏导航, 2=填充分割式导航
    window_type: ClassVar[EnumEntry] = EnumEntry(
        group="Window",
        name="WindowType",
        default=1,
        validator=Validator.choice([0, 1, 2]),
        restart=True,
    )


def validate_app_window_mapping(window) -> bool:
    """严格校验 AppConfig 已声明的 Window 字段；未知字段保持可扩展。"""
    if not isinstance(window, dict):
        return False
    for entry in AppConfig._setting_entries.values():
        if entry.group != "Window" or not entry.name or entry.name not in window:
            continue
        if not entry.validator.accepts(window[entry.name]):
            return False
    return True


__all__ = [
    "AppConfig",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_APP_CONFIG",
    "validate_app_window_mapping",
]
