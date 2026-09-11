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

    # Hide-only close: the collapse animation plays in the overlay window, then the
    # window hides instead of being destroyed, and close state fully rewinds so the
    # window can be shown and closed again.
    # 隐藏式关闭: 收缩动画播完后隐藏而非销毁, 关闭状态全部复位, 窗口可再次显示与关闭。
    class HideToTrayWindow(Window):
        def __init__(self):
            super().__init__(window_type=WindowType.BAR)
            self.close_events = 0

        def closeEvent(self, event):
            self.close_events += 1
            event.requestHideOnClose()

    hide_win = HideToTrayWindow()
    hide_win.setSplashEnabled(False)
    hide_win.setWindowTitle("Hide-only close regression")
    hide_win.addPage(None, "Home", "Home")
    hide_win.show()
    pump(150)

    if not QMetaObject.invokeMethod(hide_win._window, "requestClose"):
        failures.append("hide-only requestClose method was not invokable")
    # Cover the 420ms circle collapse plus frame-end handshake with margin.
    pump(1200)

    if hide_win.close_events != 1:
        failures.append(f"hide-only requestClose emitted {hide_win.close_events} close events, expected 1")
    if hide_win.isVisible():
        failures.append("hide-only requestClose left the window visible")
    if hide_win._window.property("closeRequestAccepted") is not True:
        failures.append("hide-only request did not write closeRequestAccepted=true")
    if hide_win._window.property("closeRequestHideOnly") is not True:
        failures.append("hide-only request did not write closeRequestHideOnly=true")
    if hide_win._window.property("_closeInProgress") is not False:
        failures.append("hide-only close left _closeInProgress=true")
    if abs(float(hide_win._window.opacity()) - 1.0) > 0.01:
        failures.append(f"hide-only close left window opacity at {hide_win._window.opacity()}")

    # Re-show must present a fully visible window with its content layer back on.
    hide_win.show()
    pump(180)
    if not hide_win.isVisible():
        failures.append("re-show after hide-only close failed to show the window")
    if abs(float(hide_win._window.opacity()) - 1.0) > 0.01:
        failures.append(f"re-show after hide-only close left opacity at {hide_win._window.opacity()}")
    frame_layer = None
    for child in hide_win._window.contentItem().childItems():
        if "WindowsCoreFrame" in child.metaObject().className():
            frame_layer = child
            break
    if frame_layer is None:
        failures.append("WindowsCoreFrame content layer was not found")
    elif not frame_layer.isVisible():
        failures.append("hide-only close left the content layer hidden after re-show")

    # A second request must run the full handshake again.
    if not QMetaObject.invokeMethod(hide_win._window, "requestClose"):
        failures.append("second hide-only requestClose was not invokable")
    pump(1200)
    if hide_win.close_events != 2:
        failures.append(f"second hide-only requestClose emitted {hide_win.close_events} close events, expected 2")
    if hide_win.isVisible():
        failures.append("second hide-only requestClose left the window visible")
    if hide_win._window.property("_closeInProgress") is not False:
        failures.append("second hide-only close left _closeInProgress=true")

    # The landing mode is latched when the accepted close starts: writing
    # closeRequestHideOnly during the collapse animation must not hijack an
    # already-accepted hide-only close into the destroy path.
    # 收尾方式在已接受关闭发起的那一刻闩锁: 收缩动画期间写 closeRequestHideOnly
    # 不得把已被接受的隐藏式关闭劫持进销毁路径。
    hide_win.show()
    pump(180)
    if not QMetaObject.invokeMethod(hide_win._window, "requestClose"):
        failures.append("latched hide-only requestClose was not invokable")
    if hide_win._window.property("_closeInProgress") is not True:
        failures.append("latched hide-only requestClose did not start synchronously")
    if hide_win._window.property("_closeHideOnlyLatched") is not True:
        failures.append("hide-only close was not latched when the accepted close started")
    hide_win._window.setProperty("closeRequestHideOnly", False)
    pump(1200)
    if hide_win.close_events != 3:
        failures.append(f"latched hide-only requestClose emitted {hide_win.close_events} close events, expected 3")
    if hide_win.isVisible():
        failures.append("latched hide-only requestClose left the window visible")
    if hide_win._window.property("_closeInProgress") is not False:
        failures.append("mid-animation closeRequestHideOnly write hijacked the accepted close into the destroy path")

    # A native close delivered through onClosing must land exactly the same way.
    # 经 onClosing 送达的原生关闭也必须以同样方式收尾。
    hide_win.show()
    pump(180)
    result = hide_win.close()
    pump(1200)
    if result is not False:
        failures.append(f"hide-only native close returned {result!r}, expected False")
    if hide_win.close_events != 4:
        failures.append(f"hide-only native close emitted {hide_win.close_events} close events, expected 4")
    if hide_win.isVisible():
        failures.append("hide-only native close left the window visible")
    if hide_win._window.property("closeRequestHideOnly") is not True:
        failures.append("hide-only native close did not write closeRequestHideOnly=true")
    if hide_win._window.property("_closeInProgress") is not False:
        failures.append("hide-only native close left _closeInProgress=true")
    hide_win.show()
    pump(180)
    if not hide_win.isVisible():
        failures.append("re-show after hide-only native close failed to show the window")
    frame_layer = None
    for child in hide_win._window.contentItem().childItems():
        if "WindowsCoreFrame" in child.metaObject().className():
            frame_layer = child
            break
    if frame_layer is not None and not frame_layer.isVisible():
        failures.append("hide-only native close left the content layer hidden after re-show")

    # A real close only hides the window; the QML object and the engine stay alive, so the
    # close state must be rewound after it. Otherwise _closeInProgress latches forever and
    # every later close is swallowed by the "already closing" branch.
    # 真实关闭只是把窗口藏起来, QML 对象与引擎都还活着, 因此关闭之后必须复位关闭状态。
    # 否则 _closeInProgress 永久闩住, 之后每次关闭都会被「关闭中」分支吞掉。
    #
    # 收尾的帧尾握手要求窗口仍在提交帧, 所以这里不能在 closeEvent 里提前 hide() ——
    # 那种宿主在收尾前就下屏, 帧尾永不到达 (既有行为, 不在本回归范围内)。
    class RealCloseWindow(Window):
        def __init__(self):
            super().__init__(window_type=WindowType.BAR)
            self.close_events = 0

        def closeEvent(self, event):
            self.close_events += 1

    real_win = RealCloseWindow()
    real_win.setSplashEnabled(False)
    real_win.setWindowTitle("Real close reset regression")
    real_win.addPage(None, "Home", "Home")
    real_win.show()
    pump(150)

    if not QMetaObject.invokeMethod(real_win._window, "requestClose"):
        failures.append("real close requestClose was not invokable")
    pump(1200)

    if real_win.close_events != 1:
        failures.append(f"real close emitted {real_win.close_events} close events, expected 1")
    if real_win.isVisible():
        failures.append("real close left the window visible")
    if real_win._window.property("_closeInProgress") is not False:
        failures.append("real close left _closeInProgress=true")
    if real_win._window.property("_closeCompletionPending") is not False:
        failures.append("real close left _closeCompletionPending=true")
    if real_win._window.property("_closeHideOnlyLatched") is not False:
        failures.append("real close left _closeHideOnlyLatched=true")

    # The window can be shown again, and the next close must run the handshake again
    # instead of being swallowed by a still-latched close gate.
    # 窗口可以再次显示, 且下一次关闭必须完整重跑握手, 而不是被仍闩住的关闭门吞掉。
    real_win.show()
    pump(180)
    if not real_win.isVisible():
        failures.append("re-show after real close failed to show the window")
    if not QMetaObject.invokeMethod(real_win._window, "requestClose"):
        failures.append("second real close requestClose was not invokable")
    pump(1200)
    if real_win.close_events != 2:
        failures.append(f"real close gate stayed latched: {real_win.close_events} close events, expected 2")
    if real_win.isVisible():
        failures.append("second real close left the window visible")
    if real_win._window.property("_closeInProgress") is not False:
        failures.append("second real close left _closeInProgress=true")

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
