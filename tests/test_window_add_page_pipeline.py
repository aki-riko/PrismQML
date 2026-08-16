# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowCore.addPage characterization. 页面注册现状合同。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from prismqml.python import config
from prismqml.python.window import window_core


class _PageClass:
    def __init__(self):
        raise AssertionError("page class must not be instantiated during registration")


class _CallableFactory:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return object()


@pytest.fixture
def manager(monkeypatch):
    config_manager = SimpleNamespace(
        lazyLoading=True,
        appearancePersistenceEnabled=True,
        _bind_appearance_runtime=lambda _callback, *, apply_persisted=True: None,
    )
    monkeypatch.setattr(config, "getConfigManager", lambda: config_manager)
    return window_core.WindowCore()


def _source_for(kind):
    if kind == "class":
        return _PageClass
    if kind == "factory":
        return _CallableFactory()
    if kind == "instance":
        return object()
    return None


def _assert_source_slot(item, kind, interface):
    assert item.page_class is (interface if kind == "class" else None)
    assert item.page_getter is (interface if kind == "factory" else None)
    assert item._page_instance is (interface if kind == "instance" else None)
    if kind == "factory":
        assert interface.calls == 0


@pytest.mark.parametrize("kind", ["class", "factory", "instance", "none"])
def test_add_page_preserves_source_classification_and_metadata(manager, kind):
    interface = _source_for(kind)

    index = manager.addPage(
        interface,
        "source-icon",
        "Source page",
        selectedIcon="selected-icon",
        selectable=False,
    )

    assert index == 0
    assert manager._bottom_nav_items == []
    assert len(manager._nav_items) == 1
    item = manager._nav_items[0]
    assert item.text == "Source page"
    assert item.icon == "source-icon"
    assert item.selected_icon == "selected-icon"
    assert item.selectable is False
    _assert_source_slot(item, kind, interface)


def test_add_page_keeps_top_bottom_lists_and_local_indexes(manager):
    top_zero = manager.addPage(None, "top-0", "Top zero")
    bottom_zero = manager.addPage(None, "bottom-0", "Bottom zero", "bottom")
    top_one = manager.addPage(None, "top-1", "Top one", "top")
    bottom_one = manager.addPage(None, "bottom-1", "Bottom one", "bottom")

    assert (top_zero, bottom_zero, top_one, bottom_one) == (0, 0, 1, 1)
    assert [item.text for item in manager._nav_items] == ["Top zero", "Top one"]
    assert [item.text for item in manager._bottom_nav_items] == [
        "Bottom zero",
        "Bottom one",
    ]
    assert manager._nav_items[0].selected_icon == ""
    assert manager._nav_items[0].selectable is True


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_add_page_constructor_failures_propagate_without_registration(
    manager, monkeypatch, error_type
):
    def fail_navigation_item(*_args, **_kwargs):
        raise error_type("stop")

    monkeypatch.setattr(window_core, "NavigationItem", fail_navigation_item)
    with pytest.raises(error_type, match="stop"):
        manager.addPage(_PageClass, "icon", "Page")

    assert manager._nav_items == []
    assert manager._bottom_nav_items == []
