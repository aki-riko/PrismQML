# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""Gallery资源包"""

from pathlib import Path

from PySide6.QtCore import QResource


GALLERY_RCC_PATH = Path(__file__).with_name("gallery.rcc")


def register_gallery_resources() -> bool:
    """Register the compiled Gallery resources. 注册 Gallery 二进制资源。"""
    return QResource.registerResource(str(GALLERY_RCC_PATH))
