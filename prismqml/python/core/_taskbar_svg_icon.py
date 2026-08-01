# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Lazy taskbar SVG icon engine. 任务栏 SVG 图标惰性渲染引擎。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QIconEngine, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


class _TaskbarSvgIconEngine(QIconEngine):
    """Rasterize only the fixed source size requested by Qt. 仅渲染 Qt 请求的固定源尺寸。"""

    def __init__(self, svg_path: str, icon_sizes: Sequence[int]) -> None:
        super().__init__()
        self._svg_path = svg_path
        self._icon_sizes = tuple(icon_sizes)
        self._renderer = QSvgRenderer(svg_path)
        self._source_icons: dict[int, QIcon] = {}
        self._pixmaps: dict[tuple[int, int, QIcon.Mode, QIcon.State], QPixmap] = {}

    def is_valid(self) -> bool:
        """Return whether the SVG and size table are usable. 返回 SVG 与尺寸表是否可用。"""
        return bool(self._icon_sizes) and self._renderer.isValid()

    def _source_size_for(self, size: QSize) -> int:
        """Match QPixmapIconEngine's fixed-size area selection. 匹配固定图标的面积选档。"""
        requested_area = size.width() * size.height()
        for source_size in self._icon_sizes:
            if source_size * source_size >= requested_area:
                return source_size
        return self._icon_sizes[-1]

    def _source_icon(self, source_size: int) -> QIcon:
        """Render and cache one fixed source size. 渲染并缓存一个固定源尺寸。"""
        cached = self._source_icons.get(source_size)
        if cached is not None:
            return cached
        pixmap = QPixmap(QSize(source_size, source_size))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        if not painter.isActive():
            return QIcon()
        try:
            self._renderer.render(painter)
        finally:
            painter.end()
        icon = QIcon(pixmap)
        self._source_icons[source_size] = icon
        return icon

    def actualSize(self, size, mode, state) -> QSize:  # noqa: N802, ARG002
        """Preserve the eager multi-pixmap icon's actual size. 保持原多位图实际尺寸。"""
        if size.width() <= 0 or size.height() <= 0 or not self._icon_sizes:
            return QSize()
        side = min(size.width(), size.height(), self._icon_sizes[-1])
        return QSize(side, side)

    def availableSizes(self, mode, state) -> list[QSize]:  # noqa: N802, ARG002
        """Expose the same fixed size table as the eager icon. 暴露与原图标相同的尺寸表。"""
        return [QSize(size, size) for size in self._icon_sizes]

    def clone(self) -> QIconEngine:
        """Clone the engine for a detached QIcon. 为分离后的 QIcon 克隆引擎。"""
        return _TaskbarSvgIconEngine(self._svg_path, self._icon_sizes)

    def paint(self, painter: QPainter, rect, mode, state) -> None:
        """Paint with the same fixed-source scaling policy. 按相同固定源缩放策略绘制。"""
        if rect.width() <= 0 or rect.height() <= 0:
            return
        source_size = self._source_size_for(rect.size())
        self._source_icon(source_size).paint(
            painter,
            rect,
            Qt.AlignmentFlag.AlignCenter,
            mode,
            state,
        )

    def pixmap(self, size, mode, state) -> QPixmap:
        """Return one lazily rendered and scaled pixmap. 返回惰性渲染并缩放的位图。"""
        if size.width() <= 0 or size.height() <= 0:
            return QPixmap()
        cache_key = (size.width(), size.height(), mode, state)
        cached = self._pixmaps.get(cache_key)
        if cached is not None:
            return cached
        source_size = self._source_size_for(size)
        pixmap = self._source_icon(source_size).pixmap(size, mode, state)
        if not pixmap.isNull():
            self._pixmaps[cache_key] = pixmap
        return pixmap


def create_taskbar_svg_icon(
    svg_path: str,
    icon_sizes: Sequence[int],
) -> Optional[QIcon]:
    """Create a validated lazy taskbar icon. 创建已验证的惰性任务栏图标。"""
    engine = _TaskbarSvgIconEngine(svg_path, icon_sizes)
    if not engine.is_valid():
        return None
    return QIcon(engine)


__all__ = ["create_taskbar_svg_icon"]
