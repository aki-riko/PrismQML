# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""同步页面挂载必须对已析构对象保持安全。

背景：``_attach_async_page_content`` 用 ``_live_qt_object`` 做存活校验，而同步
路径 ``_attach_sync_page_content`` 原先用 Python 真值判断 ``if page_item:``。
Shiboken 包装器在 C++ 对象被 delete 之后**依然为真**，于是对已析构对象调
``setParentItem`` 会抛 ``RuntimeError: libshiboken: Internal C++ object already
deleted``；异步路径同一场景下则干净返回。

本测试用**真实 QQuickItem**（不用替身）覆盖两条路径，因为替身的真值语义与
Shiboken 包装器不同，测不出该缺陷。
"""

from __future__ import annotations

import shiboken6
from PySide6.QtQuick import QQuickItem

import prismqml.python.window._page_manager as page_manager


class _Page:
    """只带 ``_qml_item`` 的最小页面替身。"""

    def __init__(self, qml_item):
        self._qml_item = qml_item


def _profile(_label):
    """吞掉启动剖析回调。"""


def _dead_item():
    """构造一个 C++ 对象已被删除的 QQuickItem 包装器。"""
    item = QQuickItem()
    shiboken6.delete(item)
    return item


def _collect_warnings(monkeypatch):
    warnings = []
    monkeypatch.setattr(
        page_manager, "warning", lambda message, *a, **k: warnings.append(str(message))
    )
    return warnings


def test_sync_attach_skips_destroyed_page_item(monkeypatch):
    warnings = _collect_warnings(monkeypatch)
    manager = page_manager.PageManagerMixin()
    container = QQuickItem()

    manager._attach_sync_page_content(
        7, _Page(_dead_item()), container, _profile
    )

    assert warnings, "已析构 page_item 必须留下 warning"
    assert "page_7" in warnings[-1]
    assert container.childItems() == []


def test_sync_attach_skips_destroyed_container(monkeypatch):
    warnings = _collect_warnings(monkeypatch)
    manager = page_manager.PageManagerMixin()
    page = _Page(QQuickItem())

    manager._attach_sync_page_content(
        8, page, _dead_item(), _profile
    )

    assert warnings, "已析构 container 必须留下 warning"
    assert "page_8" in warnings[-1]


def test_sync_attach_still_attaches_live_page(monkeypatch):
    """存活路径必须保持原有行为：挂到容器上且不产生 warning。"""
    warnings = _collect_warnings(monkeypatch)
    manager = page_manager.PageManagerMixin()
    page_item = QQuickItem()
    container = QQuickItem()

    manager._attach_sync_page_content(
        9, _Page(page_item), container, _profile
    )

    assert warnings == []
    assert page_item.parentItem() is container


def test_async_attach_skips_destroyed_page_item(monkeypatch):
    """异步路径（已有守卫）作为对照，行为必须与同步路径一致。"""
    warnings = _collect_warnings(monkeypatch)
    manager = page_manager.PageManagerMixin()
    container = QQuickItem()

    manager._attach_async_page_content(_Page(_dead_item()), container)

    assert container.childItems() == []
