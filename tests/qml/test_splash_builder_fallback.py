# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Real Splash fallback-boundary regressions. 真实启动画面回退边界回归。"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ["QML_DISABLE_DISK_CACHE"] = "1"
os.environ.pop("QML_FORCE_DISK_CACHE", None)

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
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


def _new_window(window_type, window_class):
    window = window_class(window_type=window_type)
    window.addPage(None, "Home", "Home")
    return window


def _isolated_window_class(window_class, temp_dir, prefix):
    class IsolatedWindow(window_class):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-windows"
        _GENERATED_SPLASH_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-splash"

    return IsolatedWindow


def _exercise_post_component_profile_failure(temp_dir):
    from prismqml import Window, WindowType
    from prismqml.python.window import _splash_builder

    original_info, profile_messages = _splash_builder.info, []
    raised = False

    def fail_after_component(message):
        nonlocal raised
        profile_messages.append(message)
        if not raised and "PrismQML._create_splash QQmlComponent(file):" in message:
            raised = True
            raise RuntimeError("profile failed after Splash component creation")
        return original_info(message)

    window_class = _isolated_window_class(Window, temp_dir, "profile")
    window = _new_window(WindowType.BAR, window_class)
    _splash_builder.info = fail_after_component
    try:
        window.show()
        pump(120)
        assert raised
        assert window._splash_instance is not None
        assert window._window.property("_splashInstance") is not None
        assert not any(
            "component.setData fallback" in message for message in profile_messages
        )
    finally:
        _splash_builder.info = original_info
        _dispose_window(window)


def _exercise_file_fallback(temp_dir):
    from prismqml import Window, WindowType

    blocked_cache = Path(temp_dir) / "blocked-splash-cache"
    blocked_cache.write_text("not a directory", encoding="utf-8")

    class FileFallbackWindow(Window):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / "fallback-windows"
        _GENERATED_SPLASH_QML_CACHE_DIR = blocked_cache

    window = _new_window(WindowType.BAR, FileFallbackWindow)
    try:
        window.show()
        pump(120)
        assert window._splash_instance is not None
        assert window._window.property("_splashInstance") is not None
    finally:
        _dispose_window(window)


def _exercise_deleted_window_mount_failure(temp_dir):
    from prismqml import Window, WindowType

    window_class = _isolated_window_class(Window, temp_dir, "deleted")
    window = _new_window(WindowType.BAR, window_class)
    window.setSplashEnabled(False)
    try:
        window.show()
        pump(60)
        qml_window = window._window
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
        QApplication.processEvents()
        assert not shiboken6.isValid(qml_window)

        window.setSplashEnabled(True)
        window._create_splash()
        assert window._splash_instance is None
    finally:
        _dispose_window(window)


def _exercise_rich_splash_contract(temp_dir):
    from prismqml import Window, WindowType

    window_class = _isolated_window_class(Window, temp_dir, "rich")
    window = _new_window(WindowType.BAR, window_class)
    title = 'Title "quoted" {brace}\nline'
    subtitle = "Sub $ value"
    window.resize(1111, 777)
    window.showSplash(":/icons/splash.svg", title, subtitle)
    try:
        window.show()
        pump(120)
        splash = window._window.property("_splashInstance")
        assert splash is window._splash_instance
        assert window._splash_component is not None
        assert splash.property("iconSource") == "qrc:/icons/splash.svg"
        assert splash.property("title") == title
        assert splash.property("subtitle") == subtitle
        assert splash.parentItem() == window._window.contentItem()
        assert splash.property("width") == 1111
        assert splash.property("height") == 777
    finally:
        _dispose_window(window)


def _assert_boundary_records(records):
    _assert_traceback_record(
        records,
        "[Splash] 文件化组件已创建，后续诊断失败，保留文件组件",
        RuntimeError,
        'raise RuntimeError("profile failed after Splash component creation")',
    )
    _assert_traceback_record(
        records,
        "[Splash] 文件化加载失败，回退到 inline",
        FileExistsError,
        "cache_dir.mkdir(parents=True, exist_ok=True)",
    )
    _assert_traceback_record(
        records,
        "[Splash] 创建启动画面失败(不影响启动)",
        RuntimeError,
        "builder._window.contentItem()",
    )


def main():
    from prismqml.python.core.logger import getLogger

    app = QApplication.instance() or QApplication(sys.argv)
    capture = _RecordCapture()
    logger = getLogger().logger
    logger.addHandler(capture)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                os.environ, {"PRISMQML_STARTUP_PROFILE_VERBOSE": "1"}
            ):
                _exercise_post_component_profile_failure(temp_dir)
            _exercise_file_fallback(temp_dir)
            _exercise_deleted_window_mount_failure(temp_dir)
            _exercise_rich_splash_contract(temp_dir)
    finally:
        logger.removeHandler(capture)

    _assert_boundary_records(capture.records)
    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
