# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Non-interactive test process launcher. 无交互测试进程启动器。"""

from __future__ import annotations

import argparse
import ctypes
import logging
import math
import os
import signal
import subprocess
import sys
import time
from collections.abc import Sequence


SEM_FAILCRITICALERRORS = 0x0001
SEM_NOGPFAULTERRORBOX = 0x0002
SEM_NOOPENFILEERRORBOX = 0x8000
WER_FAULT_REPORTING_FLAG_QUEUE = 0x0002
WER_FAULT_REPORTING_ALWAYS_SHOW_UI = 0x0010
WER_FAULT_REPORTING_NO_UI = 0x0020
HRESULT_ERROR_NOT_FOUND = 0x80070490
WINDOWS_ERROR_MODE_FLAGS = (
    SEM_FAILCRITICALERRORS
    | SEM_NOGPFAULTERRORBOX
    | SEM_NOOPENFILEERRORBOX
)
TEST_TIMEOUT_EXIT_CODE = 124
TEST_CLEANUP_FAILURE_EXIT_CODE = 125
PROCESS_GRACEFUL_WAIT_SECONDS = 2
PROCESS_FORCE_KILL_WAIT_SECONDS = 5
PROCESS_GROUP_POLL_INTERVAL_SECONDS = 0.05
WINDOWS_TASKKILL_TIMEOUT_SECONDS = 30
LOGGER = logging.getLogger(__name__)


def _hresult_failed(result: int) -> bool:
    return bool(result & 0x80000000)


def _windows_error_library():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    kernel32.GetErrorMode.argtypes = []
    kernel32.GetErrorMode.restype = ctypes.c_uint
    kernel32.SetErrorMode.argtypes = [ctypes.c_uint]
    kernel32.SetErrorMode.restype = ctypes.c_uint
    kernel32.WerGetFlags.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    kernel32.WerGetFlags.restype = ctypes.c_long
    kernel32.WerSetFlags.argtypes = [ctypes.c_uint32]
    kernel32.WerSetFlags.restype = ctypes.c_long
    return kernel32


def _windows_error_policy() -> tuple[int, int]:
    kernel32 = _windows_error_library()
    error_mode = int(kernel32.GetErrorMode())
    wer_flags = ctypes.c_uint32()
    result = int(
        kernel32.WerGetFlags(kernel32.GetCurrentProcess(), ctypes.byref(wer_flags))
    )
    if result & 0xFFFFFFFF == HRESULT_ERROR_NOT_FOUND:
        return error_mode, 0
    if _hresult_failed(result):
        raise OSError(f"WerGetFlags failed with HRESULT 0x{result & 0xFFFFFFFF:08X}")
    return error_mode, int(wer_flags.value)


def _configure_windows_error_ui() -> None:
    kernel32 = _windows_error_library()
    error_mode, wer_flags = _windows_error_policy()
    # SetErrorMode is inherited; WerSetFlags applies only to the current process.
    # ErrorMode 可由后代继承；WerSetFlags 只作用于当前进程。
    target_error_mode = error_mode | WINDOWS_ERROR_MODE_FLAGS
    target_wer_flags = (
        wer_flags & ~WER_FAULT_REPORTING_ALWAYS_SHOW_UI
    ) | WER_FAULT_REPORTING_FLAG_QUEUE | WER_FAULT_REPORTING_NO_UI
    result = int(kernel32.WerSetFlags(target_wer_flags))
    if _hresult_failed(result):
        raise OSError(f"WerSetFlags failed with HRESULT 0x{result & 0xFFFFFFFF:08X}")
    kernel32.SetErrorMode(target_error_mode)

    current_error_mode, current_wer_flags = _windows_error_policy()
    if (
        current_error_mode & WINDOWS_ERROR_MODE_FLAGS
        != WINDOWS_ERROR_MODE_FLAGS
    ):
        raise RuntimeError("Windows test error mode was not applied")
    if current_wer_flags & WER_FAULT_REPORTING_NO_UI == 0:
        raise RuntimeError("Windows Error Reporting no-UI flag was not applied")
    if current_wer_flags & WER_FAULT_REPORTING_FLAG_QUEUE == 0:
        raise RuntimeError("Windows Error Reporting queue flag was not applied")
    if current_wer_flags & WER_FAULT_REPORTING_ALWAYS_SHOW_UI:
        raise RuntimeError("Windows Error Reporting always-show-UI flag remains enabled")


def configure_automated_test_process(qt_platform: str | None = "offscreen") -> None:
    """Force non-interactive Qt and Windows crash handling before Qt is imported."""
    if qt_platform is not None:
        os.environ["QT_QPA_PLATFORM"] = qt_platform
    os.environ["PYTHONFAULTHANDLER"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    if sys.platform == "win32":
        _configure_windows_error_ui()


def configure_test_launcher(qt_platform: str | None = "offscreen") -> None:
    """Protect a child before its own test bootstrap can configure WER."""
    if qt_platform is not None:
        os.environ["QT_QPA_PLATFORM"] = qt_platform
    os.environ["PYTHONFAULTHANDLER"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    if sys.platform == "win32":
        _configure_windows_error_ui()


def automated_test_process_is_noninteractive() -> bool:
    """Return whether the current process has the required Windows no-UI flags."""
    if sys.platform != "win32":
        return True
    error_mode, wer_flags = _windows_error_policy()
    return (
        error_mode & WINDOWS_ERROR_MODE_FLAGS == WINDOWS_ERROR_MODE_FLAGS
        and wer_flags & WER_FAULT_REPORTING_FLAG_QUEUE != 0
        and wer_flags & WER_FAULT_REPORTING_NO_UI != 0
        and wer_flags & WER_FAULT_REPORTING_ALWAYS_SHOW_UI == 0
    )


def _positive_timeout(value: str) -> float:
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError(
            "timeout must be a finite number greater than zero"
        )
    return timeout


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--qt-platform",
        choices=("offscreen", "windows", "inherit"),
        default="offscreen",
    )
    parser.add_argument("--timeout", type=_positive_timeout)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        parser.error("a child command is required after --")
    return args


def _wait_for_windows_process_exit(process: subprocess.Popen) -> bool:
    try:
        process.wait(timeout=PROCESS_GRACEFUL_WAIT_SECONDS)
        return True
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
        process.wait(timeout=PROCESS_FORCE_KILL_WAIT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as error:
        LOGGER.error("[test-process] root process cleanup failed: %s", error)
        return False
    return True


def _terminate_windows_process_tree(process: subprocess.Popen) -> bool:
    taskkill_succeeded = False
    try:
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=WINDOWS_TASKKILL_TIMEOUT_SECONDS,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        LOGGER.error("[test-process] taskkill failed: %s", error)
    else:
        taskkill_succeeded = completed.returncode == 0
        if not taskkill_succeeded:
            detail = (completed.stderr or completed.stdout or "").strip()
            LOGGER.error(
                "[test-process] taskkill exit code %s: %s",
                completed.returncode,
                detail or "no diagnostic output",
            )
    root_stopped = _wait_for_windows_process_exit(process)
    return taskkill_succeeded and root_stopped


def _posix_process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_posix_process_group_exit(
    process: subprocess.Popen, timeout: float
) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        process.poll()
        if not _posix_process_group_exists(process.pid):
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(PROCESS_GROUP_POLL_INTERVAL_SECONDS, remaining))


def _terminate_process_tree(process: subprocess.Popen) -> bool:
    if sys.platform == "win32":
        return _terminate_windows_process_tree(process)

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except OSError as error:
        LOGGER.error("[test-process] SIGTERM process-tree cleanup failed: %s", error)
        return False
    if _wait_for_posix_process_group_exit(
        process, PROCESS_GRACEFUL_WAIT_SECONDS
    ):
        return True
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except OSError as error:
        LOGGER.error("[test-process] SIGKILL process-tree cleanup failed: %s", error)
        return False
    if not _wait_for_posix_process_group_exit(
        process, PROCESS_FORCE_KILL_WAIT_SECONDS
    ):
        LOGGER.error("[test-process] process group survived SIGKILL")
        return False
    return True


def _format_return_code(return_code: int) -> str:
    if sys.platform == "win32":
        return f"{return_code} (0x{return_code & 0xFFFFFFFF:08X})"
    return str(return_code)


def run_child(command: Sequence[str], timeout: float | None = None) -> int:
    """Run one child command and preserve its raw exit status."""
    popen_options = {"start_new_session": True} if sys.platform != "win32" else {}
    process = subprocess.Popen(command, **popen_options)
    try:
        return_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        LOGGER.error("[test-process] child timed out after %gs", timeout)
        if not _terminate_process_tree(process):
            LOGGER.error("[test-process] child process tree cleanup was incomplete")
            return TEST_CLEANUP_FAILURE_EXIT_CODE
        return TEST_TIMEOUT_EXIT_CODE
    if return_code != 0:
        detail = _format_return_code(return_code)
        LOGGER.error("[test-process] child exit code: %s", detail)
    return return_code


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    qt_platform = None if args.qt_platform == "inherit" else args.qt_platform
    configure_test_launcher(qt_platform)
    return run_child(args.command, args.timeout)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    status = main()
    if sys.platform == "win32" and not 0 <= status <= 255:
        sys.stdout.flush()
        sys.stderr.flush()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.ExitProcess.argtypes = [ctypes.c_uint32]
        kernel32.ExitProcess.restype = None
        kernel32.ExitProcess(ctypes.c_uint32(status).value)
    raise SystemExit(1 if status < 0 else status)
