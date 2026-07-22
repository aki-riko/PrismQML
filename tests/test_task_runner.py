# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Generic background-task regressions. 通用后台任务回归测试。"""

import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest
from PySide6.QtCore import QCoreApplication, QEventLoop, QThread, QTimer
from PySide6.QtTest import QSignalSpy

from prismqml import (
    TaskFailure,
    TaskState,
    current_task,
    run_in_pool,
    run_in_thread,
)


TASK_TIMEOUT_MS = 3000
REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"

_APP_SHUTDOWN_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import time
import shiboken6
from PySide6.QtCore import QTimer
from prismqml import App, run_in_thread

app = App([])
started_at = time.monotonic()
run_in_thread(lambda: time.sleep(0.1))
QTimer.singleShot(1, app.quit)
result = app.exec()
elapsed = time.monotonic() - started_at
qapp = app.qapp
App._reset()
shiboken6.delete(qapp)
print(f"TASK_SHUTDOWN_OK={result}:{elapsed:.3f}", flush=True)
raise SystemExit(0 if result == 0 and elapsed >= 0.08 else 3)
'''


def _wait_for_finished(handle, finished=None) -> None:
    """Wait for the public completion signal. 等待公开完成信号。"""
    finished = finished or QSignalSpy(handle.finished)
    if handle.state not in TaskState.terminal_states():
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        handle.finished.connect(loop.quit)
        timeout.start(TASK_TIMEOUT_MS)
        loop.exec()
        assert finished.count() == 1
    assert handle.state in TaskState.terminal_states()


def _run_app_shutdown_probe():
    """Run the real App teardown boundary in isolation. 隔离运行真实 App 退出边界。"""
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
            _APP_SHUTDOWN_SCRIPT,
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


def _assert_success_outcome(handle, progress, observations) -> None:
    """Check the common successful task contract. 检查成功任务的通用契约。"""
    value, ran_on_main_thread = handle.result
    assert value == "result"
    assert not ran_on_main_thread
    assert [list(progress.at(index)) for index in range(progress.count())] == [
        ["progress"]
    ]
    assert observations == [
        (
            QCoreApplication.instance().thread(),
            TaskState.SUCCEEDED,
            handle.result,
            handle.result,
        )
    ]
    assert handle.state is TaskState.SUCCEEDED
    assert handle.failure is None


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_callable_result_progress_and_signal_thread(qapp, launcher) -> None:
    """Return values and progress reach the Qt owner thread. 结果和进度回到 Qt 所在线程。"""
    callback_observations = []

    def work(left, right):
        task = current_task()
        task.report_progress(left)
        return right, QThread.isMainThread()

    handle = launcher(work, "progress", "result")
    progress = QSignalSpy(handle.progress)
    handle.succeeded.connect(
        lambda result: callback_observations.append(
            (QThread.currentThread(), handle.state, handle.result, result)
        )
    )

    _wait_for_finished(handle)
    _assert_success_outcome(handle, progress, callback_observations)


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_exceptions_are_structured_and_finish_once(qapp, launcher) -> None:
    """Exceptions become one structured failure. 异常转换为一次结构化失败。"""
    def fail():
        raise ValueError("real task failure")

    handle = launcher(fail)
    failed = QSignalSpy(handle.failed)
    finished = QSignalSpy(handle.finished)

    _wait_for_finished(handle, finished)

    assert failed.count() == 1
    assert finished.count() == 1
    assert isinstance(handle.failure, TaskFailure)
    assert isinstance(handle.failure.exception, ValueError)
    assert "real task failure" in handle.failure.traceback
    assert handle.result is None
    assert handle.state is TaskState.FAILED


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_cooperative_cancellation(qapp, launcher) -> None:
    """Cancellation stops context-aware work without termination. 取消协作停止任务且不强杀线程。"""
    worker_started = threading.Event()
    emergency_stop = threading.Event()

    def work():
        worker_started.set()
        while not emergency_stop.is_set():
            current_task().raise_if_cancelled()
            time.sleep(0.001)

    handle = launcher(work)
    cancelled = QSignalSpy(handle.cancelled)
    try:
        assert worker_started.wait(TASK_TIMEOUT_MS / 1000)
        assert handle.cancel()
        assert handle.cancel_requested
        _wait_for_finished(handle)
    finally:
        emergency_stop.set()

    assert cancelled.count() == 1
    assert handle.state is TaskState.CANCELLED
    assert not handle.cancel()
    assert handle.result is None
    assert handle.failure is None


def test_current_task_rejects_calls_outside_runner(qapp) -> None:
    """Task context is scoped to worker invocation. 任务上下文仅在后台调用中有效。"""
    with pytest.raises(RuntimeError, match="background task"):
        current_task()


def test_task_api_is_exported_from_public_modules(qapp) -> None:
    """Both supported import surfaces expose the task API. 两个公开导入面均暴露任务 API。"""
    import prismqml
    from prismqml.python import core

    names = {
        "TaskCancelledError",
        "TaskContext",
        "TaskFailure",
        "TaskHandle",
        "TaskState",
        "current_task",
        "run_in_pool",
        "run_in_thread",
        "shutdown_tasks",
    }

    assert all(name in prismqml.__all__ for name in names)
    assert all(name in core.__all__ for name in names)
    assert all(getattr(prismqml, name) is getattr(core, name) for name in names)


def test_app_shutdown_waits_for_active_dedicated_thread() -> None:
    """App teardown must not destroy a running QThread. App 退出不得销毁运行中的 QThread。"""
    completed = _run_app_shutdown_probe()
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "TASK_SHUTDOWN_OK=0:" in output
    assert "QThread: Destroyed while thread" not in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output
