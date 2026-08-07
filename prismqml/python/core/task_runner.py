# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Callable-based Qt background tasks. 基于可调用对象的 Qt 后台任务。"""

from contextvars import ContextVar
import math
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

from PySide6.QtCore import (
    QCoreApplication,
    QObject,
    QThread,
    QTimer,
    Qt,
    Signal,
    Slot,
)

from .logger import exception
from ._task_failures import build_task_failure, log_task_failure
from ._task_pool import TaskThreadPool, global_task_pool
from ._task_types import (
    _TaskOutcome,
    PoolSubmitPolicy,
    PoolTaskOptions,
    TaskCancelledError,
    TaskFailure,
    TaskRejectedError,
    TaskShutdownReport,
    TaskShutdownTimeoutError,
    TaskState,
)


_BACKEND_RELEASE_RETRY_MS = 1


class _TaskControl:
    """Thread-safe cancellation and completion state. 线程安全的取消与完成状态。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._outcome = None
        self._backend_stopped = threading.Event()

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    def request_cancel(self) -> bool:
        with self._lock:
            if self._outcome is not None or self._cancel_requested:
                return False
            self._cancel_requested = True
            return True

    def settle(self, state: TaskState, payload: Any) -> bool:
        with self._lock:
            if self._outcome is not None:
                return False
            self._outcome = _TaskOutcome(state, payload)
            return True

    def outcome(self) -> Optional[_TaskOutcome]:
        with self._lock:
            return self._outcome

    def mark_backend_stopped(self) -> None:
        self._backend_stopped.set()

    def wait_for_backend(self, timeout_ms: Optional[int]) -> bool:
        timeout = None if timeout_ms is None else timeout_ms / 1000
        return self._backend_stopped.wait(timeout)


class TaskContext:
    """Context available while a PrismQML task is running. PrismQML 任务运行上下文。"""

    def __init__(self, control: _TaskControl, report: Callable[[Any], None]) -> None:
        self._control = control
        self._report = report

    @property
    def cancel_requested(self) -> bool:
        """Return whether cancellation was requested. 返回是否已请求取消。"""
        return self._control.cancel_requested

    def report_progress(self, value: Any) -> None:
        """Publish one arbitrary progress value. 发布一个任意类型的进度值。"""
        self._report(value)

    def raise_if_cancelled(self) -> None:
        """Stop cooperatively when cancellation was requested. 收到取消请求时协作停止。"""
        if self.cancel_requested:
            raise TaskCancelledError("Background task cancellation was requested")

    def _request_cancel(self) -> bool:
        return self._control.request_cancel()

    def _settle(self, state: TaskState, payload: Any) -> bool:
        return self._control.settle(state, payload)


_CURRENT_TASK = ContextVar("prismqml_current_task", default=None)


def current_task() -> TaskContext:
    """Return the context for the current PrismQML background task. 返回当前后台任务上下文。"""
    context = _CURRENT_TASK.get()
    if context is None:
        raise RuntimeError("current_task() is only available inside a background task")
    return context


class _TaskEvents(QObject):
    """Cross-thread event bridge owned by a task handle. 任务句柄持有的跨线程事件桥。"""

    started = Signal()
    progress = Signal(object)
    settled = Signal(object, object)
    backend_stopped = Signal()


class _TaskExecution:
    """Execute one callable and convert its outcome. 执行一次调用并转换结果。"""

    def __init__(
        self,
        function: Callable[..., Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        context: TaskContext,
        events: _TaskEvents,
    ) -> None:
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._context = context
        self._events = events

    def run(self) -> None:
        if self._context.cancel_requested:
            self._settle(TaskState.CANCELLED, None)
            return
        self._events.started.emit()
        token = _CURRENT_TASK.set(self._context)
        try:
            result = self._function(*self._args, **self._kwargs)
        except TaskCancelledError:
            self._settle(TaskState.CANCELLED, None)
        except BaseException as caught:
            self._fail(caught)
        else:
            if self._context.cancel_requested:
                self._settle(TaskState.CANCELLED, None)
            else:
                self._settle(TaskState.SUCCEEDED, result)
        finally:
            _CURRENT_TASK.reset(token)

    def cancel_before_start(self) -> None:
        """Settle queued work removed before execution. 结算执行前被移除的排队任务。"""
        self._settle(TaskState.CANCELLED, None)

    def _fail(self, caught: BaseException) -> None:
        failure = build_task_failure(caught)
        self._settle(TaskState.FAILED, failure)
        log_task_failure(caught)

    def _settle(self, state: TaskState, payload: Any) -> None:
        if self._context._settle(state, payload):
            self._events.settled.emit(state, payload)


class TaskHandle(QObject):
    """Signals and control surface for one background task. 单个后台任务的信号与控制面。"""

    started = Signal()
    progress = Signal("QVariant")
    succeeded = Signal("QVariant")
    failed = Signal("QVariant")
    cancelled = Signal()
    finished = Signal()
    state_changed = Signal("QVariant")

    def __init__(self, control: _TaskControl) -> None:
        super().__init__()
        self._control = control
        self._state = TaskState.PENDING
        self._result = None
        self._failure = None
        self._waited_outcome = None
        self._waited_outcome_lock = threading.Lock()
        self._backend = None
        self._backend_lock = threading.RLock()
        self._backend_stopped = False
        self._backend_release_scheduled = False
        self._events = _TaskEvents(self)
        self._context = TaskContext(control, self._events.progress.emit)
        self._connect_events()

    @property
    def state(self) -> TaskState:
        """Return the published or explicitly waited state. 返回已发布或已等待的状态。"""
        outcome = self._get_waited_outcome()
        if outcome is not None:
            return outcome.state
        return self._state

    @property
    def result(self) -> Any:
        """Return the successful result, otherwise None. 返回成功结果，否则返回 None。"""
        outcome = self._get_waited_outcome()
        if outcome is not None and outcome.state is TaskState.SUCCEEDED:
            return outcome.payload
        return self._result

    @property
    def failure(self) -> Optional[TaskFailure]:
        """Return structured failure details, otherwise None. 返回结构化失败信息，否则返回 None。"""
        outcome = self._get_waited_outcome()
        if outcome is not None and outcome.state is TaskState.FAILED:
            return outcome.payload
        return self._failure

    @property
    def cancel_requested(self) -> bool:
        """Return whether cooperative cancellation was requested. 返回是否已请求协作取消。"""
        return self._context.cancel_requested

    def cancel(self) -> bool:
        """Request cooperative cancellation once. 请求一次协作取消。"""
        requested = self._context._request_cancel()
        backend = self._backend
        if requested and backend is not None:
            backend.request_cancel()
        return requested

    def wait(self, timeout_ms: Optional[int] = None) -> bool:
        """Wait for backend stop and expose its outcome. 等待后端停止并公开结果。"""
        _validate_timeout_ms(timeout_ms, "Task wait timeout")
        with self._backend_lock:
            if self._backend is None:
                stopped = self._control.wait_for_backend(timeout_ms)
            else:
                stopped = self._backend.wait(timeout_ms)
            if stopped:
                self._cache_waited_outcome()
                self._release_backend()
        return stopped

    def _get_waited_outcome(self) -> Optional[_TaskOutcome]:
        with self._waited_outcome_lock:
            return self._waited_outcome

    def _cache_waited_outcome(self) -> None:
        outcome = self._control.outcome()
        if outcome is None:
            return
        with self._waited_outcome_lock:
            self._waited_outcome = outcome

    def _connect_events(self) -> None:
        queued = Qt.ConnectionType.QueuedConnection
        self._events.started.connect(self._relay_started, queued)
        self._events.progress.connect(self._relay_progress, queued)
        self._events.settled.connect(self._relay_settled, queued)
        self._events.backend_stopped.connect(self._relay_backend_stopped, queued)

    @Slot()
    def _relay_started(self) -> None:
        self._publish_state(TaskState.RUNNING)
        self.started.emit()

    @Slot(object)
    def _relay_progress(self, value: Any) -> None:
        self.progress.emit(value)

    @Slot(object, object)
    def _relay_settled(self, state: TaskState, payload: Any) -> None:
        if state is TaskState.SUCCEEDED:
            self._result = payload
        elif state is TaskState.FAILED:
            self._failure = payload
        self._publish_state(state)
        if state is TaskState.SUCCEEDED:
            self.succeeded.emit(payload)
        elif state is TaskState.FAILED:
            self.failed.emit(payload)
        else:
            self.cancelled.emit()
        self.finished.emit()
        self._release_if_stopped()

    @Slot()
    def _relay_backend_stopped(self) -> None:
        self._backend_stopped = True
        self._release_if_stopped()

    def _publish_state(self, state: TaskState) -> None:
        self._state = state
        self.state_changed.emit(state)

    def _release_if_stopped(self) -> None:
        terminal = self._state in TaskState.terminal_states()
        if self._backend_stopped and terminal and not self._backend_release_scheduled:
            self._backend_release_scheduled = True
            QTimer.singleShot(0, self._release_backend)

    def _release_backend(self) -> None:
        with self._backend_lock:
            backend = self._backend
            if backend is None:
                return
            if not backend.wait(0):
                QTimer.singleShot(
                    _BACKEND_RELEASE_RETRY_MS,
                    self._release_backend,
                )
                return
            backend.release()
            self._backend = None
            _release_handle(self)

    def _discard_unstarted_backend(self) -> None:
        with self._backend_lock:
            backend = self._backend
            if backend is not None:
                backend.release()
                self._backend = None
            _release_handle(self)


_ACTIVE_HANDLES = {}
_ACTIVE_HANDLES_LOCK = threading.Lock()


def _retain_handle(handle: TaskHandle) -> None:
    with _ACTIVE_HANDLES_LOCK:
        _ACTIVE_HANDLES[id(handle)] = handle


def _release_handle(handle: TaskHandle) -> None:
    with _ACTIVE_HANDLES_LOCK:
        _ACTIVE_HANDLES.pop(id(handle), None)


def _active_handles() -> Tuple[TaskHandle, ...]:
    with _ACTIVE_HANDLES_LOCK:
        return tuple(_ACTIVE_HANDLES.values())


def _validate_timeout_ms(timeout_ms: Optional[int], label: str) -> None:
    if timeout_ms is None:
        return
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise TypeError(f"{label} must be an int or None")
    if timeout_ms < 0:
        raise ValueError(f"{label} must be non-negative or None")


def _remaining_timeout_ms(deadline: Optional[float]) -> Optional[int]:
    if deadline is None:
        return None
    return max(0, math.ceil((deadline - time.monotonic()) * 1000))


def _create_task(
    function: Callable[..., Any],
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Tuple[TaskHandle, _TaskExecution]:
    app = QCoreApplication.instance()
    if app is None:
        raise RuntimeError("A QCoreApplication is required before starting a task")
    if QThread.currentThread() != app.thread():
        raise RuntimeError(
            "Background tasks must be started from the Qt application thread"
        )
    if not callable(function):
        raise TypeError("Background task function must be callable")
    control = _TaskControl()
    handle = TaskHandle(control)
    execution = _TaskExecution(function, args, kwargs, handle._context, handle._events)
    _retain_handle(handle)
    return handle, execution


def _start_pool_backend(
    handle: TaskHandle,
    execution: _TaskExecution,
    options: PoolTaskOptions,
    pool: TaskThreadPool,
) -> None:
    from ._task_backends import _PoolRunnable

    try:
        backend = _PoolRunnable(execution, handle._events, handle._control, pool)
        handle._backend = backend
        if options.submit_policy is PoolSubmitPolicy.REQUIRE_AVAILABLE:
            if backend.try_start():
                return
            handle._discard_unstarted_backend()
            raise TaskRejectedError("No QThreadPool worker thread is available")
        backend.start(options.priority)
    except TaskRejectedError:
        raise
    except Exception as caught:
        handle._discard_unstarted_backend()
        exception(
            f"QThreadPool task submission failed: {type(caught).__name__}: {caught}"
        )
        raise


def _start_thread_backend(handle: TaskHandle, execution: _TaskExecution) -> None:
    from ._task_backends import _ThreadBackend

    try:
        backend = _ThreadBackend(execution, handle, handle._control)
        handle._backend = backend
        backend.start()
    except Exception as caught:
        handle._discard_unstarted_backend()
        exception(f"QThread task startup failed: {type(caught).__name__}: {caught}")
        raise


def run_in_pool(
    function: Callable[..., Any],
    /,
    *args: Any,
    task_options: Optional[PoolTaskOptions] = None,
    **kwargs: Any,
) -> TaskHandle:
    """Run a callable on a configured Qt thread pool. 在配置的 Qt 线程池运行调用。"""
    if task_options is None:
        task_options = PoolTaskOptions()
    elif not isinstance(task_options, PoolTaskOptions):
        raise TypeError("task_options must be a PoolTaskOptions or None")
    pool = (
        task_options.pool
        if task_options.pool is not None
        else global_task_pool()
    )
    handle, execution = _create_task(function, args, kwargs)
    _start_pool_backend(handle, execution, task_options, pool)
    return handle


def run_in_thread(
    function: Callable[..., Any], /, *args: Any, **kwargs: Any
) -> TaskHandle:
    """Run a callable on one dedicated QThread. 在独立 QThread 中运行可调用对象。"""
    handle, execution = _create_task(function, args, kwargs)
    _start_thread_backend(handle, execution)
    return handle


def shutdown_tasks(timeout_ms: Optional[int] = None) -> TaskShutdownReport:
    """Cancel active tasks and wait up to one shared deadline. 取消任务并等待统一截止时间。"""
    app = QCoreApplication.instance()
    if app is None:
        raise RuntimeError("A QCoreApplication is required before shutting down tasks")
    if QThread.currentThread() != app.thread():
        raise RuntimeError("shutdown_tasks() must be called from the Qt application thread")
    _validate_timeout_ms(timeout_ms, "Task shutdown timeout")
    handles = _active_handles()
    for handle in handles:
        handle.cancel()
    deadline = None
    if timeout_ms is not None:
        deadline = time.monotonic() + timeout_ms / 1000
    stopped_count = 0
    pending = []
    for handle in handles:
        if handle.wait(_remaining_timeout_ms(deadline)):
            stopped_count += 1
        else:
            pending.append(handle)
    return TaskShutdownReport(len(handles), stopped_count, tuple(pending))


__all__ = [
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
    "global_task_pool",
    "run_in_pool",
    "run_in_thread",
    "shutdown_tasks",
]
