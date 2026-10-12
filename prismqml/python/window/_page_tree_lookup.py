# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Cached objectName lookups in the stable window tree. 稳定窗口树内的带缓存子项查找。

从 `_page_manager.py` 抽出：页面容器查找依赖窗口树遍历与按窗口失效的缓存，
属于独立的查找职责，与页面生命周期管理分开维护。
"""

from typing import Any, Dict, Optional

from PySide6.QtQuick import QQuickItem


def find_item_by_name(item: QQuickItem, name: str) -> Optional[QQuickItem]:
    """Depth-first objectName lookup. 按 objectName 深度优先查找。"""
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = find_item_by_name(child, name)
        if result:
            return result
    return None


def lookup_page_container(owner: Any, name: str) -> Optional[QQuickItem]:
    """Resolve one page container by objectName with a per-window cache.

    按 objectName 解析页面容器；缓存跟随宿主窗口失效，已析构的缓存项会被丢弃后重查。
    """
    window = owner._window
    if getattr(owner, "_page_container_cache_window", None) is not window:
        owner._page_container_cache_window = window
        owner._page_container_cache = {}
    cache: Optional[Dict[str, QQuickItem]] = getattr(
        owner, "_page_container_cache", None
    )
    if cache is None:
        cache = {}
        owner._page_container_cache = cache
    cached = cache.get(name)
    if cached is not None:
        try:
            if cached.objectName() == name:
                return cached
        except RuntimeError:
            cache.pop(name, None)
    result = find_item_by_name(window.contentItem(), name)
    if result is not None:
        cache[name] = result
    return result
