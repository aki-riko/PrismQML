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


def validate_app_window_mapping(window) -> bool:
    """严格校验 AppConfig 已声明的 Window 字段；未知字段保持可扩展。"""
    return _schema.validate_app_window_mapping(window)


__all__ = [
    "AppConfig",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_APP_CONFIG",
    "validate_app_window_mapping",
]
