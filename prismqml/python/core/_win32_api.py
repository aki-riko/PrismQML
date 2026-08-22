# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Shared pointer-width Win32 declarations. 共享指针宽度 Win32 声明。"""

import ctypes
from ctypes import wintypes


def bind_set_window_pos(user32):
    """Bind one user32.SetWindowPos function. 绑定 user32.SetWindowPos 函数。"""
    function = user32.SetWindowPos
    function.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    function.restype = wintypes.BOOL
    return function
