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
import time

import pytest
from PySide6.QtCore import Qt

from prismqml import (
    PoolTaskOptions,
    TaskState,
    TaskThreadPool,
    current_task,
    run_in_pool,
    run_in_thread,
    shutdown_tasks,
)


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


_DESTROYED_HANDLE_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import shiboken6
import threading
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from prismqml import current_task, global_task_pool, run_in_pool
from prismqml.python.core import task_runner as task_runner_module

app = QCoreApplication([])
started = threading.Event()
release = threading.Event()

def work():
    started.set()
    release.wait(3)
    current_task().report_progress("late")
    return 41

handle = run_in_pool(work)
control = handle._control
events = handle._events
if not started.wait(3):
    raise SystemExit(4)
shiboken6.delete(handle)
active = task_runner_module._active_handles()
if len(active) != 1 or shiboken6.isValid(active[0]):
    raise SystemExit(5)
release.set()
if not control.wait_for_backend(3000):
    raise SystemExit(6)
if task_runner_module._active_handles():
    raise SystemExit(7)
if not global_task_pool().waitForDone(3000):
    raise SystemExit(8)
loop = QEventLoop()
QTimer.singleShot(50, loop.quit)
loop.exec()
if shiboken6.isValid(events):
    raise SystemExit(9)
print("TASK_DESTROYED_HANDLE_OK", flush=True)
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


def _run_destroyed_handle_probe():
    """Run completion after owner destruction in isolation. 隔离验证句柄先销毁。"""
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
            _DESTROYED_HANDLE_SCRIPT,
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


def test_pool_completion_survives_public_handle_destruction() -> None:
    """A destroyed handle must not break worker signal cleanup. 句柄销毁不得破坏后台收尾。"""
    completed = _run_destroyed_handle_probe()
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "TASK_DESTROYED_HANDLE_OK" in output
    assert "Signal source has been deleted" not in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output


def test_queued_pool_cancellation_stress(qapp) -> None:
    """Repeated queue removal must not execute or retain tasks. 重复移除队列不得执行或残留。"""
    pool = TaskThreadPool()
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


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_cancel_is_safe_during_backend_release(qapp, launcher) -> None:
    """Cancellation must tolerate concurrent backend release. 取消必须容忍并发后端释放。"""
    worker_started = threading.Event()
    cancel_accepted = threading.Event()
    release_entered = threading.Event()
    allow_release_return = threading.Event()
    cancel_finished = threading.Event()
    wait_finished = threading.Event()
    errors = []
    cancel_results = []

    def work():
        worker_started.set()
        while not current_task().cancel_requested:
            time.sleep(0.001)

    handle = launcher(work)
    control_request_cancel = handle._control.request_cancel
    backend = handle._backend
    backend_release = backend.release

    def delayed_request_cancel():
        requested = control_request_cancel()
        if requested:
            cancel_accepted.set()
            assert release_entered.wait(TASK_TIMEOUT_MS / 1000)
        return requested

    def paused_release():
        backend_release()
        release_entered.set()
        assert allow_release_return.wait(TASK_TIMEOUT_MS / 1000)

    handle._control.request_cancel = delayed_request_cancel
    backend.release = paused_release

    def cancel_task():
        try:
            cancel_results.append(handle.cancel())
        except BaseException as caught:
            errors.append(caught)
        finally:
            cancel_finished.set()

    def wait_task():
        try:
            assert handle.wait(TASK_TIMEOUT_MS)
        except BaseException as caught:
            errors.append(caught)
        finally:
            wait_finished.set()

    cancel_thread = threading.Thread(target=cancel_task, daemon=True)
    wait_thread = threading.Thread(target=wait_task, daemon=True)
    try:
        assert worker_started.wait(TASK_TIMEOUT_MS / 1000)
        cancel_thread.start()
        assert cancel_accepted.wait(TASK_TIMEOUT_MS / 1000)
        wait_thread.start()
        assert release_entered.wait(TASK_TIMEOUT_MS / 1000)
        assert cancel_finished.wait(TASK_TIMEOUT_MS / 1000)
        assert cancel_results == [True]
        assert not errors
    finally:
        allow_release_return.set()
        cancel_thread.join(TASK_TIMEOUT_MS / 1000)
        wait_thread.join(TASK_TIMEOUT_MS / 1000)

    assert wait_finished.is_set()
    assert handle.state is TaskState.CANCELLED


def test_pool_wait_cannot_release_backend_before_stop_event(qapp) -> None:
    """Pool wait must not clear fields still used by run(). 线程池等待不得提前清理运行字段。"""
    pool = TaskThreadPool()
    pool.setMaxThreadCount(1)
    callable_started = threading.Event()
    finish_callable = threading.Event()
    backend_marked = threading.Event()
    allow_backend_return = threading.Event()
    backend_event_emitted = threading.Event()

    def work():
        callable_started.set()
        finish_callable.wait()
        return 41

    handle = run_in_pool(work, task_options=PoolTaskOptions(pool=pool))
    backend = handle._backend
    original_mark = handle._control.mark_backend_stopped
    backend._events.backend_stopped.connect(
        backend_event_emitted.set,
        Qt.ConnectionType.DirectConnection,
    )

    def paused_mark():
        original_mark()
        backend_marked.set()
        assert allow_backend_return.wait(TASK_TIMEOUT_MS / 1000)

    handle._control.mark_backend_stopped = paused_mark
    try:
        assert callable_started.wait(TASK_TIMEOUT_MS / 1000)
        finish_callable.set()
        assert backend_marked.wait(TASK_TIMEOUT_MS / 1000)
        assert handle.wait(TASK_TIMEOUT_MS)
    finally:
        finish_callable.set()
        allow_backend_return.set()
        assert pool.waitForDone(TASK_TIMEOUT_MS)

    assert backend_event_emitted.is_set()
    assert handle.state is TaskState.SUCCEEDED
    assert handle.result == 41


def test_pool_clear_settles_managed_queued_task(qapp) -> None:
    """Managed clear must settle queued work. 受管清理必须结算排队任务。"""
    pool = TaskThreadPool()
    pool.setMaxThreadCount(1)
    blocker_started = threading.Event()
    release_blocker = threading.Event()
    queued_executed = threading.Event()

    def block_pool():
        blocker_started.set()
        release_blocker.wait()

    blocker = run_in_pool(block_pool, task_options=PoolTaskOptions(pool=pool))
    queued = run_in_pool(
        queued_executed.set,
        task_options=PoolTaskOptions(pool=pool),
    )
    try:
        assert blocker_started.wait(TASK_TIMEOUT_MS / 1000)
        pool.clear()
        assert queued.wait(TASK_TIMEOUT_MS)
        assert queued.state is TaskState.CANCELLED
        assert not queued_executed.is_set()
    finally:
        release_blocker.set()
        assert blocker.wait(TASK_TIMEOUT_MS)
        assert pool.waitForDone(TASK_TIMEOUT_MS)


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_shutdown_tasks_rejects_background_self_wait(qapp, launcher) -> None:
    """Shutdown coordination rejects worker-thread self-wait. 退出协调拒绝后台线程自等待。"""
    def work():
        try:
            shutdown_tasks()
        except RuntimeError as caught:
            return str(caught)
        return "not rejected"

    handle = launcher(work)
    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.SUCCEEDED
    assert "Qt application thread" in handle.result
