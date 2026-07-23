# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Qt execution backends for callable tasks. 可调用任务的 Qt 执行后端。"""

import threading
from typing import Any, Optional

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, Qt, Signal, Slot


class _PoolRunnable(QRunnable):
    """Run one task in a caller-selected QThreadPool. 在指定线程池运行单个任务。"""

    def __init__(
        self,
        execution: Any,
        events: QObject,
        control: Any,
        pool: QThreadPool,
    ) -> None:
        super().__init__()
        self._execution = execution
        self._events = events
        self._control = control
        self._pool = pool
        self._lifecycle_lock = threading.Lock()
        # Non-auto-delete is required for safe QThreadPool.tryTake() use.
        # 安全使用 QThreadPool.tryTake() 必须关闭自动删除以规避 ABA 问题。
        self.setAutoDelete(False)

    def start(self, priority: int) -> None:
        """Queue the runnable with a priority. 按优先级提交到队列。"""
        self._pool.start(self, priority)

    def try_start(self) -> bool:
        """Start only when a worker thread is available. 仅在线程可用时启动。"""
        return self._pool.tryStart(self)

    def run(self) -> None:
        execution = self._execution
        if execution is None:
            return
        try:
            execution.run()
        finally:
            self._control.mark_backend_stopped()
            self._events.backend_stopped.emit()

    def request_cancel(self) -> None:
        """Remove queued work when possible, otherwise stay cooperative. 优先移除排队任务。"""
        with self._lifecycle_lock:
            pool = self._pool
            execution = self._execution
            control = self._control
            events = self._events
            if pool is None or execution is None or control is None or events is None:
                return
            if not pool.tryTake(self):
                return
            execution.cancel_before_start()
            control.mark_backend_stopped()
            events.backend_stopped.emit()

    def wait(self, timeout_ms: Optional[int]) -> bool:
        """Wait until the pool callable has returned. 等待线程池任务返回。"""
        return self._control.wait_for_backend(timeout_ms)

    def release(self) -> None:
        """Drop retained Python objects after execution stops. 后端停止后释放 Python 对象。"""
        with self._lifecycle_lock:
            self._execution = None
            self._events = None
            self._control = None
            self._pool = None


class _TaskWorker(QObject):
    """Internal worker-object adapter for QThread. QThread 内部 worker 适配器。"""

    finished = Signal()

    def __init__(self, execution: Any) -> None:
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

    def __init__(self, execution: Any, handle: QObject, control: Any) -> None:
        self._thread = QThread(handle)
        self._worker = _TaskWorker(execution)
        self._lifecycle_lock = threading.Lock()
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

    def start(self) -> None:
        """Start the dedicated thread. 启动独立线程。"""
        self._thread.start()

    def request_cancel(self) -> None:
        """Request cooperative QThread interruption. 请求协作式 QThread 中断。"""
        with self._lifecycle_lock:
            thread = self._thread
            if thread is not None:
                thread.requestInterruption()

    def wait(self, timeout_ms: Optional[int]) -> bool:
        """Wait for QThread.run() to return completely. 等待 QThread.run() 完全返回。"""
        if timeout_ms is None:
            return self._thread.wait()
        return self._thread.wait(timeout_ms)

    def release(self) -> None:
        """Release invalid worker wrapper before the stopped thread. 先释放失效 worker。"""
        with self._lifecycle_lock:
            self._worker = None
            self._thread = None
