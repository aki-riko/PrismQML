# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Runtime behavior mixed into the generated Icon enum. 生成图标枚举的运行时行为。"""

from pathlib import Path
import re
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon


def _default_icon_color(color: Optional[str]) -> str:
    if color is not None:
        return color
    from .theme import isDark

    return "#ffffff" if isDark() else "#1a1a1a"


def _tinted_svg(svg_path: str, color: str) -> str:
    with open(svg_path, "r", encoding="utf-8") as stream:
        svg_content = stream.read()
    svg_content = re.sub(r'fill="[^"]*"', f'fill="{color}"', svg_content)
    if "fill=" not in svg_content:
        svg_content = svg_content.replace("<svg", f'<svg fill="{color}"', 1)
    return svg_content


def _render_svg_icon(svg_content: str) -> "QIcon":
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QIcon, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(svg_content.encode("utf-8"))
    if not renderer.isValid():
        return QIcon()
    icon = QIcon()
    for size in (16, 24, 32, 48):
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


class _IconRuntimeMixin:
    """Preserve public helpers without putting rendering in generated data. 保留公开方法。"""

    def path(self) -> str:
        """Return the Fluent SVG path. 返回 Fluent SVG 路径。"""
        from .utils import qml_path

        return str(qml_path() / "controls" / "icons" / "fluent" / f"{self.value}.svg")

    def to_qicon(self, color: Optional[str] = None) -> "QIcon":
        """Render a theme-aware QIcon. 渲染主题感知 QIcon。"""
        from PySide6.QtGui import QIcon

        svg_path = self.path()
        if not Path(svg_path).exists():
            return QIcon()
        svg_content = _tinted_svg(svg_path, _default_icon_color(color))
        return _render_svg_icon(svg_content)
