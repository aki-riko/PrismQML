# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""SVG Image Provider - 高质量SVG渲染器

使用QSvgRenderer提供高质量的SVG渲染，供QML Image组件使用。
Usage in QML: Image { source: "image://svg/path/to/icon.svg" }
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtSvg import QSvgRenderer


class SvgImageProvider(QQuickImageProvider):
    """SVG图片提供器 - 使用QSvgRenderer实现高质量渲染

    QML Usage 使用方式:
        Image {
            source: "image://svg/path/to/icon.svg"
            sourceSize: Qt.size(128, 128)  // Optional: specify render size 可选：指定渲染尺寸
        }

    The path after "image://svg/" is the actual file path.
    "image://svg/" 后面的路径是实际的文件路径。
    """

    # Default render size when not specified 未指定时的默认渲染尺寸
    DEFAULT_SIZE = 128
    # 最大缓存条目数 Maximum cache entries
    MAX_CACHE_SIZE = 256

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._cache: dict[str, QSvgRenderer] = {}

    def requestImage(self, id, size, requestedSize):
        """Request an image from the provider 从提供器请求图片

        Args:
            id: The path to the SVG file (after "image://svg/")
                SVG文件路径（"image://svg/"之后的部分）
            size: Output parameter for the actual image size (not used in Python)
                  输出参数，实际图片尺寸（Python中不使用）
            requestedSize: The requested size from QML (from sourceSize property)
                          QML请求的尺寸（来自sourceSize属性）

        Returns:
            QImage: The rendered SVG image SVG渲染后的图片
        """
        # Handle qrc paths QRC路径处理
        if id.startswith("qrc:/"):
            path = ":" + id[4:]  # Convert "qrc:/xxx" to ":/xxx"
        elif id.startswith(":/"):
            path = id
        else:
            path = id

        # Get or create renderer 获取或创建渲染器
        renderer = self._get_renderer(path)
        if not renderer or not renderer.isValid():
            # Return empty image if SVG is invalid 如果SVG无效则返回空图片
            return QImage()

        # Determine render size 确定渲染尺寸
        if (
            requestedSize.isValid()
            and requestedSize.width() > 0
            and requestedSize.height() > 0
        ):
            render_size = requestedSize
        else:
            # Use default size or SVG's default size 使用默认尺寸或SVG的默认尺寸
            default_size = renderer.defaultSize()
            if default_size.isValid():
                render_size = default_size
            else:
                render_size = QSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE)

        # Create image with transparency 创建带透明度的图片
        image = QImage(render_size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)

        # Render SVG 渲染SVG
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(painter)
        painter.end()

        return image

    def _get_renderer(self, path: str) -> Optional[QSvgRenderer]:
        """Get cached renderer or create new one 获取缓存的渲染器或创建新的

        Args:
            path: The SVG file path SVG文件路径

        Returns:
            QSvgRenderer or None if file not found 渲染器或None（如果文件未找到）
        """
        if path not in self._cache:
            renderer = QSvgRenderer(path)
            if renderer.isValid():
                # 缓存限制：超出时清除最早的一半
                if len(self._cache) >= self.MAX_CACHE_SIZE:
                    keys_to_remove = list(self._cache.keys())[: self.MAX_CACHE_SIZE // 2]
                    for k in keys_to_remove:
                        del self._cache[k]
                self._cache[path] = renderer
            else:
                return None
        return self._cache.get(path)

    def clearCache(self) -> None:
        """Clear the renderer cache 清除渲染器缓存"""
        self._cache.clear()


# Singleton instance 单例实例
_svg_provider: Optional[SvgImageProvider] = None


def get_svg_provider() -> SvgImageProvider:
    """Get the singleton SVG image provider 获取单例SVG图片提供器

    Returns:
        SvgImageProvider: The singleton instance 单例实例
    """
    global _svg_provider
    if _svg_provider is None:
        _svg_provider = SvgImageProvider()
    return _svg_provider


__all__ = ["SvgImageProvider", "get_svg_provider"]
