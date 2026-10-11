# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Page manager failure-boundary regressions. 页面管理失败边界回归。"""

from types import SimpleNamespace

import pytest
from PySide6.QtQuick import QQuickItem


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_page_size_signal_process_control_propagates(error_type):
    from prismqml.python.window._page_manager import _emit_page_size_signals

    def stop_emit():
        raise error_type("stop")

    page_item = SimpleNamespace(
        widthChanged=SimpleNamespace(emit=stop_emit),
        heightChanged=SimpleNamespace(emit=lambda: None),
    )
    with pytest.raises(error_type, match="stop"):
        _emit_page_size_signals(page_item)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_async_page_creation_process_control_propagates(error_type):
    from prismqml.python.window._page_manager import _create_async_page_boundary

    def stop_create():
        raise error_type("stop")

    item = SimpleNamespace(
        page_getter=stop_create,
        page_class=None,
        _page_instance=None,
    )
    with pytest.raises(error_type, match="stop"):
        _create_async_page_boundary(item, lambda _page: None)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize(
    ("method_name", "args"),
    (
        ("_switch_to_index", (0,)),
        ("_start_async_page_load", (0,)),
        ("_finish_loading", ()),
    ),
)
def test_page_manager_invoke_process_control_propagates(
    monkeypatch, error_type, method_name, args
):
    from prismqml.python.window import _page_manager

    def stop_invoke(*_args):
        raise error_type("stop")

    monkeypatch.setattr(
        _page_manager,
        "QMetaObject",
        SimpleNamespace(invokeMethod=stop_invoke),
    )
    manager = _page_manager.PageManagerMixin()
    manager._window = object()
    with pytest.raises(error_type, match="stop"):
        getattr(manager, method_name)(*args)


def test_page_container_lookup_reuses_cache_until_window_changes(qapp):
    from prismqml.python.window._page_manager import PageManagerMixin

    root = QQuickItem()
    first_page = QQuickItem(root)
    first_page.setObjectName("page_0")

    class Window:
        def __init__(self, content_item):
            self._content_item = content_item

        def contentItem(self):
            return self._content_item

    manager = PageManagerMixin()
    first_window = Window(root)
    manager._window = first_window

    assert manager._find_child_by_name("page_0") is first_page
    assert manager._find_child_by_name("page_0") is first_page

    second_root = QQuickItem()
    second_page = QQuickItem(second_root)
    second_page.setObjectName("page_0")
    manager._window = Window(second_root)
    assert manager._find_child_by_name("page_0") is second_page

    first_page.deleteLater()
    second_page.deleteLater()
    root.deleteLater()
    second_root.deleteLater()
