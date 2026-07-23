# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Managed QThreadPool for observable task queues. 可观测任务队列的受管线程池。"""

import threading
from typing import Any, Dict, Tuple

from PySide6.QtCore import QCoreApplication, QThread, QThreadPool


class TaskThreadPool(QThreadPool):
    """Settle PrismQML tasks removed by clear(). 结算被 clear() 移除的 PrismQML 任务。"""

    def __init__(self) -> None:
        super().__init__()
        self._operations_lock = threading.RLock()
        self._pending_lock = threading.Lock()
        self._pending: Dict[int, Any] = {}

    def clear(self) -> None:
        """Cancel managed queued tasks before clearing others. 先取消受管排队任务再清理其余任务。"""
        with self._operations_lock:
            for runnable in self._pending_tasks():
                runnable.cancel_from_pool_clear()
            super().clear()

    def _start_task(self, runnable: Any, priority: int) -> None:
        with self._operations_lock:
            self._register_pending(runnable)
            try:
                super().start(runnable, priority)
            except Exception:
                self._discard_pending(runnable)
                raise

    def _try_start_task(self, runnable: Any) -> bool:
        with self._operations_lock:
            self._register_pending(runnable)
            started = super().tryStart(runnable)
            if not started:
                self._discard_pending(runnable)
            return started

    def _try_take_task(self, runnable: Any) -> bool:
        with self._operations_lock:
            if not self._is_pending(runnable) or not super().tryTake(runnable):
                return False
            self._discard_pending(runnable)
            return True

    def _mark_task_started(self, runnable: Any) -> None:
        self._discard_pending(runnable)

    def _register_pending(self, runnable: Any) -> None:
        with self._pending_lock:
            self._pending[id(runnable)] = runnable

    def _discard_pending(self, runnable: Any) -> None:
        with self._pending_lock:
            self._pending.pop(id(runnable), None)

    def _is_pending(self, runnable: Any) -> bool:
        with self._pending_lock:
            return self._pending.get(id(runnable)) is runnable

    def _pending_tasks(self) -> Tuple[Any, ...]:
        with self._pending_lock:
            return tuple(self._pending.values())


_GLOBAL_TASK_POOL = None
_GLOBAL_TASK_POOL_LOCK = threading.Lock()


def global_task_pool() -> TaskThreadPool:
    """Return the process-wide managed task pool. 返回进程级受管任务线程池。"""
    app = QCoreApplication.instance()
    if app is None:
        raise RuntimeError("A QCoreApplication is required before accessing the task pool")
    if QThread.currentThread() != app.thread():
        raise RuntimeError("The task pool must be accessed from the Qt application thread")
    global _GLOBAL_TASK_POOL
    with _GLOBAL_TASK_POOL_LOCK:
        if _GLOBAL_TASK_POOL is None:
            _GLOBAL_TASK_POOL = TaskThreadPool()
        return _GLOBAL_TASK_POOL


__all__ = ["TaskThreadPool", "global_task_pool"]
