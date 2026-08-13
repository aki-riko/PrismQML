# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
DPI缩放工具 DPI Scale Utilities
"""

import json
import os
import sys
from pathlib import Path

from ._app_config_schema import (
    DEFAULT_APP_CONFIG,
    DPI_SCALE_VALIDATOR,
    resolve_app_config_path,
    validate_app_appearance_mapping,
    validate_app_window_mapping,
)
from ..core import debug, info, warning

# ==================== DPI Constants DPI常量 ====================

DPI_BASE = 96  # Windows base DPI Windows基准DPI
DPI_SCALE_DEFAULT = 100  # Default scale percentage 默认缩放百分比
_AUTO_DPI_ENVIRONMENT = (
    "QT_AUTO_SCREEN_SCALE_FACTOR",
    "QT_SCREEN_SCALE_FACTORS",
)


def _dpi_to_scale(dpi):
    """把正整数 DPI 换算为百分比；异常 API 值返回 None。"""
    if type(dpi) is not int or dpi <= 0:
        return None
    return round(dpi / DPI_BASE * DPI_SCALE_DEFAULT)


def _read_registry_dpi_scale(winreg, key_path, value_name):
    """读取一个注册表 DPI 值，并保证查询失败时句柄也会关闭。"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            dpi, _ = winreg.QueryValueEx(key, value_name)
    except (OSError, AttributeError, TypeError, ValueError) as exc:
        debug(f"{value_name} 注册表读取失败 Registry read failed: {exc}")
        return None
    return _dpi_to_scale(dpi)


def _get_dpi_for_system_scale():
    """调用 awareness-dependent GetDpiForSystem 作为注册表后的兜底。"""
    try:
        import ctypes

        dpi = ctypes.windll.user32.GetDpiForSystem()
    except (OSError, AttributeError, TypeError) as exc:
        debug(f"GetDpiForSystem 不可用 API unavailable: {exc}")
        return None
    return _dpi_to_scale(dpi)


def getSystemDpiScale() -> int:
    """
    获取Windows系统DPI缩放百分比
    Get Windows system DPI scale percentage

    Returns:
        int: DPI缩放百分比（如 100, 125, 150, 175, 200）
             DPI scale percentage (e.g. 100, 125, 150, 175, 200)
    """
    if sys.platform != "win32":
        return DPI_SCALE_DEFAULT

    try:
        import winreg
    except ImportError as exc:
        debug(f"winreg 不可用 Registry API unavailable: {exc}")
    else:
        registry_values = (
            (r"Control Panel\Desktop\WindowMetrics", "AppliedDPI"),
            (r"Control Panel\Desktop", "LogPixels"),
        )
        for key_path, value_name in registry_values:
            scale = _read_registry_dpi_scale(winreg, key_path, value_name)
            if scale is not None:
                return scale

    # GetDpiForSystem returns 96 on DPI-unaware threads, so it is fallback only.
    # DPI-unaware 线程会固定得到 96，因此该 API 只能作为注册表后的兜底。
    scale = _get_dpi_for_system_scale()
    return scale if scale is not None else DPI_SCALE_DEFAULT


def _read_configured_dpi_scale(config_file: Path) -> int:
    """从真实 JSON 严格读取 AppConfig 声明的离散 DPI 值。"""
    if not config_file.exists():
        return 0
    try:
        with open(config_file, encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        warning(f"读取 DPI 配置失败 Failed to read DPI config: {exc}")
        return 0
    if not isinstance(payload, dict):
        warning("DPI 配置根节点必须是对象 DPI config root must be an object")
        return 0
    window = payload.get("Window", {})
    appearance = payload.get("Appearance", {})
    if not validate_app_window_mapping(window):
        warning("DPI 启动配置含无效 Window 字段 Invalid Window startup config")
        return 0
    if not validate_app_appearance_mapping(appearance):
        warning(
            "DPI 启动配置含无效 Appearance 字段 Invalid Appearance startup config"
        )
        return 0
    value = window.get("DpiScale", 0)
    if not DPI_SCALE_VALIDATOR.accepts(value):
        warning(f"拒绝无效 DPI 配置 Invalid DPI config rejected: {value!r}")
        return 0
    return value


def _clear_environment(names):
    for name in names:
        os.environ.pop(name, None)


def applyDpiScale(config_path: str = None) -> int:
    """
    在QApplication创建前应用DPI缩放（必须在创建QApplication之前调用）
    Apply DPI scale before QApplication creation (must be called before QApplication)

    Returns:
        int: 应用的DPI缩放值（0=跟随系统）
             Applied DPI scale value (0=follow system)
    """
    config_file = resolve_app_config_path(config_path, default=DEFAULT_APP_CONFIG)
    dpi_scale = _read_configured_dpi_scale(config_file)

    if dpi_scale > 0:
        # 用户指定固定缩放：禁用Qt自动DPI检测，使用固定值
        # Fixed scale: disable Qt auto DPI, use fixed value
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(dpi_scale / DPI_SCALE_DEFAULT)
        # 清除可能干扰的变量 Clear potentially interfering variables
        _clear_environment(_AUTO_DPI_ENVIRONMENT)
        info(f"固定缩放 Fixed scale: {dpi_scale}%")
    else:
        # 跟随系统：让Qt自动检测和应用系统DPI
        # Follow system: let Qt auto-detect system DPI
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        # 清除可能干扰的变量 Clear potentially interfering variables
        _clear_environment(_AUTO_DPI_ENVIRONMENT + ("QT_SCALE_FACTOR",))
        system_dpi = getSystemDpiScale()
        info(f"跟随系统 Follow system: {system_dpi}%")

    return dpi_scale
