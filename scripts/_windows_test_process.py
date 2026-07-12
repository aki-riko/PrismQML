# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Windows private-desktop and Job Object test isolation.

Windows 私有桌面与 Job Object 测试隔离。
"""

from __future__ import annotations

import ctypes
import logging
import os
import time
import uuid
from collections.abc import Sequence
from ctypes import wintypes

if __package__:
    from . import _windows_test_api as _api
    from ._windows_test_cleanup import (
        CleanupIssue,
        capture_close_handle,
        close_handle,
        describe_exception,
        raise_cleanup_errors,
    )
    from ._windows_test_desktop import _PrivateDesktop
    from ._windows_test_monitor import _RunOptions, _monitor_windows_child
    from ._windows_test_result import capture_boundary_result, log_boundary_result
    from ._windows_test_startup import create_suspended_process
else:
    import _windows_test_api as _api
    from _windows_test_cleanup import (
        CleanupIssue,
        capture_close_handle,
        close_handle,
        describe_exception,
        raise_cleanup_errors,
    )
    from _windows_test_desktop import _PrivateDesktop
    from _windows_test_monitor import _RunOptions, _monitor_windows_child
    from _windows_test_result import capture_boundary_result, log_boundary_result
    from _windows_test_startup import create_suspended_process


WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS = (
    _api.WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS
)
WINDOWS_JOB_CLEANUP_WAIT_SECONDS = _api.WINDOWS_JOB_CLEANUP_WAIT_SECONDS
PROCESS_IMAGE_PATH_CAPACITY = 32768
WINDOW_CLASS_NAME_CAPACITY = 256


class _WindowsTestBoundary:
    def __init__(self, command: Sequence[str]):
        self.command = tuple(command)
        self.desktop_name = (
            f"{_api.WINDOWS_TEST_DESKTOP_PREFIX}{os.getpid()}-{uuid.uuid4().hex}"
        )
        self.job_name = (
            f"{_api.WINDOWS_TEST_JOB_PREFIX}"
            f"{self.desktop_name.removeprefix(_api.WINDOWS_TEST_DESKTOP_PREFIX)}"
        )
        self.kernel32, self.user32, self.dwmapi, self.get_window_long = (
            _api._windows_libraries()
        )
        self.private_desktop = _PrivateDesktop(
            self.kernel32, self.user32, self.desktop_name
        )
        self.job = None
        self.process = _api._ProcessInformation()
        self.standard_handles: list[int] = []

    @property
    def desktop(self):
        return self.private_desktop.handle

    @property
    def desktop_sentinel(self):
        return self.private_desktop.sentinel

    def _duplicate_standard_handles(self) -> tuple[int, int, int]:
        current_process = self.kernel32.GetCurrentProcess()
        self.standard_handles.clear()
        for identifier in (-10, -11, -12):
            source = self.kernel32.GetStdHandle(identifier & 0xFFFFFFFF)
            if not source or source == _api.INVALID_HANDLE_VALUE:
                raise OSError(f"GetStdHandle({identifier}) returned no handle")
            duplicate = wintypes.HANDLE()
            if not self.kernel32.DuplicateHandle(
                current_process,
                source,
                current_process,
                ctypes.byref(duplicate),
                0,
                True,
                _api.DUPLICATE_SAME_ACCESS,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            self.standard_handles.append(int(duplicate.value))
        return tuple(self.standard_handles)

    def _create_desktop(self) -> None:
        self.private_desktop.create()

    def _create_job(self) -> None:
        ctypes.set_last_error(0)
        self.job = self.kernel32.CreateJobObjectW(None, self.job_name)
        if not self.job:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == _api.ERROR_ALREADY_EXISTS:
            existing_job = self.job
            self.job = None
            close_handle(self.kernel32, existing_job)
            raise RuntimeError(f"Windows test Job already exists: {self.job_name}")
        limits = _api._JobExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = (
            _api.JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION
            | _api.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        if not self.kernel32.SetInformationJobObject(
            self.job,
            _api.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

    def _create_suspended_process(self) -> None:
        standard_handles = self._duplicate_standard_handles()
        self.process = create_suspended_process(
            self.kernel32,
            self.command,
            self.desktop_name,
            standard_handles,
        )

    def _assign_and_resume_process(self) -> None:
        if not self.kernel32.AssignProcessToJobObject(
            self.job,
            self.process.hProcess,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if self.kernel32.ResumeThread(self.process.hThread) == _api.WAIT_FAILED:
            raise ctypes.WinError(ctypes.get_last_error())

    def _release_startup_handles(self) -> list[CleanupIssue]:
        issues: list[CleanupIssue] = []
        thread_error = capture_close_handle(self.kernel32, self.process.hThread)
        if thread_error is None:
            self.process.hThread = None
        else:
            issues.append(("close process thread handle", thread_error))
        remaining_handles = []
        for index, handle in enumerate(self.standard_handles):
            error = capture_close_handle(self.kernel32, handle)
            if error is not None:
                remaining_handles.append(handle)
                issues.append((f"close standard handle {index}", error))
        self.standard_handles = remaining_handles
        return issues

    def _stop_failed_start_process(self) -> list[CleanupIssue]:
        if not self.process.hProcess:
            return []
        issues: list[CleanupIssue] = []
        if not self.kernel32.TerminateProcess(self.process.hProcess, 1):
            issues.append(
                ("terminate suspended test process", ctypes.WinError(ctypes.get_last_error()))
            )
        wait_result = self.kernel32.WaitForSingleObject(
            self.process.hProcess,
            int(_api.WINDOWS_JOB_CLEANUP_WAIT_SECONDS * 1000),
        )
        if wait_result != _api.WAIT_OBJECT_0:
            issues.append(
                ("wait for suspended test process", RuntimeError(str(wait_result)))
            )
        return issues

    def start(self) -> None:
        self._create_desktop()
        self._create_job()
        primary_error = None
        issues: list[CleanupIssue] = []
        try:
            self._create_suspended_process()
            self._assign_and_resume_process()
        except BaseException as error:
            primary_error = error
            issues.extend(self._stop_failed_start_process())
        issues.extend(self._release_startup_handles())
        if primary_error is not None:
            raise_cleanup_errors(issues, primary_error)
            raise primary_error
        raise_cleanup_errors(issues)

    def active_process_count(self) -> int:
        accounting = _api._JobBasicAccountingInformation()
        returned = wintypes.DWORD()
        if not self.kernel32.QueryInformationJobObject(
            self.job,
            _api.JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
            ctypes.byref(accounting),
            ctypes.sizeof(accounting),
            ctypes.byref(returned),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(accounting.ActiveProcesses)

    def root_exit_code(self) -> int | None:
        wait_result = self.kernel32.WaitForSingleObject(
            self.process.hProcess,
            0,
        )
        if wait_result != _api.WAIT_OBJECT_0:
            if wait_result == _api.WAIT_TIMEOUT:
                return None
            if wait_result == _api.WAIT_FAILED:
                raise ctypes.WinError(ctypes.get_last_error())
            raise RuntimeError(f"unexpected Windows wait result: {wait_result}")
        exit_code = wintypes.DWORD()
        if not self.kernel32.GetExitCodeProcess(
            self.process.hProcess,
            ctypes.byref(exit_code),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(exit_code.value)

    def _process_creation_ticks(self, process) -> int | None:
        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        if not self.kernel32.GetProcessTimes(
            process,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            return None
        return (int(creation.dwHighDateTime) << 32) | int(
            creation.dwLowDateTime
        )

    def _process_image_path(self, process) -> str | None:
        capacity = wintypes.DWORD(PROCESS_IMAGE_PATH_CAPACITY)
        image_buffer = ctypes.create_unicode_buffer(capacity.value)
        if not self.kernel32.QueryFullProcessImageNameW(
            process,
            0,
            image_buffer,
            ctypes.byref(capacity),
        ):
            return None
        return image_buffer.value

    def _job_process_details(self, process_id: int) -> dict | None:
        process = self.kernel32.OpenProcess(
            _api.PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            process_id,
        )
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            details = self._read_job_process_details(process, process_id)
        except BaseException as primary_error:
            close_error = capture_close_handle(self.kernel32, process)
            if close_error is not None:
                raise_cleanup_errors(
                    [("close inspected process handle", close_error)],
                    primary_error,
                )
            raise
        close_handle(self.kernel32, process)
        return details

    def _read_job_process_details(self, process, process_id: int) -> dict | None:
        in_job = wintypes.BOOL()
        if not self.kernel32.IsProcessInJob(
            process, self.job, ctypes.byref(in_job)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if not in_job.value:
            return None
        return {
            "process_id": process_id,
            "process_creation_ticks": self._process_creation_ticks(process),
            "image_path": self._process_image_path(process),
        }

    def _window_is_cloaked(self, window) -> bool:
        cloaked = wintypes.DWORD()
        result = self.dwmapi.DwmGetWindowAttribute(
            window,
            _api.DWMWA_CLOAKED,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked),
        )
        return result >= 0 and bool(cloaked.value)

    def _window_text(self, window) -> str:
        length = self.user32.GetWindowTextLengthW(window)
        buffer = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(window, buffer, len(buffer))
        return buffer.value

    def _window_class_name(self, window) -> str:
        buffer = ctypes.create_unicode_buffer(WINDOW_CLASS_NAME_CAPACITY)
        self.user32.GetClassNameW(window, buffer, len(buffer))
        return buffer.value

    def _visible_job_window_details(
        self,
        window,
    ) -> dict | None:
        if not self.user32.IsWindowVisible(window):
            return None
        if self._window_is_cloaked(window):
            return None
        process_id = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(window, ctypes.byref(process_id))
        process_details = self._job_process_details(process_id.value)
        if process_details is None:
            return None
        return {
            "desktop": self.desktop_name,
            "hwnd": int(window),
            "title": self._window_text(window),
            "class_name": self._window_class_name(window),
            "style": int(self.get_window_long(window, _api.GWL_STYLE)),
            "extended_style": int(
                self.get_window_long(window, _api.GWL_EXSTYLE)
            ),
            **process_details,
        }

    def visible_job_windows(self) -> list[dict]:
        windows: list[dict] = []
        callback_errors: list[BaseException] = []

        @_api._WindowEnumCallback
        def collect(window, _parameter):
            try:
                details = self._visible_job_window_details(window)
                if details is not None:
                    windows.append(details)
            except BaseException as error:
                callback_errors.append(error)
                return False
            return True

        ctypes.set_last_error(0)
        result = self.user32.EnumDesktopWindows(self.desktop, collect, 0)
        if callback_errors:
            raise callback_errors[0]
        if not result:
            error_code = ctypes.get_last_error()
            if error_code:
                raise ctypes.WinError(error_code)
            raise RuntimeError(
                "EnumDesktopWindows failed without a Windows error code"
            )
        return windows

    def terminate(self, exit_code: int) -> bool:
        if self.active_process_count() == 0:
            return True
        if not self.kernel32.TerminateJobObject(self.job, exit_code):
            return False
        return self.wait_until_empty(WINDOWS_JOB_CLEANUP_WAIT_SECONDS)

    def wait_until_empty(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.active_process_count() == 0:
                return True
            time.sleep(_api.WINDOW_POLL_INTERVAL_SECONDS)
        return self.active_process_count() == 0

    def _close_standard_handles(self) -> list[CleanupIssue]:
        issues: list[CleanupIssue] = []
        remaining_handles = []
        for index, handle in enumerate(self.standard_handles):
            error = capture_close_handle(self.kernel32, handle)
            if error is not None:
                remaining_handles.append(handle)
                issues.append((f"close standard handle {index}", error))
        self.standard_handles = remaining_handles
        return issues

    def _terminate_and_close_job(self) -> list[CleanupIssue]:
        if not self.job:
            return []
        issues: list[CleanupIssue] = []
        try:
            if self.active_process_count() != 0:
                if not self.kernel32.TerminateJobObject(self.job, 1):
                    raise ctypes.WinError(ctypes.get_last_error())
                if not self.wait_until_empty(WINDOWS_JOB_CLEANUP_WAIT_SECONDS):
                    raise RuntimeError(
                        "Windows Job still has active processes during cleanup"
                    )
        except (OSError, RuntimeError) as error:
            issues.append(("terminate Windows Job", error))
        close_error = capture_close_handle(self.kernel32, self.job)
        if close_error is None:
            self.job = None
        else:
            issues.append(("close Windows Job handle", close_error))
        return issues

    def _close_process_thread(self) -> list[CleanupIssue]:
        error = capture_close_handle(self.kernel32, self.process.hThread)
        if error is None:
            self.process.hThread = None
            return []
        return [("close process thread handle", error)]

    def _close_process_handle(self) -> list[CleanupIssue]:
        error = capture_close_handle(self.kernel32, self.process.hProcess)
        if error is None:
            self.process.hProcess = None
            return []
        return [("close process handle", error)]

    def close(self) -> None:
        issues = self._close_standard_handles()
        for cleanup in (
            self._terminate_and_close_job,
            self._close_process_thread,
            self._close_process_handle,
            self.private_desktop.close,
        ):
            issues.extend(cleanup())
        raise_cleanup_errors(issues)


def _close_boundary(boundary, logger: logging.Logger) -> bool:
    try:
        boundary.close()
    except (OSError, RuntimeError) as error:
        logger.error(
            "[test-process] Windows isolation cleanup failed: %s",
            describe_exception(error),
        )
        return False
    return True


def _run_boundary(boundary, options: _RunOptions) -> int:
    try:
        boundary.start()
        return _monitor_windows_child(boundary, options)
    except (OSError, RuntimeError) as error:
        options.logger.error(
            "[test-process] Windows isolation failed: %s",
            describe_exception(error),
        )
        return options.cleanup_failure_exit_code


def run_isolated_windows_child(
    command: Sequence[str],
    timeout: float | None,
    logger: logging.Logger,
    *,
    timeout_exit_code: int,
    cleanup_failure_exit_code: int,
    visible_window_exit_code: int,
) -> int:
    """Run privately and fail when polling detects visible Job windows."""
    boundary = _WindowsTestBoundary(command)
    options = _RunOptions(
        timeout,
        logger,
        timeout_exit_code,
        cleanup_failure_exit_code,
        visible_window_exit_code,
    )
    try:
        result = _run_boundary(boundary, options)
        snapshot = capture_boundary_result(boundary)
    finally:
        cleanup_succeeded = _close_boundary(boundary, logger)
    if not cleanup_succeeded:
        result = cleanup_failure_exit_code
    log_boundary_result(snapshot, result, cleanup_succeeded, logger)
    return result
