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

import gc
import shiboken6
from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtWidgets import QApplication
from prismqml import App, SystemTrayIcon
from prismqml.python.core.engine import EngineManager
from prismqml.python.window import app as app_module
from prismqml.python.window.window_core import WindowCore

app = App([])
window = app.create_window()
window.setSplashEnabled(False)
window.show()

tray = SystemTrayIcon(toolTip="shutdown-probe")
tray.addAction("Exit", actionId="exit")
tray._showQmlMenu()

button_component = QQmlComponent(app.engine)
button_component.setData(
    b"""import QtQuick
import QtQuick.Window
import PrismQML
Window {
    width: 360
    height: 240
    visible: true
    Button {
        id: splitButton
        objectName: "shutdownSplitButton"
        x: 20
        y: 20
        width: 240
        height: 40
        feature: Enums.button.feature_split
        text: "Split"
        menuItems: ["Alpha", "Beta"]
    }
}
""",
    QUrl("file:///shutdown-button.qml"),
)
button_window = button_component.create()
if button_window is None:
    raise RuntimeError([error.toString() for error in button_component.errors()])
split_button = button_window.findChild(QQuickItem, "shutdownSplitButton")
dropdown = next(
    child
    for child in split_button.findChildren(QQuickItem)
    if child.metaObject().indexOfMethod("openMenu()") >= 0
)
if not QMetaObject.invokeMethod(dropdown, "openMenu", Qt.ConnectionType.DirectConnection):
    raise RuntimeError("ButtonDropdown.openMenu invocation failed")
popup_loop = QEventLoop()
QTimer.singleShot(100, popup_loop.quit)
popup_loop.exec()

shutdown_order = []
original_delete_windows = app_module._delete_remaining_qml_windows
original_engine_reset = EngineManager.reset
original_delete_qt_object = app_module._delete_qt_object

def traced_delete_windows():
    shutdown_order.append("windows")
    return original_delete_windows()

def traced_engine_reset():
    shutdown_order.append("bindings")
    return original_engine_reset()

def traced_delete_qt_object(value):
    if value is app.engine:
        shutdown_order.append("engine")
    return original_delete_qt_object(value)

app_module._delete_remaining_qml_windows = traced_delete_windows
EngineManager.reset = traced_engine_reset
app_module._delete_qt_object = traced_delete_qt_object

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
print(f"APP_SHUTDOWN_ORDER={','.join(shutdown_order)}", flush=True)
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
    or shutdown_order[:3] != ["windows", "bindings", "engine"]
):
    raise SystemExit(4)

app_module._delete_remaining_qml_windows = original_delete_windows
EngineManager.reset = original_engine_reset
app_module._delete_qt_object = original_delete_qt_object

tray.hide()
if shiboken6.isValid(tray._tray):
    shiboken6.delete(tray._tray)
tray._tray = None
tray._qml_menu = None
tray._component = None
if shiboken6.isValid(tray):
    shiboken6.delete(tray)

for value in (popup_loop, button_component):
    if shiboken6.isValid(value):
        shiboken6.delete(value)

qapp = app.qapp
app._app = None
App._reset()
window = None
tray = None
button_component = None
button_window = None
split_button = None
dropdown = None
popup_loop = None
app = None
gc.collect()
print("APP_SHUTDOWN_REFERENCES_CLEARED=1", flush=True)
qapp.shutdown()
qapp_released = QApplication.instance() is None
print(f"APP_SHUTDOWN_QAPP_RELEASED={int(qapp_released)}", flush=True)
if not qapp_released:
    raise SystemExit(5)
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
    assert "APP_SHUTDOWN_ORDER=windows,bindings,engine" in output
    assert "APP_SHUTDOWN_WINDOW_REFERENCES_RELEASED=1" in output
    assert "APP_SHUTDOWN_REFERENCES_CLEARED=1" in output
    assert "APP_SHUTDOWN_QAPP_RELEASED=1" in output
    assert "QObject::disconnect: Unexpected nullptr parameter" not in output
    assert "PopupWindowCore.qml" not in output
    assert "Cannot read property 'fast' of undefined" not in output
    assert "containsMouse is not defined" not in output
    assert "Unable to assign [undefined] to QColor" not in output
    assert "APP_SHUTDOWN_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in completed.stderr
