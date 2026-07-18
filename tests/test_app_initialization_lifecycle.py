# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""App initialization transaction regressions. App 初始化事务回归。"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"


_RETRY_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import os
import shiboken6
from PySide6.QtWidgets import QApplication
import prismqml.python.core as core
import prismqml.python.core.input_focus_filter as focus_filter
import prismqml.python.core.shadow as shadow
from prismqml import App
from prismqml.python.core.engine import EngineManager

original_register_types = core.register_types
os.environ["QML_XHR_ALLOW_FILE_READ"] = "0"
failures = [RuntimeError("runtime"), KeyboardInterrupt(), SystemExit(7)]

for failure in failures:
    def fail_register(_engine, failure=failure):
        raise failure

    core.register_types = fail_register
    caught = None
    try:
        App([])
    except BaseException as exc:
        caught = exc
    assert caught is failure
    assert App._instance is None
    assert QApplication.instance() is None
    assert EngineManager._engine is None
    assert focus_filter._filter is None
    assert shadow._dwm_sync_filter is None
    assert os.environ["QML_XHR_ALLOW_FILE_READ"] == "0"

core.register_types = original_register_types
app = App([])
assert App.instance() is app
assert QApplication.instance() is app.qapp
assert EngineManager.get_engine() is app.engine
assert focus_filter._filter is not None
App._reset()
assert App._instance is None
assert EngineManager._engine is None
assert focus_filter._filter is None
assert shadow._dwm_sync_filter is None
shiboken6.delete(app.engine)
shiboken6.delete(app.qapp)
print("APP_INIT_RETRY_OK")
'''


def test_app_initialization_failure_is_retryable_and_transactional():
    """Every failure class must roll back and allow a real retry. 各类失败均回滚并可重试。"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(TEST_PROCESS),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "90",
            "--",
            sys.executable,
            "-c",
            _RETRY_SCRIPT,
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "APP_INIT_RETRY_OK" in completed.stdout
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in completed.stderr
