# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window state initialization helpers. 窗口状态初始化辅助函数。"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from ._page_prewarm import initialize_page_prewarm_state
from ..runtime.startup_defaults import (
    DEFAULT_SPLASH_SUBTITLE,
    resolve_initial_window_size,
)

if TYPE_CHECKING:
    from .window_core import NavigationItem


def initialize_window_state(owner: Any, window_type: int) -> None:
    """Initialize state required before config lookup. 初始化配置读取前的窗口状态。"""
    owner._window_type = window_type
    owner._engine: Optional[QQmlApplicationEngine] = None
    owner._window: Optional[QQuickWindow] = None
    owner._content_area: Optional[QQuickItem] = None

    # Cache early public calls until the QML root exists. 在 QML 根创建前缓存早期调用。
    # These two containers are flushed by _apply_pending_state.
    # 这两个容器由 _apply_pending_state 统一刷入 QML。
    owner._pending_props: Dict[str, Any] = {}
    owner._pending_calls: List[tuple[str, Any]] = []

    owner._title = "PrismQML App"
    owner._width, owner._height = resolve_initial_window_size()
    owner._icon = ""
    owner._icon_colored = True
    # Optional generic title-bar action. 可选通用标题栏动作。
    owner._caption_action_visible = False
    owner._caption_action_icon = ""
    owner._caption_action_tool_tip = ""
    owner._caption_action_enabled = True
    owner._caption_action_callback = None

    owner._nav_items: List["NavigationItem"] = []
    owner._bottom_nav_items: List["NavigationItem"] = []
    owner._current_index = 0
    owner._pages: Dict[int, Any] = {}
    initialize_page_prewarm_state(owner)


def initialize_splash_state(owner: Any) -> None:
    """Initialize Splash defaults after config succeeds. 配置成功后初始化 Splash 默认值。"""
    owner._splash_enabled = True
    owner._splash_icon = ""
    owner._splash_title = ""
    owner._splash_subtitle = DEFAULT_SPLASH_SUBTITLE
