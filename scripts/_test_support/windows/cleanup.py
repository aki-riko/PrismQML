# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Windows test-boundary cleanup helpers. Windows 测试边界清理辅助函数。"""

from __future__ import annotations

import ctypes

if __package__:
    from . import api as _api
else:
    import api as _api


CleanupIssue = tuple[str, BaseException]


def last_error(operation: str) -> OSError:
    error_code = ctypes.get_last_error()
    if not error_code:
        return OSError(f"{operation} failed without a Windows error code")
    error = ctypes.WinError(error_code)
    error.filename = operation
    return error


def close_handle(kernel32, handle) -> None:
    if not handle or handle == _api.INVALID_HANDLE_VALUE:
        return
    ctypes.set_last_error(0)
    if not kernel32.CloseHandle(handle):
        raise last_error("CloseHandle")


def capture_close_handle(kernel32, handle) -> OSError | None:
    try:
        close_handle(kernel32, handle)
    except OSError as error:
        return error
    return None


def describe_exception(error: BaseException) -> str:
    descriptions = []
    seen = set()
    current = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        detail = str(current) or type(current).__name__
        descriptions.append(f"{type(current).__name__}: {detail}")
        next_error = current.__cause__
        if next_error is None and not current.__suppress_context__:
            next_error = current.__context__
        current = next_error
    return " <- ".join(descriptions)


def raise_cleanup_errors(
    issues: list[CleanupIssue],
    primary_error: BaseException | None = None,
) -> None:
    if not issues:
        return
    details = "; ".join(f"{operation}: {error}" for operation, error in issues)
    cleanup_error = RuntimeError(f"Windows cleanup failed: {details}")
    cleanup_error.__cause__ = issues[0][1]
    cleanup_error.__suppress_context__ = True
    if primary_error is not None:
        primary_error.__cause__ = cleanup_error
        primary_error.__suppress_context__ = True
        raise primary_error
    raise cleanup_error
