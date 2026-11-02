# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Bounded teardown of task threads at interpreter shutdown. 解释器退出时的任务线程收尾。"""

import atexit
from typing import Any, Callable, Optional

from PySide6.QtCore import QCoreApplication, QThread

from .logger import exception, warning

# Long enough to drain a normal disk write, short enough to never hang a shutting-down
# process.
# 足以排空一次正常写盘, 又不至于让退出流程挂住。
EXIT_GUARD_TIMEOUT_MS = 5000

_SHUTDOWN: Optional[Callable[[Optional[int]], Any]] = None
_INSTALLED = False


def join_task_threads_at_exit() -> None:
    """Join running task threads before the interpreter tears down Qt.

    在解释器拆掉 Qt 之前 join 正在运行的任务线程。

    A task's dedicated ``QThread`` is destroyed together with the process. When it is
    still running at that moment Qt aborts the process: the console prints
    ``QThread: Destroyed while thread '' is still running`` and Windows terminates with
    ``0xC0000409`` (fail-fast). A shard can therefore report every test as passed and
    still fail, because the abort happens after ``pytest`` finished -- the
    "all green but exit code != 0" signature seen in CI.
    任务的独立 ``QThread`` 会随进程一起销毁。若此刻仍在运行, Qt 会中止进程: 控制台打印
    ``QThread: Destroyed while thread '' is still running``, Windows 以 ``0xC0000409``
    (fail-fast) 终止。于是分片可能报告全部用例通过却依然失败, 因为中止发生在 ``pytest``
    结束之后——正是 CI 里"全绿但退出码非 0"的特征。
    """
    shutdown = _SHUTDOWN
    if shutdown is None or not _on_app_thread_with_app():
        return
    try:
        report = shutdown(EXIT_GUARD_TIMEOUT_MS)
    except Exception as exc:
        exception(f"退出时等待任务线程失败 Task thread join at exit failed: {exc}")
        return
    if report.pending:
        warning(
            "退出时仍有未结束的任务线程 Tasks still running at exit: "
            f"{len(report.pending)}"
        )


def _on_app_thread_with_app() -> bool:
    """Report whether a join can run here at all. 判断此处是否具备 join 条件。"""
    app = QCoreApplication.instance()
    if app is None:
        return False
    return QThread.currentThread() is app.thread()


def ensure_installed(shutdown_tasks: Callable[[Optional[int]], Any]) -> None:
    """Install the shutdown guard once, on first task creation. 首次创建任务时安装一次。

    Installed lazily from the task path instead of at import time: the guard only
    matters once a task thread exists, and doing it here keeps ``task_runner`` free of
    extra module-level wiring.
    由任务路径惰性安装, 而不是在导入时安装: 只有存在任务线程时该守卫才有意义, 放在这里也让
    ``task_runner`` 不必增加额外的模块级装配。
    """
    global _SHUTDOWN, _INSTALLED
    if _INSTALLED:
        return
    _SHUTDOWN = shutdown_tasks
    _INSTALLED = True
    atexit.register(join_task_threads_at_exit)
