# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Optional provider factory composition. 可选 provider 工厂运行时装配。"""


def get_qrcode_generator():
    """Return the runtime-owned QR generator. 获取 runtime 持有的二维码生成器。"""
    from ..providers.qrcode_generator import (
        get_qrcode_generator as _get_qrcode_generator,
    )

    return _get_qrcode_generator()


def get_qrcode_provider():
    """Create an engine-owned QR provider. 创建由引擎持有的二维码 provider。"""
    from ..providers.qrcode_generator import (
        get_qrcode_provider as _get_qrcode_provider,
    )

    return _get_qrcode_provider()


def get_screen_eyedropper_manager():
    """Return the runtime-owned screen eyedropper. 获取 runtime 持有的屏幕取色管理器。"""
    from ..providers.screen_eyedropper import (
        get_screen_eyedropper_manager as _get_screen_eyedropper_manager,
    )

    return _get_screen_eyedropper_manager()


def get_svg_provider():
    """Create an engine-owned SVG provider. 创建由引擎持有的 SVG provider。"""
    from ..providers.svg_provider import get_svg_provider as _get_svg_provider

    return _get_svg_provider()


__all__ = [
    "get_qrcode_generator",
    "get_qrcode_provider",
    "get_screen_eyedropper_manager",
    "get_svg_provider",
]
