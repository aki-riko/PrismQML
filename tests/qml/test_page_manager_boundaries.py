# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Real PageManager failure-boundary regressions. 真实页面管理失败边界回归。"""

import logging
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtQuick import QQuickItem
from PySide6.QtWidgets import QApplication


class _RecordCapture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class _SelfDeletingItem(QQuickItem):
    def setHeight(self, height):
        super().setHeight(height)
        self.deleteLater()
        QCoreApplication.sendPostedEvents(self, QEvent.DeferredDelete)


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QApplication.processEvents()


def _assert_traceback_record(records, marker, error_type, source_line):
    from prismqml.python.core.logger import PlainFormatter

    matches = [
        record
        for record in records
        if marker in record.getMessage()
        and record.exc_info
        and record.exc_info[0] is error_type
    ]
    assert len(matches) == 1
    rendered = PlainFormatter(datefmt="%H:%M:%S").format(matches[0])
    assert "Traceback (most recent call last):" in rendered
    assert source_line in rendered


def _isolated_window_class(window_class, temp_dir, prefix):
    class IsolatedWindow(window_class):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-windows"

    return IsolatedWindow


def _new_window(window_class, window_type):
    window = window_class(window_type=window_type)
    window.setSplashEnabled(False)
    window.setLazyLoading(True)
    return window


def _exercise_page_factory_failure(temp_dir):
    from prismqml import Window, WindowType

    calls = 0

    def failing_page_getter():
        nonlocal calls
        calls += 1
        raise RuntimeError("page factory failed")

    window_class = _isolated_window_class(Window, temp_dir, "factory")
    window = _new_window(window_class, WindowType.BAR)
    window.addPage(None, "Home", "Home")
    window.addPage(failing_page_getter, "Error", "Error")
    try:
        window.show()
        pump(80)
        window.setCurrentIndex(1)
        pump(120)
        assert calls == 1
        assert 1 not in window._pages
        assert window._window.property("_pythonLoading") is False
    finally:
        _dispose_window(window)


def _exercise_size_signal_failure(temp_dir):
    from prismqml import Window, WindowType

    page = SimpleNamespace(_qml_item=_SelfDeletingItem(), _deferred_queue=[])
    window_class = _isolated_window_class(Window, temp_dir, "size")
    window = _new_window(window_class, WindowType.BAR)
    window.addPage(None, "Home", "Home")
    window.addPage(lambda: page, "Page", "Page")
    try:
        window.show()
        pump(80)
        window.setCurrentIndex(1)
        pump(240)
        assert window._pages[1] is page
        assert not shiboken6.isValid(page._qml_item)
        assert window._window.property("_pythonLoading") is False
    finally:
        _dispose_window(window)


def _exercise_deleted_window_invocations(temp_dir):
    from prismqml import Window, WindowType

    window_class = _isolated_window_class(Window, temp_dir, "deleted")
    window = _new_window(window_class, WindowType.BAR)
    try:
        window.show()
        pump(60)
        qml_window = window._window
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
        QApplication.processEvents()
        assert not shiboken6.isValid(qml_window)

        window._switch_to_index(0)
        window._start_async_page_load(0)
    finally:
        _dispose_window(window)


def _assert_boundary_records(records):
    expected = (
        ("页面创建失败", RuntimeError, 'raise RuntimeError("page factory failed")'),
        ("页面尺寸信号触发失败", RuntimeError, "page_item.widthChanged.emit()"),
        ("页面切换失败", RuntimeError, "in _switch_to_index"),
        ("页面 loading 启动方法不可用", RuntimeError, "in _start_loading_overlay"),
        ("页面 loading 结束方法不可用", RuntimeError, '"_finishPythonLoading"'),
    )
    for marker, error_type, source_line in expected:
        _assert_traceback_record(records, marker, error_type, source_line)


def main():
    from prismqml.python.core.logger import getLogger

    app = QApplication.instance() or QApplication(sys.argv)
    capture = _RecordCapture()
    logger = getLogger().logger
    logger.addHandler(capture)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            _exercise_page_factory_failure(temp_dir)
            _exercise_size_signal_failure(temp_dir)
            _exercise_deleted_window_invocations(temp_dir)
    finally:
        logger.removeHandler(capture)

    _assert_boundary_records(capture.records)
    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
