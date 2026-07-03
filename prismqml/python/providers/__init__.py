# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""PrismQML Providers - 功能提供者模块 Provider module"""

from importlib import import_module as _import_module

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

_LAZY_EXPORTS = {
    "SvgImageProvider": (".svg_provider", "SvgImageProvider"),
    "get_svg_provider": (".svg_provider", "get_svg_provider"),
    "QRCodeGenerator": (".qrcode_generator", "QRCodeGenerator"),
    "QRCodeImageProvider": (".qrcode_generator", "QRCodeImageProvider"),
    "get_qrcode_generator": (".qrcode_generator", "get_qrcode_generator"),
    "get_qrcode_provider": (".qrcode_generator", "get_qrcode_provider"),
    "ClipboardHelper": (".clipboard", "ClipboardHelper"),
    "get_clipboard_helper": (".clipboard", "get_clipboard_helper"),
    "ScreenEyedropperManager": (".screen_eyedropper", "ScreenEyedropperManager"),
    "get_screen_eyedropper_manager": (".screen_eyedropper", "get_screen_eyedropper_manager"),
}


def __getattr__(name):
    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(_import_module(module_name, __name__), attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
