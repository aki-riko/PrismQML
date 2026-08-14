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
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path


SEM_FAILCRITICALERRORS = 0x0001
SEM_NOGPFAULTERRORBOX = 0x0002
SEM_NOOPENFILEERRORBOX = 0x8000
WER_FAULT_REPORTING_FLAG_QUEUE = 0x0002
WER_FAULT_REPORTING_ALWAYS_SHOW_UI = 0x0010
WER_FAULT_REPORTING_NO_UI = 0x0020
HRESULT_ERROR_NOT_FOUND = 0x80070490
UCRT_OUT_TO_STDERR = 1
UCRT_REPORT_ERRMODE = 3
WINDOWS_ERROR_MODE_FLAGS = (
    SEM_FAILCRITICALERRORS
    | SEM_NOGPFAULTERRORBOX
    | SEM_NOOPENFILEERRORBOX
)
TEST_TIMEOUT_EXIT_CODE = 124
TEST_CLEANUP_FAILURE_EXIT_CODE = 125
TEST_VISIBLE_WINDOW_EXIT_CODE = 126
PROCESS_GRACEFUL_WAIT_SECONDS = 2
PROCESS_FORCE_KILL_WAIT_SECONDS = 5
PROCESS_GROUP_POLL_INTERVAL_SECONDS = 0.05
ARTIFACT_ROOT_ENV = "PRISM_ARTIFACT_ROOT"
PYTHON_CACHE_PREFIX_ENV = "PYTHONPYCACHEPREFIX"
AUTOMATED_TEST_BOUNDARY_ENV = "PRISMQML_AUTOMATED_TEST_BOUNDARY"
AUTOMATED_TEST_BOUNDARY_VERSION = "v1"
TEST_CONFIG_FILE_ENV = "PRISMQML_CONFIG_FILE"
_PYTHON_COMMAND_ALIASES = frozenset(("python", "python.exe"))
LOGGER = logging.getLogger(__name__)


def _artifact_root() -> Path:
    """Return the shared local artifact root. 返回统一的本地产物根目录。"""
    configured = os.environ.get(ARTIFACT_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / ".artifacts"


def _configure_python_cache() -> None:
    """Keep Python bytecode under the shared artifact root. 集中 Python 字节码缓存。"""
    cache_path = _artifact_root() / "python" / "pycache"
    os.environ[PYTHON_CACHE_PREFIX_ENV] = str(cache_path)
    sys.pycache_prefix = str(cache_path)


# Configure before importing repository helper modules. 在导入仓库辅助模块前配置缓存。
_configure_python_cache()


if sys.platform == "win32":
    if __package__:
        from ._windows_test_process import (
            WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS,
            WINDOWS_JOB_CLEANUP_WAIT_SECONDS,
            run_isolated_windows_child,
        )
        from ._windows_test_api import current_process_test_boundary_status
    else:
        script_directory = str(Path(__file__).resolve().parent)
        inserted_script_directory = script_directory not in sys.path
        if inserted_script_directory:
            sys.path.insert(0, script_directory)
        try:
            from _windows_test_process import (
                WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS,
                WINDOWS_JOB_CLEANUP_WAIT_SECONDS,
                run_isolated_windows_child,
            )
            from _windows_test_api import current_process_test_boundary_status
        finally:
            if inserted_script_directory:
                sys.path.remove(script_directory)
else:
    WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS = 0
    WINDOWS_JOB_CLEANUP_WAIT_SECONDS = 0


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


def _windows_ucrt_error_mode() -> int:
    ucrt = ctypes.CDLL("ucrtbase", use_errno=True)
    ucrt._set_error_mode.argtypes = [ctypes.c_int]
    ucrt._set_error_mode.restype = ctypes.c_int
    return int(ucrt._set_error_mode(UCRT_REPORT_ERRMODE))


def _configure_windows_crt_error_ui() -> None:
    ucrt = ctypes.CDLL("ucrtbase", use_errno=True)
    ucrt._set_error_mode.argtypes = [ctypes.c_int]
    ucrt._set_error_mode.restype = ctypes.c_int
    ucrt._set_error_mode(UCRT_OUT_TO_STDERR)
    if _windows_ucrt_error_mode() != UCRT_OUT_TO_STDERR:
        raise RuntimeError("Windows UCRT stderr error mode was not applied")


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


def _configure_qml_disk_cache() -> None:
    """Keep automated QML compilation out of the real user cache."""
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    os.environ.pop("QML_FORCE_DISK_CACHE", None)


def configure_automated_test_process(qt_platform: str | None = "offscreen") -> None:
    """Force non-interactive Qt and Windows crash handling before Qt is imported."""
    if qt_platform is not None:
        os.environ["QT_QPA_PLATFORM"] = qt_platform
    _configure_python_cache()
    _configure_qml_disk_cache()
    os.environ["PYTHONFAULTHANDLER"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    if sys.platform == "win32":
        _configure_windows_error_ui()
        _configure_windows_crt_error_ui()


def configure_test_launcher(qt_platform: str | None = "offscreen") -> None:
    """Protect a child before its own test bootstrap can configure WER."""
    if qt_platform is not None:
        os.environ["QT_QPA_PLATFORM"] = qt_platform
    _configure_python_cache()
    _configure_qml_disk_cache()
    os.environ["PYTHONFAULTHANDLER"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    if sys.platform == "win32":
        _configure_windows_error_ui()
        _configure_windows_crt_error_ui()


def _automated_test_boundary_status() -> tuple[bool, str]:
    actual = os.environ.get(AUTOMATED_TEST_BOUNDARY_ENV)
    if actual != AUTOMATED_TEST_BOUNDARY_VERSION:
        return False, (
            f"expected marker {AUTOMATED_TEST_BOUNDARY_VERSION!r}, got {actual!r}"
        )
    if sys.platform != "win32":
        return True, "workflow marker accepted on this platform"
    try:
        return current_process_test_boundary_status()
    except (OSError, RuntimeError) as error:
        return False, f"Windows boundary inspection failed: {error}"


def automated_test_boundary_is_active() -> bool:
    """Return whether the marker and platform boundary checks both pass."""
    active, _detail = _automated_test_boundary_status()
    return active


def mark_automated_test_boundary() -> None:
    """Mark descendants only after the launcher policy has been configured."""
    os.environ[AUTOMATED_TEST_BOUNDARY_ENV] = AUTOMATED_TEST_BOUNDARY_VERSION


def require_automated_test_boundary() -> None:
    """Reject automated entrypoints that bypass the process runner."""
    active, detail = _automated_test_boundary_status()
    if active:
        return
    raise RuntimeError(
        "Automated test boundary is missing or invalid; run through "
        f"scripts/test_process.py ({detail})"
    )


def prepare_automated_test_process(
    qt_platform: str | None = "offscreen",
) -> None:
    """Require the runner boundary, then apply in-process test policy."""
    require_automated_test_boundary()
    configure_automated_test_process(qt_platform)


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
        and _windows_ucrt_error_mode() == UCRT_OUT_TO_STDERR
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


def _normalize_child_command(command: Sequence[str]) -> tuple[str, ...]:
    """Keep a generic Python child in the runner's active environment.

    让裸 Python 子命令保持在 runner 当前激活的解释器环境中。
    """
    normalized = tuple(command)
    if not normalized:
        raise ValueError("child command is empty")
    if normalized[0] in _PYTHON_COMMAND_ALIASES:
        if not sys.executable:
            raise RuntimeError("current Python executable is unavailable")
        return (sys.executable, *normalized[1:])
    return normalized


def run_child(command: Sequence[str], timeout: float | None = None) -> int:
    """Run one child command and preserve its raw exit status."""
    normalized_command = _normalize_child_command(command)
    if sys.platform == "win32":
        return_code = run_isolated_windows_child(
            normalized_command,
            timeout,
            LOGGER,
            timeout_exit_code=TEST_TIMEOUT_EXIT_CODE,
            cleanup_failure_exit_code=TEST_CLEANUP_FAILURE_EXIT_CODE,
            visible_window_exit_code=TEST_VISIBLE_WINDOW_EXIT_CODE,
        )
        if return_code != 0:
            detail = _format_return_code(return_code)
            LOGGER.error("[test-process] child exit code: %s", detail)
        return return_code

    process = subprocess.Popen(normalized_command, start_new_session=True)
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
    mark_automated_test_boundary()
    with tempfile.TemporaryDirectory(prefix="prismqml-test-config-") as directory:
        os.environ[TEST_CONFIG_FILE_ENV] = str(Path(directory) / "app.json")
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
