# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Private Windows Desktop with a hidden enumeration sentinel.

带隐藏枚举哨兵的 Windows 私有 Desktop。
"""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

if __package__:
    from . import _windows_test_api as _api
    from ._windows_test_cleanup import CleanupIssue, last_error
else:
    import _windows_test_api as _api
    from _windows_test_cleanup import CleanupIssue, last_error


class _PrivateDesktop:
    def __init__(self, kernel32, user32, name: str):
        self.kernel32 = kernel32
        self.user32 = user32
        self.name = name
        self.handle = None
        self.sentinel = None
        self.setup_error = None
        self.cleanup_issues: list[CleanupIssue] = []
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.thread = None

    def create(self) -> None:
        self.handle = self.user32.CreateDesktopW(
            self.name, None, None, 0, _api.DESKTOP_REQUIRED_ACCESS, None
        )
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self._start_sentinel()

    def _start_sentinel(self) -> None:
        self.thread = threading.Thread(
            target=self._sentinel_worker,
            name=f"{self.name}-sentinel",
            daemon=True,
        )
        self.thread.start()
        if not self.ready.wait(_api.WINDOWS_JOB_CLEANUP_WAIT_SECONDS):
            self.stop.set()
            raise RuntimeError("desktop sentinel setup timed out")
        if self.setup_error is not None:
            error = self.setup_error
            self.setup_error = None
            raise error

    def _sentinel_worker(self) -> None:
        try:
            original_desktop = self._set_desktop_and_create_sentinel()
        except OSError as error:
            self.setup_error = error
            self.ready.set()
            return
        self.ready.set()
        while not self.stop.wait(_api.WINDOW_POLL_INTERVAL_SECONDS):
            self._pump_messages()
        self._pump_messages()
        self._destroy_sentinel_and_restore(original_desktop)

    def _set_desktop_and_create_sentinel(self):
        original_desktop = self._current_thread_desktop()
        ctypes.set_last_error(0)
        if not self.user32.SetThreadDesktop(self.handle):
            raise last_error("SetThreadDesktop")
        try:
            self._create_sentinel_window()
        except OSError:
            ctypes.set_last_error(0)
            if not self.user32.SetThreadDesktop(original_desktop):
                self.cleanup_issues.append(
                    ("restore sentinel thread desktop", last_error("SetThreadDesktop"))
                )
            raise
        return original_desktop

    def _current_thread_desktop(self):
        thread_id = self.kernel32.GetCurrentThreadId()
        ctypes.set_last_error(0)
        original_desktop = self.user32.GetThreadDesktop(thread_id)
        if not original_desktop:
            raise last_error("GetThreadDesktop")
        return original_desktop

    def _create_sentinel_window(self) -> None:
        ctypes.set_last_error(0)
        self.sentinel = self.user32.CreateWindowExW(
            0,
            "STATIC",
            "PrismQML test desktop sentinel",
            0,
            0,
            0,
            1,
            1,
            None,
            None,
            None,
            None,
        )
        if not self.sentinel:
            raise last_error("CreateWindowExW")

    def _pump_messages(self) -> None:
        message = wintypes.MSG()
        while self.user32.PeekMessageW(
            ctypes.byref(message), None, 0, 0, _api.PM_REMOVE
        ):
            self.user32.TranslateMessage(ctypes.byref(message))
            self.user32.DispatchMessageW(ctypes.byref(message))

    def _destroy_sentinel_and_restore(self, original_desktop) -> None:
        ctypes.set_last_error(0)
        if not self.user32.DestroyWindow(self.sentinel):
            self.cleanup_issues.append(
                ("destroy desktop sentinel", last_error("DestroyWindow"))
            )
        else:
            self.sentinel = None
        ctypes.set_last_error(0)
        if not self.user32.SetThreadDesktop(original_desktop):
            self.cleanup_issues.append(
                ("restore sentinel thread desktop", last_error("SetThreadDesktop"))
            )

    def _stop_sentinel(self) -> list[CleanupIssue]:
        issues: list[CleanupIssue] = []
        if self.thread is None:
            return issues
        self.stop.set()
        self.thread.join(_api.WINDOWS_JOB_CLEANUP_WAIT_SECONDS)
        if self.thread.is_alive():
            issues.append(("stop desktop sentinel", RuntimeError("thread did not exit")))
            return issues
        self.thread = None
        if self.setup_error is not None:
            issues.append(("set up desktop sentinel", self.setup_error))
            self.setup_error = None
        issues.extend(self.cleanup_issues)
        self.cleanup_issues.clear()
        return issues

    def close(self) -> list[CleanupIssue]:
        issues = self._stop_sentinel()
        if not self.handle:
            return issues
        ctypes.set_last_error(0)
        if self.user32.CloseDesktop(self.handle):
            self.handle = None
        else:
            issues.append(("close private desktop", last_error("CloseDesktop")))
        return issues
