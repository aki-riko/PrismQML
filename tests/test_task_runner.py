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
from PySide6.QtCore import QCoreApplication, QEventLoop, QThread, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QSignalSpy

import prismqml.python.core.task_runner as task_runner_module
from prismqml import (
    PoolSubmitPolicy,
    PoolTaskOptions,
    TaskFailure,
    TaskRejectedError,
    TaskShutdownReport,
    TaskShutdownTimeoutError,
    TaskState,
    TaskThreadPool,
    current_task,
    run_in_pool,
    run_in_thread,
    shutdown_tasks,
)


TASK_TIMEOUT_MS = 3000
THREAD_RELEASE_STRESS_CYCLES = 200
REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"

_APP_SHUTDOWN_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import time
import threading
import shiboken6
from PySide6.QtCore import QTimer
from prismqml import App, run_in_thread

app = App([])
worker_started = threading.Event()

def work():
    worker_started.set()
    time.sleep(0.1)

started_at = time.monotonic()
run_in_thread(work)
if not worker_started.wait(3.0):
    print("TASK_START_TIMEOUT", flush=True)
    raise SystemExit(4)
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


def _cancel_one_dedicated_task() -> None:
    """Cancel one dedicated worker and drain its backend. 取消单个独立 worker 并释放后端。"""
    worker_started = threading.Event()
    emergency_stop = threading.Event()

    def work():
        worker_started.set()
        while not emergency_stop.is_set():
            current_task().raise_if_cancelled()
            time.sleep(0.0005)

    handle = run_in_thread(work)
    try:
        assert worker_started.wait(TASK_TIMEOUT_MS / 1000)
        assert handle.cancel()
        _wait_for_finished(handle)
    finally:
        emergency_stop.set()


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


def test_success_string_is_a_native_qml_value(qapp) -> None:
    """QML receives strings instead of PyObjectWrapper. QML 接收原生字符串而非包装对象。"""
    handle = run_in_pool(lambda: "master")
    engine = QQmlEngine()
    warnings = []
    engine.warnings.connect(
        lambda messages: warnings.extend(message.toString() for message in messages)
    )
    engine.rootContext().setContextProperty("taskHandle", handle)
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
QtObject {
    property string branch: ""
    Component.onCompleted: taskHandle.succeeded.connect(function(result) {
        branch = result
    })
}
""",
        QUrl("task_result.qml"),
    )
    root = component.create()

    assert root is not None, [error.toString() for error in component.errors()]
    _wait_for_finished(handle)
    QCoreApplication.processEvents()

    assert root.property("branch") == "master"
    assert warnings == []


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


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_wait_exposes_outcome_before_queued_signals(qapp, launcher) -> None:
    """A successful wait makes the final outcome readable. wait 成功后结果立即可读。"""
    handle = launcher(lambda: 73)
    finished = QSignalSpy(handle.finished)

    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.SUCCEEDED
    assert handle.result == 73
    assert handle.failure is None
    assert finished.count() == 0

    qapp.processEvents()
    assert finished.count() == 1


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_wait_exposes_failure_before_queued_signals(qapp, launcher) -> None:
    """A waited failure is immediately inspectable. wait 返回后失败信息立即可读。"""
    def fail():
        raise ValueError("waited failure")

    handle = launcher(fail)
    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.FAILED
    assert isinstance(handle.failure, TaskFailure)
    assert isinstance(handle.failure.exception, ValueError)
    assert "waited failure" in handle.failure.traceback


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_wait_timeout_keeps_running_task_owned(qapp, launcher) -> None:
    """A timed-out wait keeps the backend alive for retry. wait 超时后保留后端供重试。"""
    worker_started = threading.Event()
    release_worker = threading.Event()
    handle = launcher(
        lambda: (worker_started.set(), release_worker.wait(), "complete")[-1]
    )
    try:
        assert worker_started.wait(TASK_TIMEOUT_MS / 1000)
        assert not handle.wait(20)
        assert handle in task_runner_module._active_handles()
    finally:
        release_worker.set()

    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.SUCCEEDED
    assert handle.result == "complete"


def test_concurrent_waiters_observe_one_released_backend(qapp) -> None:
    """Concurrent waits share one safe backend release. 并发等待共享一次安全后端释放。"""
    release_worker = threading.Event()
    handle = run_in_thread(lambda: (release_worker.wait(), "complete")[-1])
    observations = []
    waiters = [
        threading.Thread(
            target=lambda: observations.append(handle.wait(TASK_TIMEOUT_MS)),
            daemon=True,
        )
        for _index in range(2)
    ]
    for waiter in waiters:
        waiter.start()
    release_worker.set()
    for waiter in waiters:
        waiter.join(TASK_TIMEOUT_MS / 1000)

    assert observations == [True, True]
    assert handle.state is TaskState.SUCCEEDED
    assert handle.result == "complete"


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_cleanup_return_after_cancel_is_cancelled(qapp, launcher) -> None:
    """An accepted cancellation wins over a cleanup return. 已接受取消优先于清理返回。"""
    worker_started = threading.Event()

    def cleanup_after_cancel():
        worker_started.set()
        while not current_task().cancel_requested:
            time.sleep(0.001)
        return "cleanup complete"

    handle = launcher(cleanup_after_cancel)
    cancelled = QSignalSpy(handle.cancelled)
    assert worker_started.wait(TASK_TIMEOUT_MS / 1000)
    assert handle.cancel()
    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.CANCELLED
    assert handle.result is None

    qapp.processEvents()
    assert cancelled.count() == 1


def test_custom_pool_priority_controls_queued_order(qapp) -> None:
    """Custom pool priority orders queued work. 自定义线程池优先级控制排队顺序。"""
    pool = TaskThreadPool()
    pool.setMaxThreadCount(1)
    blocker_started = threading.Event()
    release_blocker = threading.Event()
    execution_order = []
    blocker = run_in_pool(
        lambda: (blocker_started.set(), release_blocker.wait()),
        task_options=PoolTaskOptions(pool=pool),
    )
    try:
        assert blocker_started.wait(TASK_TIMEOUT_MS / 1000)
        low = run_in_pool(
            lambda: execution_order.append("low"),
            task_options=PoolTaskOptions(pool=pool, priority=-10),
        )
        high = run_in_pool(
            lambda: execution_order.append("high"),
            task_options=PoolTaskOptions(pool=pool, priority=10),
        )
        release_blocker.set()

        assert blocker.wait(TASK_TIMEOUT_MS)
        assert high.wait(TASK_TIMEOUT_MS)
        assert low.wait(TASK_TIMEOUT_MS)
        assert execution_order == ["high", "low"]
    finally:
        release_blocker.set()
        pool.waitForDone(TASK_TIMEOUT_MS)


def test_queued_pool_task_can_be_cancelled_before_start(qapp) -> None:
    """Queued cancellation removes work without executing it. 排队取消不执行任务。"""
    pool = TaskThreadPool()
    pool.setMaxThreadCount(1)
    blocker_started = threading.Event()
    release_blocker = threading.Event()
    queued_executed = threading.Event()
    options = PoolTaskOptions(pool=pool)

    def block_pool():
        blocker_started.set()
        release_blocker.wait()

    blocker = run_in_pool(block_pool, task_options=options)
    try:
        assert blocker_started.wait(TASK_TIMEOUT_MS / 1000)
        queued = run_in_pool(queued_executed.set, task_options=options)
        assert queued.cancel()
        assert queued.wait(TASK_TIMEOUT_MS)
        assert queued.state is TaskState.CANCELLED
        assert not queued_executed.is_set()
    finally:
        release_blocker.set()
        assert blocker.wait(TASK_TIMEOUT_MS)
        pool.waitForDone(TASK_TIMEOUT_MS)


def test_require_available_policy_rejects_without_leaking_handle(qapp) -> None:
    """Backpressure rejects when the custom pool is busy. 线程池繁忙时背压拒绝。"""
    pool = TaskThreadPool()
    pool.setMaxThreadCount(1)
    blocker_started = threading.Event()
    release_blocker = threading.Event()
    blocker = run_in_pool(
        lambda: (blocker_started.set(), release_blocker.wait()),
        task_options=PoolTaskOptions(pool=pool),
    )
    try:
        assert blocker_started.wait(TASK_TIMEOUT_MS / 1000)
        retained_before = len(task_runner_module._active_handles())
        options = PoolTaskOptions(
            pool=pool,
            submit_policy=PoolSubmitPolicy.REQUIRE_AVAILABLE,
        )

        with pytest.raises(TaskRejectedError, match="available"):
            run_in_pool(lambda: None, task_options=options)

        assert len(task_runner_module._active_handles()) == retained_before
    finally:
        release_blocker.set()
        assert blocker.wait(TASK_TIMEOUT_MS)
        pool.waitForDone(TASK_TIMEOUT_MS)


def test_shutdown_timeout_reports_and_retains_non_cooperative_task(qapp) -> None:
    """Bounded shutdown reports live work for a safe retry. 有界退出保留活任务供重试。"""
    worker_started = threading.Event()
    release_worker = threading.Event()

    def ignore_cancel_until_released():
        worker_started.set()
        release_worker.wait()

    handle = run_in_thread(ignore_cancel_until_released)
    assert worker_started.wait(TASK_TIMEOUT_MS / 1000)
    try:
        report = shutdown_tasks(20)
        assert isinstance(report, TaskShutdownReport)
        assert report.requested_count == 1
        assert report.stopped_count == 0
        assert report.pending == (handle,)
        assert not report.complete
    finally:
        release_worker.set()

    retried = shutdown_tasks(TASK_TIMEOUT_MS)
    assert retried.complete
    assert retried.stopped_count == 1


def test_current_task_rejects_calls_outside_runner(qapp) -> None:
    """Task context is scoped to worker invocation. 任务上下文仅在后台调用中有效。"""
    with pytest.raises(RuntimeError, match="background task"):
        current_task()


def test_task_api_is_exported_from_public_modules(qapp) -> None:
    """Both supported import surfaces expose the task API. 两个公开导入面均暴露任务 API。"""
    import prismqml
    from prismqml.python import core

    names = {
        "PoolSubmitPolicy",
        "PoolTaskOptions",
        "TaskCancelledError",
        "TaskContext",
        "TaskFailure",
        "TaskHandle",
        "TaskRejectedError",
        "TaskShutdownReport",
        "TaskShutdownTimeoutError",
        "TaskState",
        "TaskThreadPool",
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


def test_backend_release_retries_before_dropping_ownership(qapp, monkeypatch) -> None:
    """Backend wrappers stay owned until their native work stops. 后端原生工作停止前保持所有权。"""
    events = []
    retries = []

    def wait_for_backend(_self, timeout):
        events.append(("wait", timeout))
        return sum(event[0] == "wait" for event in events) > 1

    backend = type("BackendStub", (), {
        "wait": wait_for_backend,
        "release": lambda _self: events.append(("release",)),
    })()
    handle = task_runner_module.TaskHandle(task_runner_module._TaskControl())
    handle._backend = backend
    monkeypatch.setattr(
        task_runner_module,
        "QTimer",
        type(
            "TimerStub",
            (),
            {
                "singleShot": staticmethod(
                    lambda delay, callback: retries.append((delay, callback))
                ),
            },
        ),
    )
    monkeypatch.setattr(
        task_runner_module,
        "_release_handle",
        lambda current: events.append(("drop", current)),
    )

    handle._release_backend()

    assert events == [("wait", 0)]
    assert handle._backend is backend
    assert len(retries) == 1
    assert retries[0][0] == task_runner_module._BACKEND_RELEASE_RETRY_MS

    retries[0][1]()

    assert events == [("wait", 0), ("wait", 0), ("release",), ("drop", handle)]
    assert handle._backend is None


def test_dedicated_thread_release_survives_repeated_cancellation(qapp) -> None:
    """Repeated cancellation must not double-delete QThread. 重复取消不得双重销毁 QThread。"""
    for _iteration in range(THREAD_RELEASE_STRESS_CYCLES):
        _cancel_one_dedicated_task()
        qapp.processEvents()
