# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Task runner ownership gates. 任务运行器所有权门禁。"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "prismqml/python/core/task_runner.py"
EXECUTION = ROOT / "prismqml/python/core/_task_execution.py"


def test_task_runner_keeps_public_orchestration_thin():
    runner = RUNNER.read_text(encoding="utf-8")
    execution = EXECUTION.read_text(encoding="utf-8")

    assert len(runner.splitlines()) < 400
    assert len(execution.splitlines()) < 220
    assert "from ._task_execution import (" in runner
    assert "class TaskHandle(QObject):" in runner
    assert "def run_in_pool(" in runner
    assert "def run_in_thread(" in runner
    assert "def shutdown_tasks(" in runner
    assert "class _TaskControl" not in runner
    assert "class TaskContext" not in runner
    assert "class _TaskExecution" not in runner
    assert "class _TaskEvents" not in runner
    assert "class _TaskControl" in execution
    assert "class TaskContext" in execution
    assert "class _TaskExecution" in execution
    assert "class _TaskEvents" in execution
