# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
WindowHelper - 窗口辅助工具（QML可调用）

提供 setAppIcon 等需要 Python 原生能力的窗口操作。
Provides native window operations callable from QML, such as taskbar icon setting.
"""
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap, QPainter, Qt
from PySide6.QtCore import QSize

from .logger import info, warning, error, debug


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
    def setAppIcon(self, icon: str):
        """设置应用程序图标（任务栏 + Alt-Tab）

        支持的路径格式：
        - 本地文件路径: "d:/path/to/icon.svg"
        - file:/// URL: "file:///d:/path/to/icon.svg"
        - qrc:/ 资源: "qrc:/app_icon.svg"
        - :/ 资源: ":/app_icon.svg"

        Args:
            icon: 图标路径字符串
        """
        if not icon:
            return

        # 解析图标路径 Resolve icon path
        icon_path = self._resolveIconPath(icon)
        if not icon_path:
            warning(f"无法解析图标路径: {icon}")
            return

        app = QGuiApplication.instance()
        if not app:
            warning("QGuiApplication 未创建，无法设置图标")
            return

        # SVG 需要特殊处理（渲染为多尺寸位图）
        if icon_path.lower().endswith(".svg"):
            qicon = self._renderSvgIcon(icon_path)
            if qicon and not qicon.isNull():
                app.setWindowIcon(qicon)
                debug(f"任务栏图标已设置 (SVG): {icon_path}")
                return

        # 非 SVG 直接加载
        qicon = QIcon(icon_path)
        if not qicon.isNull():
            app.setWindowIcon(qicon)
            debug(f"任务栏图标已设置: {icon_path}")
        else:
            warning(f"图标加载失败: {icon_path}")

    @staticmethod
    def _resolveIconPath(icon: str) -> str:
        """解析各类图标路径为可用的文件路径

        Args:
            icon: 原始图标路径

        Returns:
            解析后的文件路径
        """
        if icon.startswith("qrc:"):
            # 处理 "qrc:/xxx", "qrc:///xxx" 等变体 → ":/xxx"
            path = icon[4:]  # 去掉 "qrc:"
            # 去掉多余的前导斜杠，只保留一个
            path = path.lstrip("/")
            return ":/" + path
        elif icon.startswith("file:///"):
            return icon[8:]  # "file:///d:/..." -> "d:/..."
        elif icon.startswith(":/"):
            return icon  # 资源路径保持不变
        else:
            # 本地文件路径
            return str(Path(icon).resolve())

    @staticmethod
    def _renderSvgIcon(svg_path: str) -> Optional[QIcon]:
        """将 SVG 渲染为多尺寸 QIcon

        Args:
            svg_path: SVG 文件路径

        Returns:
            QIcon 或 None
        """
        try:
            from PySide6.QtSvg import QSvgRenderer

            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                warning(f"SVG 渲染器无效: {svg_path}")
                return None

            qicon = QIcon()
            for size in _ICON_SIZES:
                pixmap = QPixmap(QSize(size, size))
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                qicon.addPixmap(pixmap)

            return qicon
        except ImportError:
            warning("PySide6.QtSvg 未安装，SVG 图标无法渲染")
            return None
        except Exception as e:
            error(f"SVG 图标渲染失败: {e}")
            return None


def get_window_helper() -> WindowHelper:
    """获取 WindowHelper 单例"""
    return WindowHelper()
