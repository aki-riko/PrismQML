# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Regression probe for restoring a window after close/hide transparency."""

import os
import sys
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def force_transparent(win):
    win._window.setOpacity(0.0)
    win._window.setProperty("_animOpacity", 0.0)
    win._window.setProperty("_animScale", 0.95)
    pump(20)


def assert_opaque(win, label, failures, wait_ms=120):
    pump(wait_ms)
    if abs(float(win._window.opacity()) - 1.0) > 0.01:
        failures.append(f"{label} left window opacity at {win._window.opacity()}")
    if abs(float(win._window.property("_animOpacity")) - 1.0) > 0.01:
        failures.append(f"{label} left frame opacity at {win._window.property('_animOpacity')}")
    if abs(float(win._window.property("_animScale")) - 1.0) > 0.01:
        failures.append(f"{label} left frame scale at {win._window.property('_animScale')}")


def main():
    QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    failures = []

    win = Window(window_type=WindowType.BAR)
    win.setSplashEnabled(False)
    win.setWindowTitle("Visible state restore regression")
    win.addPage(None, "Home", "Home")
    win.show()
    pump(180)

    win.hide()
    pump(40)
    force_transparent(win)
    win.show()
    assert_opaque(win, "WindowCore.show", failures)

    win.hide()
    pump(40)
    force_transparent(win)
    win.showNormal()
    assert_opaque(win, "WindowCore.showNormal", failures)

    win._window.hide()
    pump(40)
    force_transparent(win)
    win._window.show()
    assert_opaque(win, "QQuickWindow.show", failures, wait_ms=450)

    print(f"\n{'=' * 60}")
    if failures:
        print("RESULT: FAIL - visible state restore regression failed")
        for failure in failures:
            print("  [FAIL]", failure)
        exit_code = 1
    else:
        print("RESULT: PASS - hidden transparent windows restore opaque")
        exit_code = 0
    print(f"{'=' * 60}")

    sys.stdout.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    main()
