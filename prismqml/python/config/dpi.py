# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
DPI缩放工具 DPI Scale Utilities
"""

import os
import sys
import json
from pathlib import Path

from .app_config import DEFAULT_APP_CONFIG
from ..core import info, warning, error

# ==================== DPI Constants DPI常量 ====================

DPI_BASE = 96  # Windows base DPI Windows基准DPI
DPI_SCALE_DEFAULT = 100  # Default scale percentage 默认缩放百分比


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
        import ctypes

        # 方法1: GetDpiForSystem (Windows 10 1607+) - 不受DPI感知影响
        # Method 1: GetDpiForSystem (Windows 10 1607+) - not affected by DPI awareness
        try:
            dpi = ctypes.windll.user32.GetDpiForSystem()
            if dpi > 0:
                scale = round(dpi / DPI_BASE * DPI_SCALE_DEFAULT)
                return scale
        except (OSError, AttributeError):
            # API not available on this Windows version 此Windows版本不支持此API
            pass

        # 方法2: 从注册表读取 (兼容旧系统)
        # Method 2: Read from registry (compatible with older systems)
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics"
            )
            # AppliedDPI 存储实际DPI值 AppliedDPI stores actual DPI value
            dpi, _ = winreg.QueryValueEx(key, "AppliedDPI")
            winreg.CloseKey(key)
            if dpi > 0:
                scale = round(dpi / DPI_BASE * DPI_SCALE_DEFAULT)
                return scale
        except (OSError, FileNotFoundError):
            # Registry key not found 注册表键不存在
            pass

        # 方法3: 从LogPixels注册表读取
        # Method 3: Read from LogPixels registry
        try:
            import winreg

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
            dpi, _ = winreg.QueryValueEx(key, "LogPixels")
            winreg.CloseKey(key)
            if dpi > 0:
                scale = round(dpi / DPI_BASE * DPI_SCALE_DEFAULT)
                return scale
        except (OSError, FileNotFoundError):
            # Registry key not found 注册表键不存在
            pass

        return DPI_SCALE_DEFAULT
    except Exception as e:
        error(f"获取系统DPI失败 Failed to get system DPI: {e}")
        return DPI_SCALE_DEFAULT


def applyDpiScale(config_path: str = None) -> int:
    """
    在QApplication创建前应用DPI缩放（必须在创建QApplication之前调用）
    Apply DPI scale before QApplication creation (must be called before QApplication)

    Returns:
        int: 应用的DPI缩放值（0=跟随系统）
             Applied DPI scale value (0=follow system)
    """
    config_file = Path(config_path) if config_path else DEFAULT_APP_CONFIG
    dpi_scale = 0  # 默认跟随系统 Default follow system

    if config_file.exists():
        try:
            with open(config_file, encoding="utf-8") as f:
                cfg = json.load(f)
            dpi_scale = cfg.get("Window", {}).get("DpiScale", 0)
        except Exception as e:
            error(f"读取配置失败 Failed to read config: {e}")

    # 需要清除的环境变量 Environment variables to clear
    env_vars_to_clear = ["QT_AUTO_SCREEN_SCALE_FACTOR", "QT_SCREEN_SCALE_FACTORS"]

    if dpi_scale > 0:
        # 用户指定固定缩放：禁用Qt自动DPI检测，使用固定值
        # Fixed scale: disable Qt auto DPI, use fixed value
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(dpi_scale / DPI_SCALE_DEFAULT)
        # 清除可能干扰的变量 Clear potentially interfering variables
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        info(f"固定缩放 Fixed scale: {dpi_scale}%")
    else:
        # 跟随系统：让Qt自动检测和应用系统DPI
        # Follow system: let Qt auto-detect system DPI
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        # 清除可能干扰的变量 Clear potentially interfering variables
        all_vars_to_clear = env_vars_to_clear + ["QT_SCALE_FACTOR"]
        for var in all_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        system_dpi = getSystemDpiScale()
        info(f"跟随系统 Follow system: {system_dpi}%")

    return dpi_scale
