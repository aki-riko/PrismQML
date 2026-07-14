# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash 默认挂载回归 — 验证 Window 默认创建启动画面并可关闭。

背景: PrismQML 框架(NavigationWindowCore)早有 _splashInstance + 首屏就绪
自动 finish 的机制,但 Python 端 WindowCore 从不创建 splash 实例,导致默认
窗口从未显示启动画面。本测试锁定"默认即挂载"这一行为。

判据:
  - 默认 Window(BAR) show 后,QML 根对象 _splashInstance 非 null,且
    Python 侧 self._splash_instance 持有引用(防 GC)。
  - setSplashEnabled(False) 后,根对象 _splashInstance 为 null。

用法: <venv>/python scripts/test_process.py --qt-platform offscreen --timeout 180 -- <venv>/python tests/qml/test_splash_default_mount.py
退出码: 0=通过, 1=失败
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
    splash = getattr(window, "_splash_instance", None)
    component = getattr(window, "_splash_component", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("_splashInstance", None)
        qml_window.setProperty("visible", False)
    if splash is not None and shiboken6.isValid(splash):
        splash.setParentItem(None)
    _delete_qobject(splash)
    _delete_qobject(component)
    _delete_qobject(qml_window)
    window._splash_instance = None
    window._splash_component = None
    window._window = None
    QApplication.processEvents()


def _isolated_window_class(window_class, temp_dir):
    class IsolatedWindow(window_class):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / "windows"
        _GENERATED_SPLASH_QML_CACHE_DIR = Path(temp_dir) / "splash"

    return IsolatedWindow


def _exercise_default_mount(window_class, window_type):
    failures = []
    win = window_class(window_type=window_type)
    win.setWindowTitle("Splash 测试")
    win.addPage(None, "Home", "主页")
    try:
        win.show()
        pump(100)
        qml_mounted = win._window.property("_splashInstance") is not None
        py_mounted = win._splash_instance is not None
        if not qml_mounted:
            failures.append("默认窗口 _splashInstance 为 null(splash 未挂载)")
        if not py_mounted:
            failures.append("Python 侧 _splash_instance 未持有引用(GC 风险)")
        return qml_mounted, py_mounted, failures
    finally:
        _dispose_window(win)


def _exercise_disabled_mount(window_class, window_type):
    failures = []
    win = window_class(window_type=window_type)
    win.setWindowTitle("Splash 关闭测试")
    win.setSplashEnabled(False)
    win.addPage(None, "Home", "主页")
    try:
        win.show()
        pump(100)
        qml_mounted = win._window.property("_splashInstance") is not None
        py_mounted = win._splash_instance is not None
    finally:
        _dispose_window(win)
    if qml_mounted:
        failures.append("setSplashEnabled(False) 后 _splashInstance 仍非 null")
    if py_mounted:
        failures.append("setSplashEnabled(False) 后 Python 侧仍持有 splash 引用")
    return qml_mounted, py_mounted, failures


def _report_result(default_state, disabled_state, failures):
    qml_mounted, py_mounted = default_state
    qml_disabled, py_disabled = disabled_state
    print(f"\n{'=' * 60}")
    print(f"  默认挂载: qml={qml_mounted} py={py_mounted}")
    print(f"  显式关闭: qml={qml_disabled} py={py_disabled}")
    if failures:
        print("RESULT: FAIL - splash 默认挂载测试失败")
        for failure in failures:
            print("  [FAIL]", failure)
        result = 1
    else:
        print("RESULT: PASS - splash 默认挂载/可关闭均正确")
        result = 0
    print(f"{'=' * 60}")
    return result


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    with tempfile.TemporaryDirectory() as temp_dir:
        window_class = _isolated_window_class(Window, temp_dir)
        default = _exercise_default_mount(window_class, WindowType.BAR)
        disabled = _exercise_disabled_mount(window_class, WindowType.BAR)
    failures = [*default[2], *disabled[2]]
    result = _report_result(default[:2], disabled[:2], failures)
    assert app is QApplication.instance()
    return result


if __name__ == "__main__":
    result = main()
    sys.stdout.flush()
    os._exit(result)
