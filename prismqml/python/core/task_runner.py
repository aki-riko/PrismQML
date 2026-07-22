# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Callable-based Qt background tasks. 基于可调用对象的 Qt 后台任务。"""

from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
import threading
import traceback as traceback_module
from typing import Any, Callable, Dict, Optional, Tuple

from PySide6.QtCore import (
    QCoreApplication,
    QObject,
    QRunnable,
    QThread,
    QThreadPool,
    QTimer,
    Qt,
    Signal,
    Slot,
)

from .logger import exception


class TaskState(Enum):
    """Public background-task states. 公开后台任务状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def terminal_states(cls) -> Tuple["TaskState", ...]:
        """Return all terminal states. 返回全部终态。"""
        return cls.SUCCEEDED, cls.FAILED, cls.CANCELLED


class TaskCancelledError(Exception):
    """Raised when cooperative task cancellation is observed. 任务发现协作取消时抛出。"""


@dataclass(frozen=True)
class TaskFailure:
    """Structured exception details from a background task. 后台任务的结构化异常信息。"""

    exception: BaseException
    traceback: str


class _TaskControl:
    """Thread-safe cancellation and completion state. 线程安全的取消与完成状态。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._done = False
        self._backend_stopped = threading.Event()

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    def request_cancel(self) -> bool:
        with self._lock:
            if self._done or self._cancel_requested:
                return False
            self._cancel_requested = True
            return True

    def mark_done(self) -> None:
        with self._lock:
            self._done = True

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

    def _mark_done(self) -> None:
        self._control.mark_done()


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
            self._settle(TaskState.SUCCEEDED, result)
        finally:
            _CURRENT_TASK.reset(token)

    def _fail(self, caught: BaseException) -> None:
        rendered = "".join(
            traceback_module.format_exception(type(caught), caught, caught.__traceback__)
        )
        exception(
            f"Background task failed: {type(caught).__name__}: {caught}",
            tag="TaskRunner",
        )
        self._settle(
            TaskState.FAILED,
            TaskFailure(caught.with_traceback(None), rendered),
        )

    def _settle(self, state: TaskState, payload: Any) -> None:
        self._context._mark_done()
        self._events.settled.emit(state, payload)


class _PoolRunnable(QRunnable):
    """Internal QRunnable adapter. 内部 QRunnable 适配器。"""

    def __init__(
        self,
        execution: _TaskExecution,
        events: _TaskEvents,
        control: _TaskControl,
    ) -> None:
        super().__init__()
        self._execution = execution
        self._events = events
        self._control = control
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            self._execution.run()
        finally:
            self._control.mark_backend_stopped()
            self._events.backend_stopped.emit()

    def request_cancel(self) -> None:
        """Use the shared cooperative token for pool cancellation. 使用共享令牌协作取消。"""
        return None

    def wait(self, timeout_ms: Optional[int]) -> bool:
        """Wait until the pool callable has returned. 等待线程池任务返回。"""
        return self._control.wait_for_backend(timeout_ms)

    def release(self) -> None:
        """Leave Qt-owned runnable cleanup to QThreadPool. 由 QThreadPool 清理 runnable。"""
        return None


class _TaskWorker(QObject):
    """Internal worker-object adapter for QThread. QThread 的内部 worker-object 适配器。"""

    finished = Signal()

    def __init__(self, execution: _TaskExecution) -> None:
        super().__init__()
        self._execution = execution

    @Slot()
    def execute(self) -> None:
        try:
            self._execution.run()
        finally:
            self.finished.emit()


class _ThreadBackend:
    """Own one QThread and its worker. 持有一个 QThread 及其 worker。"""

    def __init__(
        self,
        execution: _TaskExecution,
        handle: "TaskHandle",
        control: _TaskControl,
    ) -> None:
        self._thread = QThread(handle)
        self._worker = _TaskWorker(execution)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.execute)
        self._worker.finished.connect(
            self._thread.quit,
            Qt.ConnectionType.DirectConnection,
        )
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(
            control.mark_backend_stopped,
            Qt.ConnectionType.DirectConnection,
        )
        self._thread.finished.connect(
            handle._relay_backend_stopped,
            Qt.ConnectionType.QueuedConnection,
        )
        # Let the retained handle own QThread until execution has fully stopped.
        # 由受保留的 handle 持有 QThread，直至执行完全停止。

    def start(self) -> None:
        self._thread.start()

    def request_cancel(self) -> None:
        self._thread.requestInterruption()

    def wait(self, timeout_ms: Optional[int]) -> bool:
        """Wait for QThread.run() to return completely. 等待 QThread.run() 完全返回。"""
        if timeout_ms is None:
            return self._thread.wait()
        return self._thread.wait(timeout_ms)

    def release(self) -> None:
        """Release invalid worker wrapper before the stopped thread. 先释放失效 worker 再释放线程。"""
        self._worker = None
        self._thread = None


class TaskHandle(QObject):
    """Signals and control surface for one background task. 单个后台任务的信号与控制面。"""

    started = Signal()
    progress = Signal(object)
    succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal()
    finished = Signal()
    state_changed = Signal(object)

    def __init__(self, control: _TaskControl) -> None:
        super().__init__()
        self._control = control
        self._state = TaskState.PENDING
        self._result = None
        self._failure = None
        self._backend = None
        self._backend_stopped = False
        self._backend_release_scheduled = False
        self._events = _TaskEvents(self)
        self._context = TaskContext(control, self._events.progress.emit)
        self._connect_events()

    @property
    def state(self) -> TaskState:
        """Return the last state published on the Qt thread. 返回 Qt 线程已发布的最新状态。"""
        return self._state

    @property
    def result(self) -> Any:
        """Return the successful result, otherwise None. 返回成功结果，否则返回 None。"""
        return self._result

    @property
    def failure(self) -> Optional[TaskFailure]:
        """Return structured failure details, otherwise None. 返回结构化失败信息，否则返回 None。"""
        return self._failure

    @property
    def cancel_requested(self) -> bool:
        """Return whether cooperative cancellation was requested. 返回是否已请求协作取消。"""
        return self._context.cancel_requested

    def cancel(self) -> bool:
        """Request cooperative cancellation once. 请求一次协作取消。"""
        requested = self._context._request_cancel()
        if requested and self._backend is not None:
            self._backend.request_cancel()
        return requested

    def wait(self, timeout_ms: Optional[int] = None) -> bool:
        """Wait until the execution backend has stopped. 等待执行后端完全停止。"""
        if timeout_ms is not None and timeout_ms < 0:
            raise ValueError("Task wait timeout must be non-negative or None")
        if self._backend is None:
            return self._control.wait_for_backend(timeout_ms)
        return self._backend.wait(timeout_ms)

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
        backend = self._backend
        if backend is None:
            return
        backend.wait(None)
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


def _create_task(
    function: Callable[..., Any],
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Tuple[TaskHandle, _TaskExecution]:
    app = QCoreApplication.instance()
    if app is None:
        raise RuntimeError("A QCoreApplication is required before starting a task")
    if QThread.currentThread() != app.thread():
        raise RuntimeError("Background tasks must be started from the Qt application thread")
    if not callable(function):
        raise TypeError("Background task function must be callable")
    control = _TaskControl()
    handle = TaskHandle(control)
    execution = _TaskExecution(function, args, kwargs, handle._context, handle._events)
    _retain_handle(handle)
    return handle, execution


def run_in_pool(function: Callable[..., Any], /, *args: Any, **kwargs: Any) -> TaskHandle:
    """Run a callable on Qt's global thread pool. 在线程池中运行可调用对象。"""
    handle, execution = _create_task(function, args, kwargs)
    runnable = _PoolRunnable(execution, handle._events, handle._control)
    handle._backend = runnable
    QThreadPool.globalInstance().start(runnable)
    return handle


def run_in_thread(function: Callable[..., Any], /, *args: Any, **kwargs: Any) -> TaskHandle:
    """Run a callable on one dedicated QThread. 在独立 QThread 中运行可调用对象。"""
    handle, execution = _create_task(function, args, kwargs)
    backend = _ThreadBackend(execution, handle, handle._control)
    handle._backend = backend
    backend.start()
    return handle


def shutdown_tasks() -> int:
    """Cancel and wait for every active task without force termination. 取消并等待全部任务且不强杀。"""
    handles = _active_handles()
    for handle in handles:
        handle.cancel()
    for handle in handles:
        handle.wait()
        handle._release_backend()
    return len(handles)


__all__ = [
    "TaskCancelledError",
    "TaskContext",
    "TaskFailure",
    "TaskHandle",
    "TaskState",
    "current_task",
    "run_in_pool",
    "run_in_thread",
    "shutdown_tasks",
]
