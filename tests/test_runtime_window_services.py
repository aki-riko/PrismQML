# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window service runtime contracts. 窗口服务 runtime 合同。"""


def test_shadow_manager_facade_delegates_to_core(monkeypatch):
    from prismqml.python.core import shadow as core_shadow
    from prismqml.python.runtime.window_services import getShadowManager

    sentinel = object()
    monkeypatch.setattr(core_shadow, "getShadowManager", lambda: sentinel)

    assert getShadowManager() is sentinel


def test_window_helper_facade_delegates_to_core(monkeypatch):
    from prismqml.python.core import window_helper as core_window_helper
    from prismqml.python.runtime.window_services import get_window_helper

    sentinel = object()
    monkeypatch.setattr(
        core_window_helper, "get_window_helper", lambda: sentinel
    )

    assert get_window_helper() is sentinel


def test_mica_manager_facade_delegates_to_window(monkeypatch):
    from prismqml.python.runtime.window_services import get_mica_manager
    from prismqml.python.window import mica_window

    sentinel = object()
    monkeypatch.setattr(mica_window, "get_mica_manager", lambda: sentinel)

    assert get_mica_manager() is sentinel


def test_acrylic_helper_facade_delegates_to_window(monkeypatch):
    from prismqml.python.runtime.window_services import get_acrylic_helper
    from prismqml.python.window import mica_window

    sentinel = object()
    monkeypatch.setattr(mica_window, "get_acrylic_helper", lambda: sentinel)

    assert get_acrylic_helper() is sentinel


def test_native_window_hook_facade_delegates_to_window(monkeypatch):
    from prismqml.python.runtime.window_services import get_native_window_hook
    from prismqml.python.window import native_window

    sentinel = object()
    monkeypatch.setattr(native_window, "get_native_window_hook", lambda: sentinel)

    assert get_native_window_hook() is sentinel


def test_clipboard_helper_facade_delegates_to_provider(monkeypatch):
    from prismqml.python.providers import clipboard
    from prismqml.python.runtime.window_services import get_clipboard_helper

    sentinel = object()
    monkeypatch.setattr(clipboard, "get_clipboard_helper", lambda: sentinel)

    assert get_clipboard_helper() is sentinel
