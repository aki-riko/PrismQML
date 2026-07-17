# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""SVG Image Provider - 高质量SVG渲染器

使用QSvgRenderer提供高质量的SVG渲染，供QML Image组件使用。
Usage in QML: Image { source: "image://svg/path/to/icon.svg" }
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtSvg import QSvgRenderer

from ..core._icon_path import resolve_provider_path


class SvgImageProvider(QQuickImageProvider):
    """SVG图片提供器 - 使用QSvgRenderer实现高质量渲染

    QML Usage 使用方式:
        Image {
            source: "image://svg/path/to/icon.svg"
            sourceSize: Qt.size(128, 128)  // Optional: specify render size 可选：指定渲染尺寸
        }

    The path after `image://svg/` is one QML URL component: reserved
    characters are percent-decoded exactly once, then file/qrc sources are
    resolved with Qt URL semantics.
    `image://svg/` 后是一个 QML URL 组件：保留字符只解码一次，再按 Qt
    URL 语义解析 file/qrc 来源。
    """

    # Default render size when not specified 未指定时的默认渲染尺寸
    DEFAULT_SIZE = 128
    # 最大缓存条目数 Maximum cache entries
    MAX_CACHE_SIZE = 256

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._cache: dict[str, QSvgRenderer] = {}

    def requestImage(self, id: str, size: QSize, requestedSize: QSize) -> QImage:
        """Render one provider request. 渲染单个 provider 请求。"""
        del size
        path = resolve_provider_path(id)
        renderer = self._get_renderer(path)
        if not renderer or not renderer.isValid():
            return QImage()
        render_size = self._resolve_render_size(renderer, requestedSize)
        return self._render_image(renderer, render_size)

    def _resolve_render_size(
        self, renderer: QSvgRenderer, requested_size: QSize
    ) -> QSize:
        """Resolve requested, intrinsic, or fallback size. 解析请求、原生或兜底尺寸。"""
        if (
            requested_size.isValid()
            and requested_size.width() > 0
            and requested_size.height() > 0
        ):
            return requested_size
        default_size = renderer.defaultSize()
        if default_size.isValid():
            return default_size
        return QSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE)

    @staticmethod
    def _render_image(renderer: QSvgRenderer, render_size: QSize) -> QImage:
        """Render a transparent antialiased image. 渲染透明抗锯齿图像。"""
        image = QImage(render_size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
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


def get_svg_provider() -> SvgImageProvider:
    """Create an engine-owned SVG image provider 创建由引擎持有的SVG图片提供器

    Returns:
        SvgImageProvider: A new provider instance 新的 provider 实例
    """
    return SvgImageProvider()


__all__ = ["SvgImageProvider", "get_svg_provider"]
