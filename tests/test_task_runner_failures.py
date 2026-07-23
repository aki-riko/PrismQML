# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Task failure-path regressions. 后台任务失败路径回归。"""

import pytest
from PySide6.QtTest import QSignalSpy

import prismqml.python.core._task_failures as task_failures
from prismqml import TaskFailure, TaskState, run_in_pool, run_in_thread


TASK_TIMEOUT_MS = 3000


@pytest.mark.parametrize("launcher", (run_in_pool, run_in_thread))
def test_unprintable_exception_still_reaches_failed_terminal_state(
    qapp, launcher
) -> None:
    """Broken exception rendering must not lose completion. 异常渲染失败不得丢失终态。"""
    class UnprintableError(Exception):
        def __str__(self):
            raise RuntimeError("broken __str__")

    def fail():
        raise UnprintableError()

    handle = launcher(fail)
    failed = QSignalSpy(handle.failed)
    finished = QSignalSpy(handle.finished)

    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.FAILED
    assert isinstance(handle.failure, TaskFailure)
    assert isinstance(handle.failure.exception, UnprintableError)
    assert "UnprintableError" in handle.failure.traceback

    qapp.processEvents()
    assert failed.count() == 1
    assert finished.count() == 1


def test_logging_failure_cannot_replace_task_failure(qapp, monkeypatch) -> None:
    """Logger failures must not replace the business failure. 日志失败不得覆盖业务失败。"""
    def fail_logging(*_args, **_kwargs):
        raise OSError("logger unavailable")

    def fail_task():
        raise ValueError("business failure")

    monkeypatch.setattr(task_failures, "log_exception", fail_logging)
    handle = run_in_pool(fail_task)
    failed = QSignalSpy(handle.failed)
    finished = QSignalSpy(handle.finished)

    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.FAILED
    assert isinstance(handle.failure.exception, ValueError)
    assert "business failure" in handle.failure.traceback

    qapp.processEvents()
    assert failed.count() == 1
    assert finished.count() == 1


def test_traceback_rendering_failure_uses_safe_fallback(qapp, monkeypatch) -> None:
    """Traceback rendering errors must retain a useful failure. 堆栈渲染错误必须保留失败信息。"""
    def fail_rendering(*_args, **_kwargs):
        raise RuntimeError("renderer unavailable")

    def fail_task():
        raise LookupError("lookup failure")

    monkeypatch.setattr(
        task_failures.traceback_module,
        "format_exception",
        fail_rendering,
    )
    handle = run_in_thread(fail_task)

    assert handle.wait(TASK_TIMEOUT_MS)
    assert handle.state is TaskState.FAILED
    assert isinstance(handle.failure.exception, LookupError)
    assert handle.failure.traceback == (
        "LookupError: traceback rendering failed with RuntimeError"
    )
    qapp.processEvents()
