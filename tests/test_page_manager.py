# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Page manager failure-boundary regressions. 页面管理失败边界回归。"""

from types import SimpleNamespace

import pytest


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
