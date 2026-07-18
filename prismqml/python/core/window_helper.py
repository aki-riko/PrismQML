# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
WindowHelper - 窗口辅助工具（QML可调用）

提供 setAppIcon 等需要 Python 原生能力的窗口操作。
Provides native window operations callable from QML, such as taskbar icon setting.
"""
import time
from typing import Optional

from PySide6.QtCore import QObject, QPoint, QSize, Slot
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap, Qt

from ._icon_path import resolve_icon_path
from .logger import warning, error, debug


# SVG 渲染的多尺寸列表（用于生成高质量任务栏图标）
_ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


class WindowHelper(QObject):
    """
    窗口辅助工具单例

    QML 中通过 WindowHelper.setAppIcon(iconPath) 调用。
    In QML: WindowHelper.setAppIcon(iconPath)
    """

    _instance: Optional["WindowHelper"] = None

    def __new__(cls, parent: Optional[QObject] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True

    @Slot(str)
    def setAppIcon(self, icon: str) -> None:
        """Set taskbar icon from local/file/qrc paths. 从本地或资源路径设置图标。"""
        if not icon:
            return
        profile_start = time.perf_counter()
        icon_path = self._resolveIconPath(icon)
        resolve_ms = int((time.perf_counter() - profile_start) * 1000)
        if not icon_path:
            warning(f"无法解析图标路径: {icon}")
            return
        app = QGuiApplication.instance()
        if not app:
            warning("QGuiApplication 未创建，无法设置图标")
            return
        if self._try_set_svg_icon(app, icon_path, profile_start, resolve_ms):
            return
        self._set_bitmap_icon(app, icon_path, profile_start, resolve_ms)

    @Slot(int, int, result="QVariantMap")
    def availableScreenGeometryAt(self, x: int, y: int) -> dict[str, int]:
        """Return the available geometry for the screen containing a global point."""
        app = QGuiApplication.instance()
        if app is None:
            return {}
        screen = app.screenAt(QPoint(x, y))
        if screen is None:
            screen = app.primaryScreen()
        if screen is None:
            return {}
        geometry = screen.availableGeometry()
        return {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
        }

    def _try_set_svg_icon(
        self,
        app: QGuiApplication,
        icon_path: str,
        profile_start: float,
        resolve_ms: int,
    ) -> bool:
        """Render and publish an SVG when applicable. 按需渲染并发布 SVG。"""
        if not icon_path.lower().endswith(".svg"):
            return False
        render_start = time.perf_counter()
        qicon = self._renderSvgIcon(icon_path)
        if not qicon or qicon.isNull():
            return False
        app.setWindowIcon(qicon)
        debug(
            "[启动剖析] WindowHelper.setAppIcon SVG: "
            f"resolve={resolve_ms}ms / "
            f"render={int((time.perf_counter() - render_start) * 1000)}ms / "
            f"total={int((time.perf_counter() - profile_start) * 1000)}ms"
        )
        debug(f"任务栏图标已设置 (SVG): {icon_path}")
        return True

    @staticmethod
    def _set_bitmap_icon(
        app: QGuiApplication,
        icon_path: str,
        profile_start: float,
        resolve_ms: int,
    ) -> None:
        """Load and publish a bitmap icon. 加载并发布位图图标。"""
        qicon = QIcon(icon_path)
        if qicon.isNull():
            warning(f"图标加载失败: {icon_path}")
            return
        app.setWindowIcon(qicon)
        debug(
            "[启动剖析] WindowHelper.setAppIcon bitmap: "
            f"resolve={resolve_ms}ms / "
            f"total={int((time.perf_counter() - profile_start) * 1000)}ms"
        )
        debug(f"任务栏图标已设置: {icon_path}")

    @staticmethod
    def _resolveIconPath(icon: str) -> str:
        """解析各类图标路径为可用的文件路径

        Args:
            icon: 原始图标路径

        Returns:
            解析后的文件路径
        """
        return resolve_icon_path(icon)

    @staticmethod
    def _renderSvgIcon(svg_path: str) -> Optional[QIcon]:
        """Render one SVG into a multi-size icon. 将 SVG 渲染为多尺寸图标。"""
        try:
            from PySide6.QtSvg import QSvgRenderer

            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                warning(f"SVG 渲染器无效: {svg_path}")
                return None
            return WindowHelper._render_svg_sizes(renderer)
        except ImportError:
            warning("PySide6.QtSvg 未安装，SVG 图标无法渲染")
            return None
        except Exception as e:
            error(f"SVG 图标渲染失败: {e}")
            return None

    @staticmethod
    def _render_svg_sizes(renderer) -> QIcon:
        """Render all taskbar sizes. 渲染全部任务栏尺寸。"""
        qicon = QIcon()
        for size in _ICON_SIZES:
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            qicon.addPixmap(pixmap)
        return qicon


def get_window_helper() -> WindowHelper:
    """获取 WindowHelper 单例"""
    return WindowHelper()
