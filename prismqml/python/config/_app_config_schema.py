# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Lightweight application config schema. 轻量应用配置 schema。"""

import os
from pathlib import Path

from ..core.appearance_defaults import DEFAULT_ACCENT
from .validators import Validator


DEFAULT_CONFIG_DIR: Path = Path.home() / ".prismqml"
DEFAULT_APP_CONFIG: Path = DEFAULT_CONFIG_DIR / "app.json"
CONFIG_FILE_PATH_ENVIRONMENT = "PRISMQML_CONFIG_FILE"

LAZY_LOADING_VALIDATOR = Validator.boolean()
LAZY_ANIMATION_TYPE_OPTIONS = [7, 9]
LAZY_ANIMATION_TYPE_DEFAULT = LAZY_ANIMATION_TYPE_OPTIONS[0]
LAZY_ANIMATION_TYPE_VALIDATOR = Validator.choice(LAZY_ANIMATION_TYPE_OPTIONS)
DWM_SHADOW_VALIDATOR = Validator.boolean()
MICA_ENABLED_VALIDATOR = Validator.boolean()
DPI_SCALE_VALIDATOR = Validator.choice([0, 100, 125, 150, 175, 200])
WINDOW_TYPE_VALIDATOR = Validator.choice([0, 1, 2])
THEME_OPTIONS = ["auto", "light", "dark"]
SKIN_OPTIONS = ["fluent", "neobrutalism", "vintage_ticket", "neumorphism"]
LANGUAGE_OPTIONS = [
    "auto",
    "en",
    "zh_CN",
    "zh_TW",
    "hi",
    "es",
    "ar",
    "pt",
    "ru",
    "ja",
    "de",
    "fr",
    "ko",
    "it",
    "vi",
    "th",
    "id",
    "tr",
    "pl",
    "nl",
    "uk",
]
THEME_VALIDATOR = Validator.choice(THEME_OPTIONS)
SKIN_VALIDATOR = Validator.choice(SKIN_OPTIONS)
LANGUAGE_VALIDATOR = Validator.choice(LANGUAGE_OPTIONS)
ACCENT_COLOR_VALIDATOR = Validator.hex_color(DEFAULT_ACCENT)


def resolve_app_config_path(configured=None, *, default=None) -> Path:
    """Resolve explicit, environment, then default config path. 解析配置路径。"""
    if configured:
        path = Path(configured)
    else:
        environment_path = os.environ.get(CONFIG_FILE_PATH_ENVIRONMENT)
        if environment_path:
            path = Path(environment_path)
        else:
            path = Path(default) if default is not None else DEFAULT_APP_CONFIG
    return path.expanduser().resolve(strict=False)

APP_WINDOW_VALIDATORS = {
    "LazyLoading": LAZY_LOADING_VALIDATOR,
    "LazyAnimationType": LAZY_ANIMATION_TYPE_VALIDATOR,
    "DwmShadow": DWM_SHADOW_VALIDATOR,
    "MicaEnabled": MICA_ENABLED_VALIDATOR,
    "DpiScale": DPI_SCALE_VALIDATOR,
    "WindowType": WINDOW_TYPE_VALIDATOR,
}

APP_APPEARANCE_VALIDATORS = {
    "Theme": THEME_VALIDATOR,
    "Skin": SKIN_VALIDATOR,
    "Language": LANGUAGE_VALIDATOR,
}


def validate_accent_color(value) -> bool:
    """Accept the same HEX forms as ThemeManager. 校验主题管理器支持的 HEX。"""
    return ACCENT_COLOR_VALIDATOR.accepts(value)


def validate_app_window_mapping(window) -> bool:
    """Validate declared Window fields while allowing extensions. 校验已声明字段。"""
    if not isinstance(window, dict):
        return False
    return all(
        name not in window or validator.accepts(window[name])
        for name, validator in APP_WINDOW_VALIDATORS.items()
    )


def validate_app_appearance_mapping(appearance) -> bool:
    """Validate declared Appearance fields while allowing extensions. 校验外观字段。"""
    if not isinstance(appearance, dict):
        return False
    if not all(
        name not in appearance or validator.accepts(appearance[name])
        for name, validator in APP_APPEARANCE_VALIDATORS.items()
    ):
        return False
    return "AccentColor" not in appearance or validate_accent_color(
        appearance["AccentColor"]
    )


__all__ = [
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_APP_CONFIG",
    "CONFIG_FILE_PATH_ENVIRONMENT",
    "LAZY_LOADING_VALIDATOR",
    "LAZY_ANIMATION_TYPE_OPTIONS",
    "LAZY_ANIMATION_TYPE_DEFAULT",
    "LAZY_ANIMATION_TYPE_VALIDATOR",
    "DWM_SHADOW_VALIDATOR",
    "MICA_ENABLED_VALIDATOR",
    "DPI_SCALE_VALIDATOR",
    "WINDOW_TYPE_VALIDATOR",
    "THEME_OPTIONS",
    "SKIN_OPTIONS",
    "LANGUAGE_OPTIONS",
    "THEME_VALIDATOR",
    "SKIN_VALIDATOR",
    "LANGUAGE_VALIDATOR",
    "ACCENT_COLOR_VALIDATOR",
    "DEFAULT_ACCENT",
    "resolve_app_config_path",
    "validate_accent_color",
    "validate_app_window_mapping",
    "validate_app_appearance_mapping",
]
