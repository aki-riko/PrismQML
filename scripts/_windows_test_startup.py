# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Create a suspended Windows test process with an explicit handle list.

使用显式句柄列表创建挂起的 Windows 测试进程。
"""

from __future__ import annotations

import ctypes
import os
import subprocess
from collections.abc import Sequence
from ctypes import wintypes

if __package__:
    from . import _windows_test_api as _api
else:
    import _windows_test_api as _api


def _startup_info(
    desktop_name: str,
    standard_handles: tuple[int, int, int],
) -> _api._StartupInfoExW:
    startup = _api._StartupInfoExW()
    startup.StartupInfo.cb = ctypes.sizeof(startup)
    startup.StartupInfo.lpDesktop = desktop_name
    (
        startup.StartupInfo.hStdInput,
        startup.StartupInfo.hStdOutput,
        startup.StartupInfo.hStdError,
    ) = standard_handles
    startup.StartupInfo.dwFlags = _api.STARTF_USESTDHANDLES
    return startup


def _initialize_attribute_list(kernel32) -> tuple[ctypes.Array, ctypes.c_void_p]:
    attribute_size = ctypes.c_size_t()
    ctypes.set_last_error(0)
    sizing_result = kernel32.InitializeProcThreadAttributeList(
        None, 1, 0, ctypes.byref(attribute_size)
    )
    sizing_error = ctypes.get_last_error()
    if sizing_result:
        raise RuntimeError("attribute-list sizing unexpectedly succeeded")
    if sizing_error != _api.ERROR_INSUFFICIENT_BUFFER:
        if sizing_error:
            raise ctypes.WinError(sizing_error)
        raise OSError("attribute-list sizing failed without a Windows error code")
    if attribute_size.value == 0:
        raise RuntimeError("attribute-list sizing returned zero bytes")
    storage = ctypes.create_string_buffer(attribute_size.value)
    attribute_list = ctypes.cast(storage, ctypes.c_void_p)
    if not kernel32.InitializeProcThreadAttributeList(
        attribute_list, 1, 0, ctypes.byref(attribute_size)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return storage, attribute_list


def _update_handle_attribute(
    kernel32,
    attribute_list,
    standard_handles: tuple[int, int, int],
) -> ctypes.Array:
    handle_values = (wintypes.HANDLE * len(standard_handles))(*standard_handles)
    if not kernel32.UpdateProcThreadAttribute(
        attribute_list,
        0,
        _api.PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
        ctypes.cast(handle_values, ctypes.c_void_p),
        ctypes.sizeof(handle_values),
        None,
        None,
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return handle_values


def _create_process(kernel32, command: Sequence[str], startup) -> _api._ProcessInformation:
    command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
    process = _api._ProcessInformation()
    creation_flags = _api.CREATE_SUSPENDED | _api.EXTENDED_STARTUPINFO_PRESENT
    if not kernel32.CreateProcessW(
        None,
        command_line,
        None,
        None,
        True,
        creation_flags,
        None,
        os.getcwd(),
        ctypes.cast(ctypes.byref(startup), ctypes.POINTER(_api._StartupInfoW)),
        ctypes.byref(process),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return process


def create_suspended_process(
    kernel32,
    command: Sequence[str],
    desktop_name: str,
    standard_handles: tuple[int, int, int],
) -> _api._ProcessInformation:
    startup = _startup_info(desktop_name, standard_handles)
    storage, attribute_list = _initialize_attribute_list(kernel32)
    handle_values = None
    try:
        handle_values = _update_handle_attribute(
            kernel32, attribute_list, standard_handles
        )
        startup.lpAttributeList = attribute_list.value
        return _create_process(kernel32, command, startup)
    finally:
        kernel32.DeleteProcThreadAttributeList(attribute_list)
        startup.lpAttributeList = None
        _ = storage, handle_values
