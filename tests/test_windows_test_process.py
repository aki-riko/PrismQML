# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Windows private Desktop and Job filtering sentinels.

Windows 私有桌面与 Job 过滤安全哨兵。
"""

from __future__ import annotations

import ctypes
import logging
import subprocess
import sys
import time
from ctypes import wintypes
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows private Desktop only",
)

if sys.platform == "win32":
    import scripts._windows_test_cleanup as windows_test_cleanup
    import scripts._windows_test_process as windows_test_process
    from scripts.test_process import (
        TEST_CLEANUP_FAILURE_EXIT_CODE,
        TEST_TIMEOUT_EXIT_CODE,
        TEST_VISIBLE_WINDOW_EXIT_CODE,
    )
    from scripts._windows_test_api import (
        CREATE_SUSPENDED,
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
        WAIT_FAILED,
        WAIT_OBJECT_0,
        WAIT_TIMEOUT,
        _JobExtendedLimitInformation,
        _ProcessInformation,
        _StartupInfoW,
        _WindowEnumCallback,
    )
    from scripts._windows_test_process import _WindowsTestBoundary


ERROR_INVALID_HANDLE = 6
ERROR_ACCESS_DENIED = 5
HANDLE_FLAG_INHERIT = 0x00000001
UNRELATED_MESSAGE_BOX_CODE = """
import ctypes

ctypes.windll.user32.MessageBoxW(
    None,
    "same desktop unrelated sentinel",
    "PrismQML unrelated sentinel",
    0,
)
"""


class _TrackingBoundary:
    def __init__(self, _command):
        self.closed = False

    def start(self):
        pass

    def close(self):
        self.closed = True


class _FailingCleanupBoundary:
    def __init__(self, _command):
        pass

    def start(self):
        pass

    def close(self):
        raise RuntimeError("synthetic cleanup failure")


class _StartAndCleanupFailureBoundary:
    def __init__(self, primary_error=None):
        self.primary_error = primary_error or ValueError("primary create failure")

    def start(self):
        return _WindowsTestBoundary.start(self)

    def close(self):
        pass

    def _create_desktop(self):
        pass

    def _create_job(self):
        pass

    def _create_suspended_process(self):
        raise self.primary_error

    def _assign_and_resume_process(self):
        pass

    def _stop_failed_start_process(self):
        return []

    def _release_startup_handles(self):
        return [("close standard handle", OSError("synthetic close failure"))]


class _QueryAndCloseFailureKernel32:
    def OpenProcess(self, *_args):
        return 123

    def IsProcessInJob(self, *_args):
        ctypes.set_last_error(ERROR_ACCESS_DENIED)
        return False

    def CloseHandle(self, _handle):
        ctypes.set_last_error(ERROR_INVALID_HANDLE)
        return False


def _create_kill_on_close_job(boundary):
    job = boundary.kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = _JobExtendedLimitInformation()
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not boundary.kernel32.SetInformationJobObject(
        job,
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes.byref(limits),
        ctypes.sizeof(limits),
    ):
        boundary.kernel32.CloseHandle(job)
        raise ctypes.WinError(ctypes.get_last_error())
    return job


def _create_suspended_unrelated_process(boundary) -> _ProcessInformation:
    command_line = ctypes.create_unicode_buffer(
        subprocess.list2cmdline([sys.executable, "-c", UNRELATED_MESSAGE_BOX_CODE])
    )
    startup = _StartupInfoW()
    startup.cb = ctypes.sizeof(startup)
    startup.lpDesktop = boundary.desktop_name
    process = _ProcessInformation()
    if not boundary.kernel32.CreateProcessW(
        None, command_line, None, None, False, CREATE_SUSPENDED,
        None, None, ctypes.byref(startup), ctypes.byref(process)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return process


def _terminate_unrelated_process(boundary, process, job) -> None:
    boundary.kernel32.TerminateProcess(process.hProcess, 1)
    boundary.kernel32.WaitForSingleObject(process.hProcess, 5000)
    boundary.kernel32.CloseHandle(process.hThread)
    boundary.kernel32.CloseHandle(process.hProcess)
    boundary.kernel32.CloseHandle(job)


def _assign_and_resume_unrelated(boundary, process, job) -> None:
    try:
        if not boundary.kernel32.AssignProcessToJobObject(job, process.hProcess):
            raise ctypes.WinError(ctypes.get_last_error())
        if boundary.kernel32.ResumeThread(process.hThread) == WAIT_FAILED:
            raise ctypes.WinError(ctypes.get_last_error())
    except BaseException:
        _terminate_unrelated_process(boundary, process, job)
        raise


def _start_unrelated_message_box(boundary) -> tuple[_ProcessInformation, int]:
    job = _create_kill_on_close_job(boundary)
    try:
        process = _create_suspended_unrelated_process(boundary)
    except OSError:
        boundary.kernel32.CloseHandle(job)
        raise
    _assign_and_resume_unrelated(boundary, process, job)
    return process, job


def _visible_window_owner(boundary, expected_title: str) -> int | None:
    owner_process_id = None

    @_WindowEnumCallback
    def collect(window, _parameter):
        nonlocal owner_process_id
        if not boundary.user32.IsWindowVisible(window):
            return True
        owner = wintypes.DWORD()
        boundary.user32.GetWindowThreadProcessId(window, ctypes.byref(owner))
        title_length = boundary.user32.GetWindowTextLengthW(window)
        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        boundary.user32.GetWindowTextW(
            window,
            title_buffer,
            len(title_buffer),
        )
        if title_buffer.value == expected_title:
            owner_process_id = owner.value
            return False
        return True

    ctypes.set_last_error(0)
    boundary.user32.EnumDesktopWindows(boundary.desktop, collect, 0)
    error_code = ctypes.get_last_error()
    if owner_process_id is None and error_code:
        raise ctypes.WinError(error_code)
    return owner_process_id


def _wait_for_window_owner(boundary, title: str) -> int | None:
    deadline = time.monotonic() + 5
    owner_process_id = None
    while owner_process_id is None and time.monotonic() < deadline:
        owner_process_id = _visible_window_owner(boundary, title)
        time.sleep(0.025)
    return owner_process_id


def _cleanup_unrelated(boundary, process, job) -> None:
    if job:
        boundary.kernel32.TerminateJobObject(job, 0)
    if process is not None and process.hProcess:
        wait_result = boundary.kernel32.WaitForSingleObject(process.hProcess, 5000)
        assert wait_result == WAIT_OBJECT_0
        boundary.kernel32.CloseHandle(process.hThread)
        boundary.kernel32.CloseHandle(process.hProcess)
    if job:
        boundary.kernel32.CloseHandle(job)
    if boundary.job:
        assert boundary.terminate(0)
    boundary.close()


def _create_hidden_static_window(user32, title: str):
    window = user32.CreateWindowExW(
        0, "STATIC", title, 0, 0, 0, 1, 1, None, None, None, None
    )
    assert window
    return window


def _run_isolated(command: list[str]) -> int:
    return windows_test_process.run_isolated_windows_child(
        command,
        10,
        logging.getLogger(__name__),
        timeout_exit_code=TEST_TIMEOUT_EXIT_CODE,
        cleanup_failure_exit_code=TEST_CLEANUP_FAILURE_EXIT_CODE,
        visible_window_exit_code=TEST_VISIBLE_WINDOW_EXIT_CODE,
    )


def _raise_keyboard_interrupt(*_args, **_kwargs):
    raise KeyboardInterrupt


def _event_kernel32():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateEventW.argtypes = [
        ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR
    ]
    kernel32.CreateEventW.restype = wintypes.HANDLE
    kernel32.SetHandleInformation.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD
    ]
    kernel32.SetHandleInformation.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def _excluded_handle_child_code(event: int) -> str:
    return f"""
import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.SetEvent.argtypes = [ctypes.c_void_p]
kernel32.SetEvent.restype = ctypes.c_int
result = kernel32.SetEvent(ctypes.c_void_p({event}))
if not result and ctypes.get_last_error() != {ERROR_INVALID_HANDLE}:
    raise SystemExit(92)
"""


def test_visible_unrelated_process_on_same_desktop_is_ignored():
    boundary = _WindowsTestBoundary(
        [sys.executable, "-c", "import time; time.sleep(30)"]
    )
    unrelated = None
    unrelated_job = None
    try:
        boundary.start()
        unrelated, unrelated_job = _start_unrelated_message_box(boundary)
        owner_process_id = _wait_for_window_owner(
            boundary, "PrismQML unrelated sentinel"
        )

        assert owner_process_id is not None
        assert boundary._job_process_details(owner_process_id) is None
        assert boundary.visible_job_windows() == []
    finally:
        _cleanup_unrelated(boundary, unrelated, unrelated_job)


def test_private_desktop_sentinel_works_when_caller_thread_owns_window():
    boundary = _WindowsTestBoundary([sys.executable, "-c", "pass"])
    caller_window = _create_hidden_static_window(
        boundary.user32, "PrismQML caller-thread sentinel"
    )
    try:
        try:
            boundary._create_desktop()

            assert boundary.desktop_sentinel
            assert not boundary.user32.IsWindowVisible(boundary.desktop_sentinel)
            assert boundary.visible_job_windows() == []
        finally:
            boundary.close()
    finally:
        assert boundary.user32.DestroyWindow(caller_window)


def test_desktop_enumeration_failure_without_error_fails_closed():
    def fail_enumeration(_desktop, _callback, _parameter):
        ctypes.set_last_error(0)
        return False

    boundary = object.__new__(_WindowsTestBoundary)
    boundary.private_desktop = SimpleNamespace(handle=1)
    boundary.user32 = SimpleNamespace(EnumDesktopWindows=fail_enumeration)

    with pytest.raises(
        RuntimeError,
        match="EnumDesktopWindows failed without a Windows error code",
    ):
        boundary.visible_job_windows()


def test_close_handle_failure_is_reported():
    def fail_close(_handle):
        ctypes.set_last_error(ERROR_INVALID_HANDLE)
        return False

    with pytest.raises(OSError) as error:
        windows_test_cleanup.close_handle(
            SimpleNamespace(CloseHandle=fail_close),
            123,
        )

    assert error.value.winerror == ERROR_INVALID_HANDLE


def test_start_reports_primary_and_cleanup_failures_together():
    boundary = _StartAndCleanupFailureBoundary()

    with pytest.raises(ValueError) as error:
        boundary.start()

    assert error.value is boundary.primary_error
    assert "synthetic close failure" in str(error.value.__cause__)


def test_process_query_reports_primary_and_close_failures_together():
    boundary = object.__new__(_WindowsTestBoundary)
    boundary.kernel32 = _QueryAndCloseFailureKernel32()
    boundary.job = 1

    with pytest.raises(OSError) as error:
        boundary._job_process_details(42)

    assert error.value.winerror == ERROR_ACCESS_DENIED
    assert "CloseHandle" in str(error.value.__cause__)


def test_keyboard_interrupt_with_cleanup_failure_is_not_swallowed(monkeypatch):
    boundary = _StartAndCleanupFailureBoundary(KeyboardInterrupt())
    monkeypatch.setattr(
        windows_test_process,
        "_WindowsTestBoundary",
        lambda _command: boundary,
    )

    with pytest.raises(KeyboardInterrupt):
        _run_isolated([sys.executable, "-c", "pass"])


def test_unexpected_monitor_error_still_closes_boundary(monkeypatch):
    boundary = _TrackingBoundary([])
    monkeypatch.setattr(
        windows_test_process,
        "_WindowsTestBoundary",
        lambda _command: boundary,
    )
    monkeypatch.setattr(
        windows_test_process,
        "_monitor_windows_child",
        _raise_keyboard_interrupt,
    )

    with pytest.raises(KeyboardInterrupt):
        _run_isolated([sys.executable, "-c", "pass"])

    assert boundary.closed


def test_only_standard_handles_are_inherited_by_test_process():
    kernel32 = _event_kernel32()
    event = kernel32.CreateEventW(None, True, False, None)
    assert event
    try:
        assert kernel32.SetHandleInformation(
            event,
            HANDLE_FLAG_INHERIT,
            HANDLE_FLAG_INHERIT,
        )
        child_code = _excluded_handle_child_code(int(event))
        result = _run_isolated(
            [sys.executable, "-c", child_code]
        )

        # Handle values can be reused for unrelated child objects; parent state proves identity.
        # 句柄值可在子进程复用于无关对象；父 event 状态才证明对象身份。
        assert result == 0
        assert kernel32.WaitForSingleObject(event, 0) == WAIT_TIMEOUT
    finally:
        assert kernel32.CloseHandle(event)


def test_cleanup_failure_overrides_success(monkeypatch):
    monkeypatch.setattr(
        windows_test_process,
        "_WindowsTestBoundary",
        _FailingCleanupBoundary,
    )
    monkeypatch.setattr(
        windows_test_process,
        "_monitor_windows_child",
        lambda *_args, **_kwargs: 0,
    )

    result = _run_isolated(
        [sys.executable, "-c", "raise SystemExit(0)"]
    )

    assert result == TEST_CLEANUP_FAILURE_EXIT_CODE
