# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Task runner ownership gates. 任务运行器所有权门禁。"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "prismqml/python/core/task_runner.py"
EXECUTION = ROOT / "prismqml/python/core/_task_execution.py"
CONFIG_MANAGER = ROOT / "prismqml/python/config/config_manager.py"
CORE_UTILS = ROOT / "prismqml/python/core/utils.py"
TASK_POOL = ROOT / "prismqml/python/core/_task_pool.py"
EXIT_GUARD = ROOT / "prismqml/python/core/_task_exit_guard.py"


def _function_node(path: Path, name: str) -> ast.FunctionDef:
    """Return the function or method node called ``name``. 取指定函数节点。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{path.name} no longer defines {name}()")


def _called_names(node: ast.AST) -> set:
    """Collect the callee names used inside one node. 收集节点内的被调用名。"""
    names = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Attribute):
            names.add(child.func.attr)
        elif isinstance(child.func, ast.Name):
            names.add(child.func.id)
    return names


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


def test_config_persistence_defers_launch_out_of_signal_delivery():
    """The next background write must not start inside a task signal delivery.

    下一次后台写盘不得在任务信号派发过程中启动。

    ``_finish_persistence`` is reached from ``TaskHandle.finished``. Launching the next
    snapshot inline constructs a fresh ``TaskHandle`` there, which connects its internal
    bridge signals while Qt is still delivering one: on a loaded runner that nested
    connect blocked inside Qt's signal lock for the rest of the shard budget, which
    surfaced as intermittent 300s / shard-level timeouts in CI. The continuation must
    therefore stay queued on the Qt thread instead of running inline.
    ``_finish_persistence`` 由 ``TaskHandle.finished`` 进入。就地启动下一次快照会在那里
    新建 ``TaskHandle`` 并连接其内部桥接信号, 而此刻 Qt 仍在派发信号: 在负载高的机器上这次
    嵌套 connect 会卡在 Qt 的信号锁里直到分片预算耗尽, 表现为 CI 上偶发的 300 秒 / 分片级
    超时。因此续跑必须排队到 Qt 线程, 不得就地执行。
    """
    finish = _function_node(CONFIG_MANAGER, "_finish_persistence")
    finish_calls = _called_names(finish)

    assert "_schedule_next_persistence" in finish_calls, (
        "_finish_persistence 必须把续跑交给 _schedule_next_persistence()，"
        "不得直接调用 _start_next_persistence()"
    )
    assert "_start_next_persistence" not in finish_calls, (
        "_finish_persistence 不得就地启动下一次落盘：那会在 TaskHandle.finished 的"
        "信号派发过程中重入 Qt 信号机制并新建 TaskHandle"
    )

    schedule = _function_node(CONFIG_MANAGER, "_schedule_next_persistence")
    schedule_calls = _called_names(schedule)
    assert "singleShot" in schedule_calls, (
        "_schedule_next_persistence 必须用 QTimer.singleShot 排队，"
        "否则续跑仍会在当前信号派发中就地执行"
    )
    assert "is_app_thread" in schedule_calls, (
        "_schedule_next_persistence 必须用 core.utils.is_app_thread() 判断事件循环可用性，"
        "不得自行比较 QThread.currentThread()"
    )


def test_core_owns_the_app_thread_predicate():
    """Only core/utils.py may compare the current thread to the app thread.

    仅 core/utils.py 可以直接比较当前线程与应用线程。
    """
    assert "def is_app_thread(" in CORE_UTILS.read_text(encoding="utf-8")

    for path in (CONFIG_MANAGER, RUNNER, TASK_POOL):
        source = path.read_text(encoding="utf-8")
        assert "QThread.currentThread()" not in source, (
            f"{path.name} 应使用 core.utils.is_app_thread()，"
            "不要直接比较 QThread.currentThread()"
        )


def test_task_threads_are_joined_before_interpreter_shutdown():
    """Task threads must be joined at exit, not destroyed mid-flight.

    任务线程必须在退出时被 join, 不得在运行中被销毁。

    A task's dedicated ``QThread`` dies with the process. When it is still running at
    that moment Qt aborts: the console prints
    ``QThread: Destroyed while thread '' is still running`` and Windows exits with
    ``0xC0000409``. Observed in CI as a shard that reported **every test passed** and
    still failed, because the abort happens after pytest finished. An ``atexit`` guard
    that drains ``shutdown_tasks`` keeps that teardown bounded and explicit.
    任务的独立 ``QThread`` 会随进程销毁。若此刻仍在运行, Qt 会中止: 控制台打印
    ``QThread: Destroyed while thread '' is still running``, Windows 以 ``0xC0000409``
    退出。CI 观察到的形态是分片报告**全部用例通过**却依然失败, 因为中止发生在 pytest 结束
    之后。用 ``atexit`` 钩子排空 ``shutdown_tasks`` 可让该收尾有界且显式。
    """
    runner_source = RUNNER.read_text(encoding="utf-8")
    guard_source = EXIT_GUARD.read_text(encoding="utf-8")
    assert "_exit_guard.ensure_installed(shutdown_tasks)" in runner_source
    assert "atexit.register(" in guard_source
    assert "join_task_threads_at_exit" in guard_source
    assert "shutdown(" in guard_source
