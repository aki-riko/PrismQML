# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""App shutdown ordering regressions. App 退出销毁顺序回归。"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"


_SHUTDOWN_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import shiboken6
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from prismqml import App, SystemTrayIcon
from prismqml.python.core.engine import EngineManager
from prismqml.python.window.window_core import WindowCore

app = App([])
window = app.create_window()
window.setSplashEnabled(False)
window.show()

tray = SystemTrayIcon(toolTip="shutdown-probe")
tray.addAction("Exit", actionId="exit")
tray._showQmlMenu()

windows_before = len(QGuiApplication.topLevelWindows())
QTimer.singleShot(100, lambda: App.exit(7))
result = app.exec()
windows_after = len(QGuiApplication.topLevelWindows())
engine_released = app.engine is None and EngineManager._engine is None
window_references_released = (
    WindowCore.get_current_window() is None and not app.windows
)
app.shutdown()

print(f"APP_SHUTDOWN_RESULT={result}", flush=True)
print(f"APP_SHUTDOWN_WINDOWS={windows_before}->{windows_after}", flush=True)
print(f"APP_SHUTDOWN_ENGINE_RELEASED={int(engine_released)}", flush=True)
print(
    f"APP_SHUTDOWN_WINDOW_REFERENCES_RELEASED={int(window_references_released)}",
    flush=True,
)

if (
    result != 7
    or windows_before < 2
    or windows_after != 0
    or not engine_released
    or not window_references_released
):
    raise SystemExit(4)

qapp = app.qapp
App._reset()
shiboken6.delete(qapp)
print("APP_SHUTDOWN_OK", flush=True)
'''


def test_exec_destroys_qml_windows_before_qapplication_teardown() -> None:
    """Live QML windows must not outlive QApplication. 活 QML 窗口不得晚于应用析构。"""
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
            _SHUTDOWN_SCRIPT,
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

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "APP_SHUTDOWN_RESULT=7" in output
    window_result = re.search(r"APP_SHUTDOWN_WINDOWS=(\d+)->0", output)
    assert window_result is not None, output
    assert int(window_result.group(1)) >= 2
    assert "APP_SHUTDOWN_ENGINE_RELEASED=1" in output
    assert "APP_SHUTDOWN_WINDOW_REFERENCES_RELEASED=1" in output
    assert "QObject::disconnect: Unexpected nullptr parameter" not in output
    assert "PopupWindowCore.qml" not in output
    assert "APP_SHUTDOWN_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in completed.stderr
