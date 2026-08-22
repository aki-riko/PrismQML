# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Shared Win32 declaration contracts. 共享 Win32 声明合同。"""

import ctypes
from ctypes import wintypes

from prismqml.python.core._win32_api import bind_set_window_pos


class _FakeFunction:
    def __init__(self):
        self.argtypes = None
        self.restype = None


class _FakeUser32:
    def __init__(self):
        self.SetWindowPos = _FakeFunction()


def test_bind_set_window_pos_configures_one_pointer_width_signature():
    user32 = _FakeUser32()

    bound = bind_set_window_pos(user32)

    assert bound is user32.SetWindowPos
    assert bound.argtypes == [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    assert bound.restype is wintypes.BOOL
