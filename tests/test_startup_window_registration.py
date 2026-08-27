# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Startup-window registration contracts. 纯 QML 启动窗口注册合同。"""

from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def test_app_exposes_public_startup_window_attach():
    from prismqml.python.window.app import App

    calls = []
    controller = SimpleNamespace(
        _main_window=None,
        attach_to_window=lambda engine, window: calls.append((engine, window)) or True,
    )
    app = object.__new__(App)
    app._engine = object()
    app._fast_splash = controller
    window = object()

    assert app.attach_startup_window(window) is True
    controller._main_window = window
    assert app.attach_startup_window(object()) is False
    assert calls == [(app._engine, window)]


def test_qml_startup_bridge_forwards_to_public_app_api():
    from prismqml.python.runtime.startup_window import StartupWindowRegistrar

    calls = []
    owner = SimpleNamespace(
        attach_startup_window=lambda window: calls.append(window) or True
    )
    registrar = StartupWindowRegistrar(owner, None)
    window = object()

    assert registrar.registerStartupWindow(window) is True
    assert calls == [window]
    assert registrar.registerStartupWindow(None) is False


def test_navigation_window_core_registers_only_pure_qml_windows():
    source = (
        ROOT / "prismqml/PrismQML/NavigationWindowCore.qml"
    ).read_text(encoding="utf-8")

    assert "function _registerStartupWindow()" in source
    assert "PrismQmlStartup.registerStartupWindow(window)" in source
    assert "if (_pythonPageMode" in source
    assert "_registerStartupWindow()" in source
