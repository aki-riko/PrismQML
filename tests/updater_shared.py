# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared updater test support: module aliases and Windows ShellExecute fakes.
Updater 测试共用支撑：Windows ShellExecute 假实现与补丁助手（不真启动进程、不碰网络）。
"""

from types import SimpleNamespace

import prismqml.python.core._updater_install as install_module
import prismqml.python.core.updater as updater_module


# ==================== Windows ShellExecute 假实现 (原 test_updater.py 整段迁移) ====================
class _FakeShellExecute:
    def __init__(self, result=42, error=None):
        self._result = result
        self._error = error
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        if self._error is not None:
            raise self._error
        return self._result


def _patch_windows_shell(monkeypatch, shell_execute):
    wintypes = SimpleNamespace(
        HWND=object(),
        LPCWSTR=object(),
        HINSTANCE=object(),
    )
    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(
            shell32=SimpleNamespace(ShellExecuteW=shell_execute),
        ),
        wintypes=wintypes,
        c_int=object(),
        ArgumentError=type("ArgumentError", (Exception,), {}),
    )
    monkeypatch.setattr(updater_module.sys, "platform", "win32")
    monkeypatch.setattr(install_module, "ctypes", fake_ctypes)
    monkeypatch.setattr(install_module, "wintypes", wintypes)
    return fake_ctypes, wintypes


def _assert_shell_execute_contract(
    shell_execute,
    fake_ctypes,
    wintypes,
    installer,
):
    assert shell_execute.argtypes == [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        fake_ctypes.c_int,
    ]
    assert shell_execute.restype is wintypes.HINSTANCE
    assert shell_execute.calls == [(
        None, "open", str(installer), "/NORESTART", None, 1,
    )]
