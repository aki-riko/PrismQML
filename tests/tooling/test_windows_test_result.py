# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Windows boundary-result failure records. Windows 边界失败结果记录。"""

from __future__ import annotations

import json
import logging
import sys
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows private Desktop only",
)

if sys.platform == "win32":
    import scripts._test_support.windows.process as windows_test_process
    from scripts._test_support.windows.result import BOUNDARY_RESULT_PREFIX
    from scripts.test_process import (
        TEST_CLEANUP_FAILURE_EXIT_CODE,
        TEST_TIMEOUT_EXIT_CODE,
        TEST_VISIBLE_WINDOW_EXIT_CODE,
    )


class _FailingCleanupBoundary:
    def __init__(self, _command):
        pass

    def start(self):
        pass

    def close(self):
        raise RuntimeError("synthetic cleanup failure")


class _ActiveQueryFailureBoundary:
    def __init__(self, _command):
        self.desktop_name = "PrismQMLTest-synthetic"
        self.job_name = "PrismQMLTestJob-synthetic"
        self.process = SimpleNamespace(dwProcessId=321)

    def start(self):
        pass

    def active_process_count(self):
        raise OSError("synthetic active-process query failure")

    def close(self):
        pass


def _run_isolated(command: list[str]) -> int:
    return windows_test_process.run_isolated_windows_child(
        command,
        10,
        logging.getLogger(__name__),
        timeout_exit_code=TEST_TIMEOUT_EXIT_CODE,
        cleanup_failure_exit_code=TEST_CLEANUP_FAILURE_EXIT_CODE,
        visible_window_exit_code=TEST_VISIBLE_WINDOW_EXIT_CODE,
    )


def _logged_boundary_results(caplog) -> list[dict]:
    return [
        json.loads(message[len(BOUNDARY_RESULT_PREFIX) :])
        for message in caplog.messages
        if message.startswith(BOUNDARY_RESULT_PREFIX)
    ]


def test_cleanup_failure_is_structured(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(
        windows_test_process,
        "_WindowsTestBoundary",
        _FailingCleanupBoundary,
    )
    monkeypatch.setattr(
        windows_test_process,
        "_monitor_windows_child",
        lambda *_args, **_kwargs: 0,
    )

    result = _run_isolated([sys.executable, "-c", "raise SystemExit(0)"])

    assert result == TEST_CLEANUP_FAILURE_EXIT_CODE
    records = _logged_boundary_results(caplog)
    assert len(records) == 1
    assert records[0]["exit_code"] == TEST_CLEANUP_FAILURE_EXIT_CODE
    assert records[0]["cleanup_succeeded"] is False


def test_active_process_query_failure_is_structured(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(
        windows_test_process,
        "_WindowsTestBoundary",
        _ActiveQueryFailureBoundary,
    )
    monkeypatch.setattr(
        windows_test_process,
        "_monitor_windows_child",
        lambda *_args, **_kwargs: 7,
    )

    result = _run_isolated([sys.executable, "-c", "raise SystemExit(7)"])

    assert result == 7
    records = _logged_boundary_results(caplog)
    assert len(records) == 1
    assert records[0]["final_active_processes"] is None
    assert "synthetic active-process query failure" in records[0][
        "active_process_error"
    ]
