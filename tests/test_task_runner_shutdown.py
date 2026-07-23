# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Bounded task-shutdown regressions. 有界后台任务退出回归。"""

import os
from pathlib import Path
import subprocess
import sys
import threading

from PySide6.QtCore import QThreadPool

from prismqml import PoolTaskOptions, TaskState, run_in_pool


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"
POOL_CANCEL_STRESS_CYCLES = 200
TASK_TIMEOUT_MS = 3000

_BOUNDED_APP_SHUTDOWN_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import threading
import shiboken6
from PySide6.QtCore import QTimer
from prismqml import (
    App,
    TaskShutdownTimeoutError,
    run_in_thread,
    shutdown_tasks,
)

gate = threading.Event()
started = threading.Event()

def ignore_cancellation_until_released():
    started.set()
    gate.wait()

app = App([], task_shutdown_timeout_ms=20)
run_in_thread(ignore_cancellation_until_released)
if not started.wait(1):
    raise SystemExit(4)
QTimer.singleShot(1, app.quit)

try:
    app.exec()
except TaskShutdownTimeoutError as caught:
    print(f"TASK_SHUTDOWN_TIMEOUT={caught.report.pending_count}", flush=True)
    if app.engine is None:
        raise SystemExit(5)
else:
    raise SystemExit(6)

gate.set()
report = shutdown_tasks(3000)
if not report.complete:
    raise SystemExit(7)
app.shutdown()

qapp = app.qapp
App._reset()
shiboken6.delete(qapp)
print("TASK_BOUNDED_SHUTDOWN_OK", flush=True)
'''


def _run_bounded_app_shutdown_probe():
    """Run a non-cooperative App shutdown in isolation. 隔离运行非协作任务退出。"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    return subprocess.run(
        [
            sys.executable,
            str(TEST_PROCESS),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "30",
            "--",
            sys.executable,
            "-c",
            _BOUNDED_APP_SHUTDOWN_SCRIPT,
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=40,
        check=False,
    )


def test_app_bounded_shutdown_preserves_runtime_until_retry() -> None:
    """App timeout must not destroy Qt under a live task. App 超时不得销毁活任务下的 Qt。"""
    completed = _run_bounded_app_shutdown_probe()
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "TASK_SHUTDOWN_TIMEOUT=1" in output
    assert "TASK_BOUNDED_SHUTDOWN_OK" in output
    assert "QThread: Destroyed while thread" not in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output


def test_queued_pool_cancellation_stress(qapp) -> None:
    """Repeated queue removal must not execute or retain tasks. 重复移除队列不得执行或残留。"""
    pool = QThreadPool()
    pool.setMaxThreadCount(1)
    blocker_started = threading.Event()
    release_blocker = threading.Event()
    queued_executed = threading.Event()
    options = PoolTaskOptions(pool=pool)
    blocker = run_in_pool(
        lambda: (blocker_started.set(), release_blocker.wait()),
        task_options=options,
    )
    try:
        assert blocker_started.wait(TASK_TIMEOUT_MS / 1000)
        for _iteration in range(POOL_CANCEL_STRESS_CYCLES):
            handle = run_in_pool(queued_executed.set, task_options=options)
            assert handle.cancel()
            assert handle.wait(TASK_TIMEOUT_MS)
            assert handle.state is TaskState.CANCELLED
    finally:
        release_blocker.set()
        assert blocker.wait(TASK_TIMEOUT_MS)
        pool.waitForDone(TASK_TIMEOUT_MS)

    assert not queued_executed.is_set()
    qapp.processEvents()
