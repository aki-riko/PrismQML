# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""App-level icon state orchestration. App 级图标状态编排。"""

from __future__ import annotations

import os
from typing import Union


IconSource = Union[str, os.PathLike]


class ApplicationIconMixin:
    """Expose the App-level icon facade. 暴露 App 级图标门面。"""

    def set_application_icon(
        self,
        icon: IconSource,
        colored: bool = True,
    ) -> None:
        """Set shared Qt, window, taskbar, and splash icons. 设置全局窗口、任务栏与启动图标。"""
        configure_application_icon(self, icon, colored)

    @property
    def application_icon(self) -> str:
        """Return the configured icon source. 获取应用图标来源。"""
        return self._application_icon

    @property
    def application_icon_colored(self) -> bool:
        """Return whether source colors are preserved. 获取是否保留图标原色。"""
        return self._application_icon_colored


def initialize_application_icon_state(owner) -> None:
    """Initialize application icon defaults. 初始化应用图标默认状态。"""
    owner._application_icon = ""
    owner._application_icon_colored = True


def configure_initial_application_icon(owner, icon, colored: bool) -> None:
    """Apply an optional constructor icon after Qt starts. 在 Qt 启动后应用可选构造图标。"""
    if icon is not None:
        configure_application_icon(owner, icon, colored)


def normalize_application_icon(icon: IconSource) -> str:
    """Normalize a path-like icon without altering Qt URLs. 归一化路径且保留 Qt URL。"""
    source = os.fspath(icon)
    if not isinstance(source, str):
        raise TypeError("application_icon must resolve to str")
    if not source:
        raise ValueError("application_icon must not be empty")
    return source


def apply_application_icon_to_window(owner, window) -> None:
    """Apply the configured default to one managed window. 将默认图标应用到托管窗口。"""
    if owner._application_icon:
        window.setWindowIcon(
            owner._application_icon,
            owner._application_icon_colored,
        )


def configure_application_icon(owner, icon: IconSource, colored: bool) -> str:
    """Publish one icon to Qt and every managed window. 同步图标到 Qt 与全部托管窗口。"""
    from ..core.window_helper import get_window_helper

    source = normalize_application_icon(icon)
    owner._application_icon = source
    owner._application_icon_colored = bool(colored)
    get_window_helper().setAppIcon(source)
    for window in tuple(owner._windows):
        apply_application_icon_to_window(owner, window)
    return source
