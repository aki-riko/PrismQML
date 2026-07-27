# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash 默认挂载回归 — 验证窗口基类统一创建启动画面并可关闭。

判据：默认 Python Window 创建的 QML 根对象持有 Splash；显式关闭后不创建；
Python 宿主不再保存或挂载 Splash 实例。
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ["QML_DISABLE_DISK_CACHE"] = "1"
os.environ.pop("QML_FORCE_DISK_CACHE", None)

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _delete_qobject(obj):
    if obj is None or not shiboken6.isValid(obj):
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(obj, QEvent.DeferredDelete)
    assert not shiboken6.isValid(obj)


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
    _delete_qobject(qml_window)
    window._window = None
    QApplication.processEvents()


def _isolated_window_class(window_class, temp_dir):
    class IsolatedWindow(window_class):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / "windows"

    return IsolatedWindow


def _exercise_mount(window_class, window_type, enabled):
    win = window_class(window_type=window_type)
    win.setWindowTitle("Splash 测试")
    win.setSplashEnabled(enabled)
    win.addPage(None, "Home", "主页")
    try:
        win.show()
        pump(100)
        mounted = win._window.property("_splashInstance") is not None
        host_owns_instance = hasattr(win, "_splash_instance")
        return mounted, host_owns_instance
    finally:
        _dispose_window(win)


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    with tempfile.TemporaryDirectory() as temp_dir:
        window_class = _isolated_window_class(Window, temp_dir)
        default = _exercise_mount(window_class, WindowType.BAR, True)
        disabled = _exercise_mount(window_class, WindowType.BAR, False)

    failures = []
    if default != (True, False):
        failures.append(f"默认窗口状态错误: mounted={default[0]} hostOwns={default[1]}")
    if disabled != (False, False):
        failures.append(f"关闭后状态错误: mounted={disabled[0]} hostOwns={disabled[1]}")

    print(f"默认挂载={default} 显式关闭={disabled}")
    if failures:
        for failure in failures:
            print("[FAIL]", failure)
        result = 1
    else:
        print("RESULT: PASS - Splash 由 QML 窗口基类统一持有")
        result = 0
    assert app is QApplication.instance()
    return result


if __name__ == "__main__":
    result = main()
    sys.stdout.flush()
    os._exit(result)
