# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tests for the non-interactive process launcher. 无交互进程启动器测试。"""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts._windows_test_result import BOUNDARY_RESULT_PREFIX
from scripts.test_process import (
    ARTIFACT_ROOT_ENV,
    PROCESS_GRACEFUL_WAIT_SECONDS,
    PROCESS_GROUP_POLL_INTERVAL_SECONDS,
    PYTHON_CACHE_PREFIX_ENV,
    SEM_NOGPFAULTERRORBOX,
    TEST_CLEANUP_FAILURE_EXIT_CODE,
    TEST_TIMEOUT_EXIT_CODE,
    TEST_VISIBLE_WINDOW_EXIT_CODE,
    UCRT_OUT_TO_STDERR,
    UCRT_REPORT_ERRMODE,
    WER_FAULT_REPORTING_ALWAYS_SHOW_UI,
    WER_FAULT_REPORTING_FLAG_QUEUE,
    WER_FAULT_REPORTING_NO_UI,
    WINDOWS_ERROR_MODE_FLAGS,
    automated_test_process_is_noninteractive,
    configure_automated_test_process,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "test_process.py"
NONINTERACTIVE_POLICY_CODE = r'''
import ctypes
import json
import subprocess
import sys

from scripts.test_process import configure_automated_test_process

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetErrorMode.argtypes = []
kernel32.GetErrorMode.restype = ctypes.c_uint
kernel32.GetCurrentProcess.argtypes = []
kernel32.GetCurrentProcess.restype = ctypes.c_void_p
kernel32.WerGetFlags.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
kernel32.WerGetFlags.restype = ctypes.c_long
ucrt = ctypes.CDLL("ucrtbase", use_errno=True)
ucrt._set_error_mode.argtypes = [ctypes.c_int]
ucrt._set_error_mode.restype = ctypes.c_int

def state():
    wer_flags = ctypes.c_uint32()
    kernel32.WerGetFlags(kernel32.GetCurrentProcess(), ctypes.byref(wer_flags))
    return {
        "error_mode": int(kernel32.GetErrorMode()),
        "wer_flags": int(wer_flags.value),
        "ucrt_error_mode": int(ucrt._set_error_mode(3)),
    }

before = state()
configure_automated_test_process(None)
descendant_code = (
    "import ctypes, sys; "
    "kernel32 = ctypes.WinDLL('kernel32', use_last_error=True); "
    "kernel32.GetErrorMode.argtypes = []; "
    "kernel32.GetErrorMode.restype = ctypes.c_uint; "
    "sys.stdout.write(str(int(kernel32.GetErrorMode())))"
)
descendant = subprocess.run(
    [sys.executable, "-c", descendant_code],
    capture_output=True,
    text=True,
    encoding="utf-8",
    check=False,
)
if descendant.returncode != 0:
    raise SystemExit(descendant.returncode)
sys.stdout.write(json.dumps({
    "before": before,
    "after": state(),
    "descendant_error_mode": int(descendant.stdout),
}))
'''
ROOT_MESSAGE_BOX_CODE = r'''
import ctypes

ctypes.windll.user32.MessageBoxW(
    None,
    "private desktop root sentinel",
    "PrismQML root sentinel",
    0,
)
'''
GRANDCHILD_MESSAGE_BOX_CODE = r'''
import ctypes

ctypes.windll.user32.MessageBoxW(
    None,
    "private desktop grandchild sentinel",
    "PrismQML grandchild sentinel",
    0,
)
'''
HIDDEN_WINDOW_CODE = r'''
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HANDLE, wintypes.HANDLE, ctypes.c_void_p,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL
window = user32.CreateWindowExW(
    0, "STATIC", "PrismQML hidden sentinel", 0,
    0, 0, 100, 100, None, None, None, None,
)
if not window:
    raise ctypes.WinError(ctypes.get_last_error())
time.sleep(0.2)
if not user32.DestroyWindow(window):
    raise ctypes.WinError(ctypes.get_last_error())
'''


def _run_runner(*arguments: str, env: dict[str, str] | None = None):
    return subprocess.run(
        [sys.executable, str(RUNNER), *arguments],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def _run_windows_code(code: str):
    return _run_runner(
        "--qt-platform",
        "inherit",
        "--timeout",
        "10",
        "--",
        sys.executable,
        "-c",
        code,
    )


def _boundary_records(stderr: str) -> list[dict]:
    return [
        json.loads(line[len(BOUNDARY_RESULT_PREFIX) :])
        for line in stderr.splitlines()
        if line.startswith(BOUNDARY_RESULT_PREFIX)
    ]


def _spawn_and_sleep_code(child_code: str) -> str:
    return f"""
import subprocess
import sys
import time

subprocess.Popen([sys.executable, "-c", {child_code!r}])
time.sleep(30)
"""


def _assert_noninteractive_policy(state: dict) -> None:
    assert state["before"]["error_mode"] & WINDOWS_ERROR_MODE_FLAGS == (
        WINDOWS_ERROR_MODE_FLAGS
    )
    assert state["before"]["error_mode"] & SEM_NOGPFAULTERRORBOX != 0
    assert state["after"]["error_mode"] & WINDOWS_ERROR_MODE_FLAGS == (
        WINDOWS_ERROR_MODE_FLAGS
    )
    assert state["after"]["error_mode"] & SEM_NOGPFAULTERRORBOX != 0
    assert state["after"]["wer_flags"] & WER_FAULT_REPORTING_FLAG_QUEUE
    assert state["after"]["wer_flags"] & WER_FAULT_REPORTING_NO_UI
    assert state["after"]["ucrt_error_mode"] == UCRT_OUT_TO_STDERR
    assert not state["after"]["wer_flags"] & WER_FAULT_REPORTING_ALWAYS_SHOW_UI
    assert state["descendant_error_mode"] & WINDOWS_ERROR_MODE_FLAGS == (
        WINDOWS_ERROR_MODE_FLAGS
    )


def _windows_process_exists(process_id: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint32,
    ]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.OpenProcess(0x1000, False, process_id)
    if handle:
        kernel32.CloseHandle(handle)
    return bool(handle)


def _posix_process_exists(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _windows_ucrt_error_mode() -> int:
    ucrt = ctypes.CDLL("ucrtbase", use_errno=True)
    ucrt._set_error_mode.argtypes = [ctypes.c_int]
    ucrt._set_error_mode.restype = ctypes.c_int
    return int(ucrt._set_error_mode(UCRT_REPORT_ERRMODE))


def test_configure_automated_process_overrides_visible_qt_platform(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "windows")
    monkeypatch.setenv("QML_DISABLE_DISK_CACHE", "0")
    monkeypatch.setenv("QML_FORCE_DISK_CACHE", "1")
    monkeypatch.delenv(ARTIFACT_ROOT_ENV, raising=False)
    monkeypatch.setenv(PYTHON_CACHE_PREFIX_ENV, "outside-cache")
    configure_automated_test_process()
    assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
    assert os.environ["QML_DISABLE_DISK_CACHE"] == "1"
    assert "QML_FORCE_DISK_CACHE" not in os.environ
    assert Path(os.environ[PYTHON_CACHE_PREFIX_ENV]) == (
        REPO_ROOT / ".artifacts" / "python" / "pycache"
    )
    assert Path(sys.pycache_prefix) == REPO_ROOT / ".artifacts" / "python" / "pycache"
    assert automated_test_process_is_noninteractive()
    if sys.platform == "win32":
        assert _windows_ucrt_error_mode() == UCRT_OUT_TO_STDERR


def test_configure_automated_process_honors_artifact_root(monkeypatch, tmp_path):
    artifact_root = tmp_path / "custom-artifacts"
    monkeypatch.setenv(ARTIFACT_ROOT_ENV, str(artifact_root))
    configure_automated_test_process(None)
    assert Path(os.environ[PYTHON_CACHE_PREFIX_ENV]) == (
        artifact_root / "python" / "pycache"
    )
    assert Path(sys.pycache_prefix) == artifact_root / "python" / "pycache"


def test_runner_forces_headless_environment_in_child():
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "windows"
    environment["QML_DISABLE_DISK_CACHE"] = "0"
    environment["QML_FORCE_DISK_CACHE"] = "1"
    code = (
        "import json, os, sys; sys.stdout.write(json.dumps({"
        "'platform': os.environ['QT_QPA_PLATFORM'], "
        "'cache_disabled': os.environ['QML_DISABLE_DISK_CACHE'], "
        "'cache_forced': os.environ.get('QML_FORCE_DISK_CACHE')}))"
    )
    result = _run_runner(
        "--qt-platform",
        "offscreen",
        "--",
        sys.executable,
        "-c",
        code,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "platform": "offscreen",
        "cache_disabled": "1",
        "cache_forced": None,
    }


@pytest.mark.parametrize("timeout", ("0", "-1", "nan", "inf"))
def test_runner_rejects_non_positive_or_non_finite_timeout(timeout):
    result = _run_runner(
        "--timeout",
        timeout,
        "--",
        sys.executable,
        "-c",
        "raise SystemExit(99)",
    )

    assert result.returncode == 2
    assert "timeout must be a finite number greater than zero" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows error mode only")
def test_runner_child_and_descendant_keep_noninteractive_error_policy():
    result = _run_runner(
        "--qt-platform", "inherit", "--", sys.executable, "-c",
        NONINTERACTIVE_POLICY_CODE,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    _assert_noninteractive_policy(json.loads(result.stdout))


def test_runner_reports_child_failure_without_masking_it():
    result = _run_runner("--", sys.executable, "-c", "raise SystemExit(7)")

    assert result.returncode == 7
    assert "child exit code: 7" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows boundary only")
def test_runner_emits_structured_boundary_result():
    result = _run_runner("--", sys.executable, "-c", "pass")
    records = _boundary_records(result.stderr)

    assert result.returncode == 0, result.stdout + result.stderr
    assert len(records) == 1
    assert records[0]["desktop"].startswith("PrismQMLTest-")
    assert records[0]["job"] == "PrismQMLTestJob-" + records[0][
        "desktop"
    ].removeprefix("PrismQMLTest-")
    assert records[0]["root_process_id"] > 0
    assert records[0]["final_active_processes"] == 0
    assert records[0]["exit_code"] == 0
    assert records[0]["cleanup_succeeded"] is True


@pytest.mark.skipif(sys.platform != "win32", reason="Windows boundary only")
def test_runner_structured_result_preserves_nonzero_child_exit():
    result = _run_runner("--", sys.executable, "-c", "raise SystemExit(7)")
    records = _boundary_records(result.stderr)

    assert result.returncode == 7
    assert len(records) == 1
    assert records[0]["exit_code"] == 7
    assert records[0]["cleanup_succeeded"] is True
    assert records[0]["final_active_processes"] == 0


@pytest.mark.skipif(sys.platform != "win32", reason="Windows NTSTATUS only")
def test_runner_preserves_windows_ntstatus_exit_code():
    status = 0xC0000374
    code = f"""
import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.ExitProcess.argtypes = [ctypes.c_uint32]
kernel32.ExitProcess.restype = None
kernel32.ExitProcess(ctypes.c_uint32({status}).value)
"""
    result = _run_runner("--", sys.executable, "-c", code)

    assert result.returncode == status
    assert "0xC0000374" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process tree only")
def test_runner_timeout_leaves_no_child_process_running():
    code = """
import os
import subprocess
import sys
import time

child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
sys.stdout.write(f"{os.getpid()} {child.pid}\\n")
sys.stdout.flush()
time.sleep(30)
"""
    result = _run_runner(
        "--timeout",
        "5",
        "--",
        sys.executable,
        "-c",
        code,
    )

    assert result.returncode in {
        TEST_TIMEOUT_EXIT_CODE,
        TEST_CLEANUP_FAILURE_EXIT_CODE,
    }, result.stdout + result.stderr
    process_ids = [int(value) for value in result.stdout.split()]
    assert len(process_ids) == 2
    assert not any(_windows_process_exists(process_id) for process_id in process_ids)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private Desktop only")
def test_runner_rejects_visible_root_window_on_private_desktop():
    result = _run_windows_code(ROOT_MESSAGE_BOX_CODE)

    assert result.returncode == TEST_VISIBLE_WINDOW_EXIT_CODE
    assert '"title": "PrismQML root sentinel"' in result.stderr
    assert "visible_windows=1 / job_active_processes=0" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private Desktop only")
def test_runner_rejects_visible_grandchild_window_on_private_desktop():
    result = _run_windows_code(
        _spawn_and_sleep_code(GRANDCHILD_MESSAGE_BOX_CODE)
    )

    assert result.returncode == TEST_VISIBLE_WINDOW_EXIT_CODE
    assert '"title": "PrismQML grandchild sentinel"' in result.stderr
    assert "visible_windows=1 / job_active_processes=0" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private Desktop only")
def test_runner_allows_hidden_window():
    result = _run_windows_code(HIDDEN_WINDOW_CODE)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "visible_windows=0 / job_active_processes=0" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object only")
def test_runner_waits_for_grandchild_after_root_exit():
    child_code = "import time; time.sleep(0.4)"
    code = f"""
import subprocess
import sys

subprocess.Popen([sys.executable, "-c", {child_code!r}])
"""
    started_at = time.monotonic()
    result = _run_runner(
        "--qt-platform",
        "inherit",
        "--timeout",
        "10",
        "--",
        sys.executable,
        "-c",
        code,
    )
    elapsed = time.monotonic() - started_at

    assert result.returncode == 0, result.stdout + result.stderr
    assert elapsed >= 0.3
    assert "visible_windows=0 / job_active_processes=0" in result.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups only")
def test_runner_timeout_terminates_posix_process_group():
    code = """
import signal
import subprocess
import sys
import time

child_code = (
    "import signal,time; "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "time.sleep(30)"
)
child = subprocess.Popen([sys.executable, "-c", child_code])
sys.stdout.write(str(child.pid) + "\\n")
sys.stdout.flush()
time.sleep(30)
"""
    result = _run_runner(
        "--timeout", "3", "--", sys.executable, "-c", code
    )

    assert result.returncode == TEST_TIMEOUT_EXIT_CODE, result.stdout + result.stderr
    child_pid = int(result.stdout.strip())
    deadline = time.monotonic() + PROCESS_GRACEFUL_WAIT_SECONDS
    while _posix_process_exists(child_pid) and time.monotonic() < deadline:
        time.sleep(PROCESS_GROUP_POLL_INTERVAL_SECONDS)
    assert not _posix_process_exists(child_pid)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows isolation only")
def test_windows_isolation_setup_failure_fails_closed():
    result = _run_runner(
        "--timeout",
        "5",
        "--",
        str(REPO_ROOT / "missing-test-command.exe"),
    )

    assert result.returncode == TEST_CLEANUP_FAILURE_EXIT_CODE
    assert "Windows isolation failed" in result.stderr
