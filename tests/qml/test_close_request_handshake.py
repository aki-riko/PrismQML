# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""Regression probe for cancellable PrismQML window close requests."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer
from PySide6.QtWidgets import QApplication


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    failures = []

    class RejectingWindow(Window):
        def __init__(self):
            super().__init__(window_type=WindowType.BAR)
            self.close_events = 0

        def closeEvent(self, event):
            self.close_events += 1
            event.ignore()

    win = RejectingWindow()
    win.setSplashEnabled(False)
    win.setWindowTitle("Close request regression")
    win.addPage(None, "Home", "Home")
    win.show()
    pump(150)

    if not QMetaObject.invokeMethod(win._window, "requestClose"):
        failures.append("requestClose method was not invokable")
    pump(80)

    if win.close_events != 1:
        failures.append(f"requestClose emitted {win.close_events} close events, expected 1")
    if not win.isVisible():
        failures.append("ignored requestClose hid or closed the window")
    if win._window.property("closeRequestAccepted") is not False:
        failures.append("ignored request did not write closeRequestAccepted=false")
    if abs(float(win._window.opacity()) - 1.0) > 0.01:
        failures.append(f"ignored request left window opacity at {win._window.opacity()}")
    if abs(float(win._window.property("_animOpacity")) - 1.0) > 0.01:
        failures.append(f"ignored request left frame opacity at {win._window.property('_animOpacity')}")

    result = win.close()
    pump(80)
    if result is not False:
        failures.append(f"Window.close returned {result!r} for an ignored native close")
    if win.close_events != 2:
        failures.append(f"native close emitted {win.close_events} close events, expected 2")
    if not win.isVisible():
        failures.append("ignored native close hid or closed the window")

    print(f"\n{'=' * 60}")
    if failures:
        print("RESULT: FAIL - close request handshake regression failed")
        for failure in failures:
            print("  [FAIL]", failure)
        exit_code = 1
    else:
        print("RESULT: PASS - close request can be cancelled without transparency loss")
        exit_code = 0
    print(f"{'=' * 60}")

    sys.stdout.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    main()
