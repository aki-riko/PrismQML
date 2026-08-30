# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Shared startup surface defaults. 共享启动表面默认值。"""

DEFAULT_SPLASH_SUBTITLE = "正在加载组件..."

# Single source for the host window size, shared by the pre-window splash and
# the navigation window. App resolves it once so both surfaces open at the same
# size without the host repeating the numbers.
# 宿主窗口尺寸的单一来源，由窗口前启动页与导航窗口共享。App 只解析一次，
# 使两个表面以相同尺寸打开，宿主无需重复填写同一组数字。
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800


def validate_window_dimension(value: int, name: str) -> int:
    """Reject non-positive or non-integer sizes. 拒绝非正数与非整数尺寸。"""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def resolve_initial_window_size() -> tuple[int, int]:
    """Read the App-owned window size. 读取 App 持有的窗口尺寸。

    App resolves the size before any window exists, so the splash and the
    window open at one geometry. A bare window built without App still falls
    back to the shared defaults.
    App 在任何窗口存在前解析尺寸，使启动页与窗口以同一几何打开；未经 App
    直接构造窗口时回落到共享默认值。
    """
    from ..window.app import App

    try:
        return App.instance().window_size
    except RuntimeError:
        return (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
