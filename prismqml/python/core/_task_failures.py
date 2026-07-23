# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Fail-safe task exception conversion. 任务异常的失效安全转换。"""

import logging
import traceback as traceback_module

from ._task_types import TaskFailure
from .logger import exception as log_exception


def build_task_failure(caught: BaseException) -> TaskFailure:
    """Detach and render an exception without invoking unsafe overrides. 安全分离并渲染异常。"""
    try:
        rendered = "".join(
            traceback_module.format_exception(
                type(caught), caught, caught.__traceback__
            )
        )
    except BaseException as render_error:
        rendered = (
            f"{type(caught).__name__}: traceback rendering failed "
            f"with {type(render_error).__name__}"
        )
    detached = BaseException.with_traceback(caught, None)
    return TaskFailure(detached, rendered)


def log_task_failure(caught: BaseException) -> None:
    """Log after settlement without risking task finalization. 结算后记录且不破坏任务终态。"""
    try:
        log_exception(
            f"Background task failed: {type(caught).__name__}",
            tag="TaskRunner",
        )
    except Exception as log_error:
        logging.getLogger(__name__).error(
            "Task failure logging failed: %s",
            type(log_error).__name__,
            exc_info=True,
        )


__all__ = ["build_task_failure", "log_task_failure"]
