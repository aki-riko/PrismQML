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

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"


_SHUTDOWN_SCRIPT = r'''
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

import os
import sys
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

case_name = os.environ.get("PRISM_SHUTDOWN_PROBE_CASE", "full")
enable_window = os.environ.get("PRISM_SHUTDOWN_PROBE_WINDOW", "1") == "1"
enable_tray = os.environ.get("PRISM_SHUTDOWN_PROBE_TRAY", "1") == "1"
enable_dropdown = os.environ.get("PRISM_SHUTDOWN_PROBE_DROPDOWN", "1") == "1"
minimum_windows = int(os.environ.get("PRISM_SHUTDOWN_PROBE_MIN_WINDOWS", "0"))

app = App([])
window = None
if enable_window:
    window = app.create_window()
    window.setSplashEnabled(False)
    window.show()

tray = None
if enable_tray:
    tray = SystemTrayIcon(toolTip="shutdown-probe")
    tray.addAction("Exit", actionId="exit")
    tray._showQmlMenu()

button_component = None
button_window = None
split_button = None
dropdown = None
popup_loop = None
if enable_dropdown:
    if window is None:
        raise RuntimeError("dropdown shutdown probe requires a window")
    button_component = QQmlComponent(app.engine, parent=app.engine)
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
    if not QMetaObject.invokeMethod(
        dropdown, "openMenu", Qt.ConnectionType.DirectConnection
    ):
        raise RuntimeError("ButtonDropdown.openMenu invocation failed")
    popup_loop = QEventLoop()
    QTimer.singleShot(100, popup_loop.quit)
    popup_loop.exec()

shutdown_order = []
original_delete_windows = app_module._delete_remaining_qml_windows
original_engine_reset = EngineManager.reset
original_delete_qml_engine = app_module._delete_qml_engine
original_tray_release_engine = tray.release_engine if tray is not None else None

def traced_delete_windows():
    shutdown_order.append("windows")
    return original_delete_windows()

def traced_engine_reset():
    shutdown_order.append("bindings")
    return original_engine_reset()

def traced_delete_qml_engine(value):
    if value is app.engine:
        shutdown_order.append("engine")
    return original_delete_qml_engine(value)

def traced_tray_release_engine():
    shutdown_order.append("surfaces")
    return original_tray_release_engine()

app_module._delete_remaining_qml_windows = traced_delete_windows
EngineManager.reset = traced_engine_reset
app_module._delete_qml_engine = traced_delete_qml_engine
if tray is not None:
    tray.release_engine = traced_tray_release_engine

windows_before = len(QGuiApplication.topLevelWindows())
QTimer.singleShot(100, lambda: App.exit(7))
result = app.exec()
windows_after = len(QGuiApplication.topLevelWindows())
engine_released = app.engine is None and EngineManager._engine is None
window_references_released = (
    WindowCore.get_current_window() is None and not app.windows
)
tray_engine_released = tray is None or (
    tray._qml_menu is None and tray._component is None
)
component_released = button_component is None or not shiboken6.isValid(
    button_component
)
expected_shutdown_order = (
    ["surfaces", "windows", "bindings", "engine"]
    if enable_tray
    else ["windows", "bindings", "engine"]
)
app.shutdown()

print(f"APP_SHUTDOWN_CASE={case_name}", flush=True)
print(f"APP_SHUTDOWN_RESULT={result}", flush=True)
print(f"APP_SHUTDOWN_WINDOWS={windows_before}->{windows_after}", flush=True)
print(f"APP_SHUTDOWN_ENGINE_RELEASED={int(engine_released)}", flush=True)
print(f"APP_SHUTDOWN_ORDER={','.join(shutdown_order)}", flush=True)
print(
    f"APP_SHUTDOWN_WINDOW_REFERENCES_RELEASED={int(window_references_released)}",
    flush=True,
)
print(f"APP_SHUTDOWN_TRAY_ENGINE_RELEASED={int(tray_engine_released)}", flush=True)
print(f"APP_SHUTDOWN_COMPONENT_RELEASED={int(component_released)}", flush=True)

if (
    result != 7
    or windows_before < minimum_windows
    or windows_after != 0
    or not engine_released
    or not window_references_released
    or not tray_engine_released
    or not component_released
    or shutdown_order[:len(expected_shutdown_order)] != expected_shutdown_order
):
    raise SystemExit(4)

app_module._delete_remaining_qml_windows = original_delete_windows
EngineManager.reset = original_engine_reset
app_module._delete_qml_engine = original_delete_qml_engine
if tray is not None:
    tray.release_engine = original_tray_release_engine

qapp = app.qapp
App._reset()
if sys.platform == "win32":
    shiboken6.delete(qapp)
    if QApplication.instance() is not None:
        raise SystemExit(5)
    print("APP_SHUTDOWN_QAPP_TEARDOWN=explicit", flush=True)
else:
    qapp = None
    print("APP_SHUTDOWN_QAPP_TEARDOWN=process", flush=True)
print("APP_SHUTDOWN_OK", flush=True)
'''


@pytest.mark.parametrize(
    (
        "case_name",
        "enable_window",
        "enable_tray",
        "enable_dropdown",
        "minimum_windows",
    ),
    (
        ("engine", False, False, False, 0),
        ("window", True, False, False, 1),
        ("tray", False, True, False, 0),
        ("dropdown", True, False, True, 2),
        ("full", True, True, True, 2),
    ),
    ids=("engine", "window", "tray", "dropdown", "full"),
)
def test_exec_destroys_qml_windows_before_qapplication_teardown(
    case_name: str,
    enable_window: bool,
    enable_tray: bool,
    enable_dropdown: bool,
    minimum_windows: int,
) -> None:
    """Live QML windows must not outlive QApplication. 活 QML 窗口不得晚于应用析构。"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    environment.update(
        {
            "PRISM_SHUTDOWN_PROBE_CASE": case_name,
            "PRISM_SHUTDOWN_PROBE_WINDOW": str(int(enable_window)),
            "PRISM_SHUTDOWN_PROBE_TRAY": str(int(enable_tray)),
            "PRISM_SHUTDOWN_PROBE_DROPDOWN": str(int(enable_dropdown)),
            "PRISM_SHUTDOWN_PROBE_MIN_WINDOWS": str(minimum_windows),
        }
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
    assert f"APP_SHUTDOWN_CASE={case_name}" in output
    assert "APP_SHUTDOWN_RESULT=7" in output
    window_result = re.search(r"APP_SHUTDOWN_WINDOWS=(\d+)->0", output)
    assert window_result is not None, output
    assert int(window_result.group(1)) >= minimum_windows
    assert "APP_SHUTDOWN_ENGINE_RELEASED=1" in output
    expected_order = (
        "surfaces,windows,bindings,engine"
        if enable_tray
        else "windows,bindings,engine"
    )
    assert f"APP_SHUTDOWN_ORDER={expected_order}" in output
    assert "APP_SHUTDOWN_WINDOW_REFERENCES_RELEASED=1" in output
    assert "APP_SHUTDOWN_TRAY_ENGINE_RELEASED=1" in output
    assert "APP_SHUTDOWN_COMPONENT_RELEASED=1" in output
    expected_teardown = "explicit" if sys.platform == "win32" else "process"
    assert f"APP_SHUTDOWN_QAPP_TEARDOWN={expected_teardown}" in output
    assert "QObject::disconnect: Unexpected nullptr parameter" not in output
    assert "PopupWindowCore.qml" not in output
    assert "Cannot read property 'fast' of undefined" not in output
    assert "containsMouse is not defined" not in output
    assert "Unable to assign [undefined] to QColor" not in output
    assert "APP_SHUTDOWN_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in completed.stderr
