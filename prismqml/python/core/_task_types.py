# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Types shared by the callable task API. 可调用任务 API 的共享类型。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple, TYPE_CHECKING

from ._task_pool import TaskThreadPool

if TYPE_CHECKING:
    from .task_runner import TaskHandle


class TaskState(Enum):
    """Public background-task states. 公开后台任务状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def terminal_states(cls) -> Tuple[TaskState, ...]:
        """Return all terminal states. 返回全部终态。"""
        return cls.SUCCEEDED, cls.FAILED, cls.CANCELLED


class PoolSubmitPolicy(Enum):
    """Control whether pool work may wait in a queue. 控制线程池任务是否允许排队。"""

    QUEUE = "queue"
    REQUIRE_AVAILABLE = "require_available"


class TaskCancelledError(Exception):
    """Raised when cooperative task cancellation is observed. 任务发现协作取消时抛出。"""


@dataclass(frozen=True)
class TaskFailure:
    """Structured exception details from a background task. 后台任务的结构化异常信息。"""

    exception: BaseException
    traceback: str


class TaskRejectedError(RuntimeError):
    """Raised when backpressure rejects a pool submission. 背压拒绝线程池提交时抛出。"""


@dataclass(frozen=True)
class PoolTaskOptions:
    """Options for one QThreadPool submission. 单次 QThreadPool 提交选项。"""

    pool: Optional[TaskThreadPool] = None
    priority: int = 0
    submit_policy: PoolSubmitPolicy = PoolSubmitPolicy.QUEUE

    def __post_init__(self) -> None:
        if self.pool is not None and not isinstance(self.pool, TaskThreadPool):
            raise TypeError("PoolTaskOptions.pool must be a TaskThreadPool or None")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise TypeError("PoolTaskOptions.priority must be an int")
        if not isinstance(self.submit_policy, PoolSubmitPolicy):
            raise TypeError("PoolTaskOptions.submit_policy must be a PoolSubmitPolicy")


@dataclass(frozen=True)
class _TaskOutcome:
    """Thread-safe immutable task outcome. 线程安全的不可变任务结果。"""

    state: TaskState
    payload: Any


@dataclass(frozen=True)
class TaskShutdownReport:
    """Result of one bounded task-shutdown attempt. 单次有界任务退出结果。"""

    requested_count: int
    stopped_count: int
    pending: Tuple[TaskHandle, ...]

    @property
    def complete(self) -> bool:
        """Return whether every captured task stopped. 返回本次捕获任务是否全部停止。"""
        return not self.pending

    @property
    def pending_count(self) -> int:
        """Return the number of tasks still running. 返回仍在运行的任务数。"""
        return len(self.pending)


class TaskShutdownTimeoutError(RuntimeError):
    """Prevent unsafe Qt teardown while tasks remain active. 活任务存在时阻止不安全清理。"""

    def __init__(self, report: TaskShutdownReport) -> None:
        self.report = report
        super().__init__(
            f"{report.pending_count} background task(s) exceeded the shutdown deadline"
        )
