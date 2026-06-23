# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""FluentQML Window Classes - Python版窗口类

统一窗口入口模块。
"""

from typing import Optional
from PySide6.QtCore import QObject

from .window_base import WindowCore, WindowType, NavigationItem

# ==================== 统一窗口类 ====================

class Window(WindowCore):
    """FluentQML统一窗口类

    通过window_type参数选择窗口风格：
    - WindowType.SPLIT (0): 展开式侧边导航
    - WindowType.BAR (1): 紧凑侧边导航（默认）
    - WindowType.FILLED (2): 填充式分割窗口

    Example:
        # 紧凑侧边导航（默认）
        window = Window()

        # 展开式侧边导航
        window = Window(window_type=WindowType.SPLIT)

        # 填充式分割窗口
        window = Window(window_type=WindowType.FILLED)
    """

    def __init__(
        self, window_type: int = WindowType.BAR, parent: Optional[QObject] = None
    ):
        super().__init__(window_type=window_type, parent=parent)


# ==================== 导出 ====================

# App 类已提取到 app.py
from .app import App

__all__ = [
    "App",
    "Window",
    "WindowCore",
    "WindowType",
    "NavigationItem",
]
