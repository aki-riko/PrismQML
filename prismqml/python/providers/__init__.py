# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""FluentQML Providers - 功能提供者模块 Provider module"""

from .svg_provider import SvgImageProvider, get_svg_provider
from .qrcode_generator import (
    QRCodeGenerator,
    QRCodeImageProvider,
    get_qrcode_generator,
    get_qrcode_provider,
)
from .clipboard import ClipboardHelper, get_clipboard_helper
from .screen_eyedropper import (
    ScreenEyedropperManager,
    get_screen_eyedropper_manager,
)

__all__ = [
    "SvgImageProvider",
    "get_svg_provider",
    "QRCodeGenerator",
    "QRCodeImageProvider",
    "get_qrcode_generator",
    "get_qrcode_provider",
    "ClipboardHelper",
    "get_clipboard_helper",
    "ScreenEyedropperManager",
    "get_screen_eyedropper_manager",
]
