# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Structured Windows test-boundary results. Windows 测试边界结构化结果。"""

from __future__ import annotations

import json
import logging


BOUNDARY_RESULT_PREFIX = "[test-process] boundary_result="


def capture_boundary_result(boundary) -> dict:
    process = getattr(boundary, "process", None)
    result = {
        "desktop": getattr(boundary, "desktop_name", None),
        "job": getattr(boundary, "job_name", None),
        "root_process_id": int(getattr(process, "dwProcessId", 0)),
    }
    active_process_count = getattr(boundary, "active_process_count", None)
    if not callable(active_process_count):
        result["final_active_processes"] = None
        result["active_process_error"] = "active_process_count unavailable"
        return result
    try:
        result["final_active_processes"] = active_process_count()
    except (OSError, RuntimeError) as error:
        result["final_active_processes"] = None
        result["active_process_error"] = str(error)
    return result


def log_boundary_result(
    snapshot: dict,
    exit_code: int,
    cleanup_succeeded: bool,
    logger: logging.Logger,
) -> None:
    result = dict(snapshot)
    result["exit_code"] = exit_code
    result["cleanup_succeeded"] = cleanup_succeeded
    logger.info(
        "%s%s",
        BOUNDARY_RESULT_PREFIX,
        json.dumps(result, ensure_ascii=False, sort_keys=True),
    )
