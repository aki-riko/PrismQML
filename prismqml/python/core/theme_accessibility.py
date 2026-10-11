# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Theme accessibility probes. 主题无障碍探测。"""

import os
import sys
from typing import Optional

from .logger import debug, warning


# High-contrast environment override. Unset means "ask the platform"; the
# documented truthy/falsy spellings win over the platform answer.
# 高对比度环境变量覆盖。未设置表示"询问平台"；文档化的真/假拼写优先于平台结果。
HIGH_CONTRAST_ENV = "PRISM_HIGH_CONTRAST"
_HIGH_CONTRAST_TRUTHY = frozenset({"1", "true", "yes", "on"})
_HIGH_CONTRAST_FALSY = frozenset({"0", "false", "no", "off"})
_SPI_GETHIGHCONTRAST = 0x0042
_HCF_HIGHCONTRASTON = 0x00000001


def read_high_contrast_env(raw: Optional[str] = None) -> Optional[bool]:
    """Parse the high-contrast override, or None when unset. 解析高对比度覆盖值。"""
    value = os.environ.get(HIGH_CONTRAST_ENV) if raw is None else raw
    if value is None:
        return None
    normalized = value.strip().casefold()
    if not normalized:
        return None
    if normalized in _HIGH_CONTRAST_TRUTHY:
        return True
    if normalized in _HIGH_CONTRAST_FALSY:
        return False
    warning(f"{HIGH_CONTRAST_ENV} 值非法: {value!r}，已忽略并回退平台判定")
    return None


def _read_high_contrast_flags() -> Optional[int]:
    """Read the Windows high-contrast flag word, or None when unavailable."""
    try:
        import ctypes
        from ctypes import wintypes

        class _HighContrast(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("dwFlags", wintypes.DWORD),
                ("lpszDefaultScheme", wintypes.LPWSTR),
            ]

        info = _HighContrast()
        info.cbSize = ctypes.sizeof(_HighContrast)
        succeeded = ctypes.windll.user32.SystemParametersInfoW(
            _SPI_GETHIGHCONTRAST, info.cbSize, ctypes.byref(info), 0
        )
        if not succeeded:
            debug("SystemParametersInfoW(SPI_GETHIGHCONTRAST) 调用失败，按未启用处理")
            return None
        return int(info.dwFlags)
    except (AttributeError, OSError, ValueError) as error:
        debug(f"高对比度探测失败: {error}")
        return None


def detect_high_contrast() -> bool:
    """Detect the platform high-contrast setting. 探测平台高对比度设置。"""
    if sys.platform != "win32":
        return False
    flags = _read_high_contrast_flags()
    if flags is None:
        return False
    return bool(flags & _HCF_HIGHCONTRASTON)
