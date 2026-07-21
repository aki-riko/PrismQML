# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window show orchestration helpers. 窗口显示编排辅助函数。"""

import time
from typing import Any, Callable


ProfileCallback = Callable[[str], None]


def make_show_profile(log: ProfileCallback) -> ProfileCallback:
    """Create the WindowCore.show profiler. 创建窗口显示剖析器。"""
    profile_start = time.perf_counter()
    profile_last = profile_start

    def profile(label: str):
        nonlocal profile_last
        now = time.perf_counter()
        log(
            f"[启动剖析] WindowCore.show {label}: "
            f"+{int((now - profile_last) * 1000)}ms / "
            f"total {int((now - profile_start) * 1000)}ms"
        )
        profile_last = now

    return profile


def show_window_root(owner: Any, profile: ProfileCallback) -> bool:
    """Create or restore and show the root window. 创建或恢复并显示根窗口。"""
    created_window = owner._window is None
    if created_window:
        owner._create_window()
        profile("_create_window")
    else:
        profile("复用已有窗口")

    if not owner._window:
        return False
    if created_window:
        owner._prepare_initial_frame()
        profile("show 前准备首帧")
    if not created_window:
        owner._restore_visible_state()
        profile("show 前恢复可见状态")
    owner._window.show()
    profile("QQuickWindow.show")
    if not created_window:
        owner._restore_visible_state()
        profile("show 后恢复可见状态")
    return True


def ensure_initial_pages(owner: Any, profile: ProfileCallback) -> None:
    """Create the initial page set after the root is visible. 显示根窗口后创建初始页面集。"""
    if owner._lazy_loading:
        if owner._nav_items or owner._bottom_nav_items:
            owner._ensure_page_created(0)
            profile("创建/确认首页")
    else:
        total = len(owner._nav_items) + len(owner._bottom_nav_items)
        for index in range(total):
            owner._ensure_page_created(index)
        profile("创建/确认全部页面")
