# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Monitor a Windows test Job for windows, exits, and timeouts.

监控 Windows 测试 Job 的窗口、退出与超时状态。
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Protocol

if __package__:
    from . import _windows_test_api as _api
else:
    import _windows_test_api as _api


class _WindowsBoundary(Protocol):
    def active_process_count(self) -> int: ...

    def root_exit_code(self) -> int | None: ...

    def terminate(self, exit_code: int) -> bool: ...

    def visible_job_windows(self) -> list[dict]: ...


@dataclass(frozen=True)
class _RunOptions:
    timeout: float | None
    logger: logging.Logger
    timeout_exit_code: int
    cleanup_failure_exit_code: int
    visible_window_exit_code: int


def _terminate_boundary_result(
    boundary: _WindowsBoundary,
    requested_exit_code: int,
    options: _RunOptions,
    failure_message: str,
) -> int:
    if boundary.terminate(requested_exit_code):
        return requested_exit_code
    options.logger.error(failure_message)
    return options.cleanup_failure_exit_code


def _visible_window_result(
    boundary: _WindowsBoundary,
    visible_windows: list[dict],
    options: _RunOptions,
) -> int:
    for window in visible_windows:
        options.logger.error(
            "[test-process] visible test window: %s",
            json.dumps(window, ensure_ascii=False, sort_keys=True),
        )
    result = _terminate_boundary_result(
        boundary,
        options.visible_window_exit_code,
        options,
        "[test-process] visible-window cleanup was incomplete",
    )
    if result == options.visible_window_exit_code:
        options.logger.error(
            "[test-process] visible_windows=%s / job_active_processes=0",
            len(visible_windows),
        )
    return result


def _empty_job_termination_result(
    boundary: _WindowsBoundary,
    requested_exit_code: int,
    options: _RunOptions,
    failure_message: str,
) -> int:
    result = _terminate_boundary_result(
        boundary,
        requested_exit_code,
        options,
        failure_message,
    )
    if result == requested_exit_code:
        options.logger.info(
            "[test-process] visible_windows=0 / job_active_processes=0"
        )
    return result


def _root_exit_state(
    boundary: _WindowsBoundary,
    root_exit_code: int | None,
    root_exit_at: float | None,
) -> tuple[int | None, float | None]:
    if root_exit_code is not None:
        return root_exit_code, root_exit_at
    root_exit_code = boundary.root_exit_code()
    if root_exit_code is not None:
        root_exit_at = time.monotonic()
    return root_exit_code, root_exit_at


def _completion_result(
    boundary: _WindowsBoundary,
    root_exit_code: int | None,
    root_exit_at: float | None,
    logger: logging.Logger,
) -> tuple[int | None, int | None, float | None]:
    active_processes = boundary.active_process_count()
    root_exit_code, root_exit_at = _root_exit_state(
        boundary,
        root_exit_code,
        root_exit_at,
    )
    if root_exit_code is not None and active_processes == 0:
        logger.info("[test-process] visible_windows=0 / job_active_processes=0")
        return root_exit_code, root_exit_code, root_exit_at
    return None, root_exit_code, root_exit_at


def _expiration_result(
    boundary: _WindowsBoundary,
    deadline: float | None,
    root_exit_at: float | None,
    options: _RunOptions,
) -> int | None:
    now = time.monotonic()
    if deadline is not None and now >= deadline:
        options.logger.error(
            "[test-process] child timed out after %gs",
            options.timeout,
        )
        return _empty_job_termination_result(
            boundary,
            options.timeout_exit_code,
            options,
            "[test-process] timeout cleanup was incomplete",
        )
    if root_exit_at is None or (
        now - root_exit_at < _api.WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS
    ):
        return None
    options.logger.error("[test-process] descendants remained after root exit")
    return _empty_job_termination_result(
        boundary,
        options.cleanup_failure_exit_code,
        options,
        "[test-process] descendant cleanup was incomplete",
    )


def _detected_visible_window_result(
    boundary: _WindowsBoundary,
    options: _RunOptions,
) -> int | None:
    visible_windows = boundary.visible_job_windows()
    if not visible_windows:
        return None
    return _visible_window_result(boundary, visible_windows, options)


def _monitor_windows_child(
    boundary: _WindowsBoundary,
    options: _RunOptions,
) -> int:
    deadline = (
        None if options.timeout is None else time.monotonic() + options.timeout
    )
    root_exit_at = None
    root_exit_code = None
    while True:
        result = _detected_visible_window_result(boundary, options)
        if result is not None:
            return result
        result, root_exit_code, root_exit_at = _completion_result(
            boundary,
            root_exit_code,
            root_exit_at,
            options.logger,
        )
        if result is not None:
            return result
        result = _expiration_result(
            boundary,
            deadline,
            root_exit_at,
            options,
        )
        if result is not None:
            return result
        time.sleep(_api.WINDOW_POLL_INTERVAL_SECONDS)
