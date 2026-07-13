# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Regression probe for cancellable PrismQML window close requests."""

import os
import logging
import sys
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
)
from PySide6.QtWidgets import QApplication


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class _RecordCapture(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _prepare_window(window):
    window.setSplashEnabled(False)
    window.addPage(None, "Home", "Home")
    window.show()
    pump(120)
    return window


def _dispose_window(window):
    qml_window = window._window
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QApplication.processEvents()


def _assert_traceback_record(records, marker, error_type, source_text):
    from prismqml.python.core.logger import PlainFormatter

    matches = [record for record in records if marker in record.getMessage()]
    assert len(matches) == 1
    assert matches[0].exc_info is not None
    assert matches[0].exc_info[0] is error_type
    rendered = PlainFormatter(datefmt="%H:%M:%S").format(matches[0])
    assert "Traceback (most recent call last):" in rendered
    assert source_text in rendered


def _exercise_close_event_failure(capture):
    from prismqml import Window, WindowType

    class RaisingWindow(Window):
        def closeEvent(self, _event):
            raise RuntimeError("close hook exploded")

    window = _prepare_window(RaisingWindow(window_type=WindowType.BAR))
    try:
        assert QMetaObject.invokeMethod(window._window, "requestClose")
        pump(80)
        assert window._window.property("closeRequestAccepted") is False
        assert window.isVisible()
        _assert_traceback_record(
            capture.records,
            "WindowCore.closeEvent failed",
            RuntimeError,
            "raise RuntimeError(\"close hook exploded\")",
        )
    finally:
        _dispose_window(window)


def _exercise_writeback_failure(capture):
    from prismqml import Window, WindowType

    window = _prepare_window(Window(window_type=WindowType.BAR))
    qml_window = window._window
    qml_window.deleteLater()
    QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    QApplication.processEvents()
    assert not shiboken6.isValid(qml_window)

    window._on_close_requested()

    _assert_traceback_record(
        capture.records,
        "WindowCore.closeRequestAccepted write failed",
        RuntimeError,
        "self._window.setProperty",
    )
    window._window = None


def _exercise_process_control(error_type):
    from prismqml import Window, WindowType

    class RaisingWindow(Window):
        def closeEvent(self, _event):
            raise error_type("stop")

    window = _prepare_window(RaisingWindow(window_type=WindowType.BAR))
    try:
        try:
            window._on_close_requested()
        except error_type as exc:
            assert str(exc) == "stop"
        else:
            raise AssertionError(f"{error_type.__name__} was swallowed")
    finally:
        _dispose_window(window)


def run_error_boundary_regressions():
    from prismqml.python.core.logger import getLogger

    app = QApplication.instance() or QApplication(sys.argv)
    capture = _RecordCapture()
    logger = getLogger().logger
    logger.addHandler(capture)
    try:
        _exercise_close_event_failure(capture)
        _exercise_writeback_failure(capture)
        _exercise_process_control(KeyboardInterrupt)
        _exercise_process_control(SystemExit)
    finally:
        logger.removeHandler(capture)
    assert app is QApplication.instance()


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

    if not QMetaObject.invokeMethod(win._window, "animatedClose"):
        failures.append("animatedClose method was not invokable")
    pump(450)
    if win.close_events != 3:
        failures.append(f"animatedClose emitted {win.close_events} close events, expected 3")
    if not win.isVisible():
        failures.append("ignored animatedClose hid or closed the window")
    if win._window.property("_closeInProgress") is not False:
        failures.append("ignored animatedClose left _closeInProgress=true")
    if abs(float(win._window.opacity()) - 1.0) > 0.01:
        failures.append(f"ignored animatedClose left window opacity at {win._window.opacity()}")

    class TrayRejectingWindow(Window):
        def __init__(self):
            super().__init__(window_type=WindowType.BAR)
            self.close_events = 0

        def closeEvent(self, event):
            self.close_events += 1
            self.hide()
            event.ignore()

    tray_win = TrayRejectingWindow()
    tray_win.setSplashEnabled(False)
    tray_win.setWindowTitle("Close-to-tray regression")
    tray_win.addPage(None, "Home", "Home")
    tray_win.show()
    pump(150)

    if not QMetaObject.invokeMethod(tray_win._window, "requestClose"):
        failures.append("tray requestClose method was not invokable")
    pump(120)

    if tray_win.close_events != 1:
        failures.append(f"tray requestClose emitted {tray_win.close_events} close events, expected 1")
    if tray_win.isVisible():
        failures.append("close-to-tray requestClose restored a hidden window")
    if tray_win._window.property("_closeInProgress") is not False:
        failures.append("close-to-tray requestClose left _closeInProgress=true")
    if tray_win._window.property("closeRequestAccepted") is not False:
        failures.append("close-to-tray requestClose did not write closeRequestAccepted=false")

    tray_win.show()
    pump(180)
    result = tray_win.close()
    pump(120)
    if result is not False:
        failures.append(f"close-to-tray native close returned {result!r}, expected False")
    if tray_win.close_events != 2:
        failures.append(f"close-to-tray native close emitted {tray_win.close_events} close events, expected 2")
    if tray_win.isVisible():
        failures.append("close-to-tray native close restored a hidden window")
    if tray_win._window.property("_closeInProgress") is not False:
        failures.append("close-to-tray native close left _closeInProgress=true")

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
    run_error_boundary_regressions()
    main()
