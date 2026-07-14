# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Real generated-window file fallback regression. 真实生成窗口文件回退回归。"""

import logging
import sys
import tempfile
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication


class _RecordCapture(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


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


def _exercise_post_create_profile_failure(temp_dir):
    from PySide6.QtQml import QQmlApplicationEngine

    from prismqml.python.window._window_builder import WindowBuilderMixin

    class ProfileFailureBuilder(WindowBuilderMixin):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / "profile-cache"

    builder = ProfileFailureBuilder()
    builder._engine = QQmlApplicationEngine()

    def fail_after_create(label):
        if label == "component.create(file)":
            raise RuntimeError("profile failed after component creation")

    loaded_window = None
    try:
        loaded_window = builder._load_generated_window_boundary(
            'import QtQuick\nItem { objectName: "profileFailureRoot" }',
            "Item",
            fail_after_create,
            False,
        )
        assert loaded_window is not None
        assert loaded_window.objectName() == "profileFailureRoot"
    finally:
        if loaded_window is not None:
            loaded_window.deleteLater()
            QCoreApplication.sendPostedEvents(loaded_window, QEvent.DeferredDelete)
        QApplication.processEvents()


def _exercise_file_fallback(temp_dir):
    from prismqml import Window, WindowType

    blocked_cache = Path(temp_dir) / "blocked-cache"
    blocked_cache.write_text("not a directory", encoding="utf-8")

    class FileFallbackWindow(Window):
        pass

    FileFallbackWindow._GENERATED_QML_CACHE_DIR = blocked_cache
    win = FileFallbackWindow(window_type=WindowType.BAR)
    win.setSplashEnabled(False)
    win.addPage(None, "Home", "Home")
    try:
        win.show()
        pump(120)
        assert win._window is not None
        assert win.isVisible()
        assert "WindowsBar" in win._window.metaObject().className()
    finally:
        qml_window = getattr(win, "_window", None)
        if qml_window is not None:
            qml_window.setProperty("visible", False)
            qml_window.deleteLater()
            QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
        win._window = None
        QApplication.processEvents()


def _exercise_missing_root_failure(temp_dir):
    from PySide6.QtQml import QQmlApplicationEngine

    from prismqml.python.window._window_builder import WindowBuilderMixin
    from prismqml.python.window._window_root_setup import load_window_root

    class MissingRootBuilder(WindowBuilderMixin):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / "missing-root-cache"

    builder = MissingRootBuilder()
    builder._engine = QQmlApplicationEngine()
    source = "import QtQuick\nItem { missingProperty: true }"
    try:
        try:
            load_window_root(builder, source, "Item", lambda _label: None, False)
        except RuntimeError as exc:
            assert str(exc) == "Failed to create window"
        else:
            raise AssertionError("invalid file and inline QML must not create a root")
        assert builder._engine.rootObjects() == []
    finally:
        builder._engine.deleteLater()
        QCoreApplication.sendPostedEvents(builder._engine, QEvent.DeferredDelete)


def main():
    from prismqml.python.core.logger import getLogger

    app = QApplication.instance() or QApplication(sys.argv)
    capture = _RecordCapture()
    logger = getLogger().logger
    logger.addHandler(capture)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            _exercise_post_create_profile_failure(temp_dir)
            _exercise_missing_root_failure(temp_dir)
            _exercise_file_fallback(temp_dir)
    finally:
        logger.removeHandler(capture)
    _assert_traceback_record(
        capture.records,
        "[WindowBuilder] 文件化窗口 QML 创建后诊断失败，保留已创建窗口",
        RuntimeError,
        'raise RuntimeError("profile failed after component creation")',
    )
    _assert_traceback_record(
        capture.records,
        "[WindowBuilder] 文件化加载窗口 QML 失败，回退到 loadData",
        FileExistsError,
        "cache_dir.mkdir(parents=True, exist_ok=True)",
    )
    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
