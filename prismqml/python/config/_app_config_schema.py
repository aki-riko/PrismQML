# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Lightweight application config schema. 轻量应用配置 schema。"""

from pathlib import Path

from .validators import Validator


DEFAULT_CONFIG_DIR: Path = Path.home() / ".prismqml"
DEFAULT_APP_CONFIG: Path = DEFAULT_CONFIG_DIR / "app.json"

LAZY_LOADING_VALIDATOR = Validator.boolean()
DWM_SHADOW_VALIDATOR = Validator.boolean()
MICA_ENABLED_VALIDATOR = Validator.boolean()
DPI_SCALE_VALIDATOR = Validator.choice([0, 100, 125, 150, 175, 200])
WINDOW_TYPE_VALIDATOR = Validator.choice([0, 1, 2])

APP_WINDOW_VALIDATORS = {
    "LazyLoading": LAZY_LOADING_VALIDATOR,
    "DwmShadow": DWM_SHADOW_VALIDATOR,
    "MicaEnabled": MICA_ENABLED_VALIDATOR,
    "DpiScale": DPI_SCALE_VALIDATOR,
    "WindowType": WINDOW_TYPE_VALIDATOR,
}


def validate_app_window_mapping(window) -> bool:
    """Validate declared Window fields while allowing extensions. 校验已声明字段。"""
    if not isinstance(window, dict):
        return False
    return all(
        name not in window or validator.accepts(window[name])
        for name, validator in APP_WINDOW_VALIDATORS.items()
    )


__all__ = [
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_APP_CONFIG",
    "LAZY_LOADING_VALIDATOR",
    "DWM_SHADOW_VALIDATOR",
    "MICA_ENABLED_VALIDATOR",
    "DPI_SCALE_VALIDATOR",
    "WINDOW_TYPE_VALIDATOR",
    "validate_app_window_mapping",
]
