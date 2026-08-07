# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Visible window-frame capture backend. 可见窗口画面截图后端。"""

from typing import Any

from PySide6.QtGui import QWindow


def grab_window_frame(
    host: Any,
    owner: Any,
    window: QWindow,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    """Capture and publish exact visible pixels. 截取并发布原始可见像素。"""
    if not window or width <= 0 or height <= 0:
        host.warning("Invalid parameters for grabWindowFrame")
        return ""
    try:
        screen = host._resolve_acrylic_screen(window)
        if screen is host._NO_ACRYLIC_SCREEN:
            return ""
        pixmap = host._grab_acrylic_region(window, screen, x, y, width, height)
        if pixmap.isNull():
            host.error("Failed to grab window frame")
            return ""
        owner._image_state.set_image(pixmap.toImage())
        image_url = f"image://acrylic/{owner._image_state.image_id}"
        owner.imageReady.emit(image_url)
        host.debug(f"Window frame image ready: {width}x{height}")
        return image_url
    except (ValueError, OSError, RuntimeError) as exc:
        host.error(f"Failed to grab window frame: {exc}")
        return ""
