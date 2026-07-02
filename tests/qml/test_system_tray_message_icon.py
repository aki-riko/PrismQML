# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""Regression probe for tolerant system tray message icons."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon


def main():
    QApplication.instance() or QApplication(sys.argv)

    from prismqml.python.window.system_tray import SystemTrayIcon
    from prismqml.python.window.tray_types import MessageIcon

    failures = []

    class FakeTray:
        def __init__(self):
            self.calls = []

        def showMessage(self, title, message, icon, msecs):
            self.calls.append((title, message, icon, msecs))

    tray = SystemTrayIcon()
    fake_tray = FakeTray()
    tray._tray = fake_tray

    cases = [
        (None, QSystemTrayIcon.MessageIcon.Information),
        (QIcon(), QSystemTrayIcon.MessageIcon.Information),
        (MessageIcon.Warning, QSystemTrayIcon.MessageIcon.Warning),
        (QSystemTrayIcon.MessageIcon.Critical, QSystemTrayIcon.MessageIcon.Critical),
        (QSystemTrayIcon.MessageIcon.NoIcon.value, QSystemTrayIcon.MessageIcon.NoIcon),
    ]

    for icon, expected in cases:
        fake_tray.calls.clear()
        tray.showMessage("title", "message", icon, 10)
        actual = fake_tray.calls[0][2]
        if actual != expected:
            failures.append(f"{icon!r} coerced to {actual!r}, expected {expected!r}")

    print(f"\n{'=' * 60}")
    if failures:
        print("RESULT: FAIL - system tray message icon coercion failed")
        for failure in failures:
            print("  [FAIL]", failure)
        exit_code = 1
    else:
        print("RESULT: PASS - system tray message icons are tolerant")
        exit_code = 0
    print(f"{'=' * 60}")

    sys.stdout.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    main()
