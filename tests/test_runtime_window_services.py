# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window service runtime contracts. 窗口服务 runtime 合同。"""


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
