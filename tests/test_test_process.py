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

import scripts.test_process as test_process
from scripts.test_process import (
    PROCESS_GRACEFUL_WAIT_SECONDS,
    PROCESS_GROUP_POLL_INTERVAL_SECONDS,
    SEM_NOGPFAULTERRORBOX,
    TEST_CLEANUP_FAILURE_EXIT_CODE,
    TEST_TIMEOUT_EXIT_CODE,
    WER_FAULT_REPORTING_ALWAYS_SHOW_UI,
    WER_FAULT_REPORTING_FLAG_QUEUE,
    WER_FAULT_REPORTING_NO_UI,
    WINDOWS_ERROR_MODE_FLAGS,
    automated_test_process_is_noninteractive,
    configure_automated_test_process,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "test_process.py"


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


class _FakeTimeoutProcess:
    pid = 12345

    def __init__(self):
        self.killed = False
        self.wait_calls = 0

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.wait_calls == 1 or not self.killed:
            raise subprocess.TimeoutExpired("fake-child", timeout)
        return 1

    def kill(self):
        self.killed = True


class _FakeUnkillableProcess(_FakeTimeoutProcess):
    def kill(self):
        raise OSError("access denied")


def _taskkill_timeout(command, **kwargs):
    raise subprocess.TimeoutExpired(command, kwargs["timeout"])


def _taskkill_nonzero(command, **_kwargs):
    return subprocess.CompletedProcess(
        command,
        5,
        stdout="",
        stderr="access denied",
    )


def test_configure_automated_process_overrides_visible_qt_platform(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "windows")
    configure_automated_test_process()
    assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
    assert automated_test_process_is_noninteractive()


def test_runner_forces_headless_environment_in_child():
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "windows"
    code = "import os, sys; sys.stdout.write(os.environ['QT_QPA_PLATFORM'])"
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
    assert result.stdout.strip() == "offscreen"


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
    code = """
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

def state():
    wer_flags = ctypes.c_uint32()
    kernel32.WerGetFlags(kernel32.GetCurrentProcess(), ctypes.byref(wer_flags))
    return {
        "error_mode": int(kernel32.GetErrorMode()),
        "wer_flags": int(wer_flags.value),
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
sys.stdout.write(
    json.dumps(
        {
            "before": before,
            "after": state(),
            "descendant_error_mode": int(descendant.stdout),
        }
    )
)
"""
    result = _run_runner("--qt-platform", "inherit", "--", sys.executable, "-c", code)

    assert result.returncode == 0, result.stdout + result.stderr
    state = json.loads(result.stdout)
    assert (
        state["before"]["error_mode"] & WINDOWS_ERROR_MODE_FLAGS
        == WINDOWS_ERROR_MODE_FLAGS
    )
    assert state["before"]["error_mode"] & SEM_NOGPFAULTERRORBOX != 0
    assert (
        state["after"]["error_mode"] & WINDOWS_ERROR_MODE_FLAGS
        == WINDOWS_ERROR_MODE_FLAGS
    )
    assert state["after"]["error_mode"] & SEM_NOGPFAULTERRORBOX != 0
    assert state["after"]["wer_flags"] & WER_FAULT_REPORTING_FLAG_QUEUE
    assert state["after"]["wer_flags"] & WER_FAULT_REPORTING_NO_UI
    assert not (
        state["after"]["wer_flags"] & WER_FAULT_REPORTING_ALWAYS_SHOW_UI
    )
    assert (
        state["descendant_error_mode"] & WINDOWS_ERROR_MODE_FLAGS
        == WINDOWS_ERROR_MODE_FLAGS
    )


def test_runner_reports_child_failure_without_masking_it():
    result = _run_runner("--", sys.executable, "-c", "raise SystemExit(7)")

    assert result.returncode == 7
    assert "child exit code: 7" in result.stderr


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


@pytest.mark.skipif(sys.platform != "win32", reason="Windows taskkill only")
@pytest.mark.parametrize(
    "taskkill_failure",
    (_taskkill_timeout, _taskkill_nonzero),
    ids=("timeout", "nonzero"),
)
def test_timeout_fails_closed_when_taskkill_cannot_confirm_tree_cleanup(
    monkeypatch, taskkill_failure
):
    process = _FakeTimeoutProcess()
    monkeypatch.setattr(test_process.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(test_process.subprocess, "run", taskkill_failure)
    result = test_process.run_child(["fake-child"], timeout=1)

    assert result == TEST_CLEANUP_FAILURE_EXIT_CODE
    assert process.killed
    assert process.wait_calls == 3


@pytest.mark.skipif(sys.platform != "win32", reason="Windows taskkill only")
def test_cleanup_failure_remains_bounded_when_root_kill_fails(monkeypatch):
    process = _FakeUnkillableProcess()
    monkeypatch.setattr(test_process.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(test_process.subprocess, "run", _taskkill_timeout)

    result = test_process.run_child(["fake-child"], timeout=1)

    assert result == TEST_CLEANUP_FAILURE_EXIT_CODE
    assert process.wait_calls == 2
