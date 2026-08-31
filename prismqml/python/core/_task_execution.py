# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Task control and callable execution internals. 任务控制与可调用执行内部实现。"""

from contextvars import ContextVar
import threading
from typing import Any, Callable, Dict, Optional, Tuple

import shiboken6
from PySide6.QtCore import QObject, Signal

from ._task_failures import build_task_failure, log_task_failure
from .logger import debug
from ._task_types import TaskCancelledError, TaskState, _TaskOutcome


def _emit_task_signal(source: QObject, signal_name: str, *args: Any) -> bool:
    """Emit a task signal while tolerating owner teardown. 任务所有者销毁时安全发信号。"""
    if not shiboken6.isValid(source):
        debug(
            f"Skip task signal {signal_name}: signal source is already deleted",
            tag="TaskRunner",
        )
        return False
    try:
        getattr(source, signal_name).emit(*args)
    except RuntimeError:
        if shiboken6.isValid(source):
            raise
        debug(
            f"Skip task signal {signal_name}: signal source was deleted during emit",
            tag="TaskRunner",
        )
        return False
    return True


class _TaskControl:
    """Thread-safe cancellation and completion state. 线程安全的取消与完成状态。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._outcome = None
        self._backend_stopped = threading.Event()
        self._backend_stop_callbacks = []
        self._backend_stop_marked = False

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
        with self._lock:
            self._backend_stop_marked = True
            callbacks = tuple(self._backend_stop_callbacks)
            self._backend_stop_callbacks.clear()
        for callback in callbacks:
            callback()
        self._backend_stopped.set()

    def run_when_backend_stops(self, callback: Callable[[], None]) -> None:
        """Run cleanup after native work stops. 原生任务停止后执行清理。"""
        with self._lock:
            if not self._backend_stop_marked:
                self._backend_stop_callbacks.append(callback)
                return
        callback()

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
        _emit_task_signal(self._events, "started")
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
        """Settle queued work removed before execution. 结算执行前被排队移除的任务。"""
        self._settle(TaskState.CANCELLED, None)

    def _fail(self, caught: BaseException) -> None:
        failure = build_task_failure(caught)
        self._settle(TaskState.FAILED, failure)
        log_task_failure(caught)

    def _settle(self, state: TaskState, payload: Any) -> None:
        if self._context._settle(state, payload):
            _emit_task_signal(self._events, "settled", state, payload)

    def release_events_later(self) -> None:
        """Delete the event bridge on its Qt thread. 在事件桥所属 Qt 线程销毁。"""
        if shiboken6.isValid(self._events):
            self._events.deleteLater()
