# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Logger exception formatting regressions. 日志异常格式化回归。"""

import logging
import sys
from types import SimpleNamespace

import pytest

from prismqml.python.core.logger import ColoredFormatter, PlainFormatter


class _RecordCapture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def project_log_records():
    from prismqml.python.core.logger import getLogger

    capture = _RecordCapture()
    logger = getLogger().logger
    logger.addHandler(capture)
    try:
        yield capture.records
    finally:
        logger.removeHandler(capture)


def _assert_traceback_record(records, marker, error_type, source_text):
    matches = [record for record in records if marker in record.getMessage()]
    assert len(matches) == 1
    assert matches[0].exc_info
    assert matches[0].exc_info[0] is error_type
    rendered = PlainFormatter(datefmt="%H:%M:%S").format(matches[0])
    assert "Traceback (most recent call last):" in rendered
    assert source_text in rendered


def _runtime_failure_record() -> logging.LogRecord:
    try:
        raise RuntimeError("DwmFlush failed")
    except RuntimeError:
        return logging.LogRecord(
            "PrismQML", logging.ERROR, __file__, 1,
            "native filter failed", (), sys.exc_info()
        )


@pytest.mark.parametrize(
    "formatter",
    (ColoredFormatter(datefmt="%H:%M:%S"), PlainFormatter(datefmt="%H:%M:%S")),
    ids=("colored", "plain"),
)
def test_custom_formatters_render_exception_traceback(formatter):
    output = formatter.format(_runtime_failure_record())

    assert "native filter failed" in output
    assert "Traceback (most recent call last):" in output
    assert "raise RuntimeError" in output
    assert "RuntimeError: DwmFlush failed" in output


def test_exception_traceback_is_reused_once_across_handlers():
    record = _runtime_failure_record()
    colored = ColoredFormatter(datefmt="%H:%M:%S")
    plain = PlainFormatter(datefmt="%H:%M:%S")

    outputs = (colored.format(record), plain.format(record), colored.format(record))

    assert record.exc_text is not None
    for output in outputs:
        assert output.count("Traceback (most recent call last):") == 1
        assert output.count("RuntimeError: DwmFlush failed") == 1


def test_install_qt_message_handler_routes_real_warning(project_log_records):
    from PySide6.QtCore import qInstallMessageHandler, qWarning
    from prismqml.python.core.logger import install_qt_message_handler

    previous_handler = qInstallMessageHandler(None)
    qInstallMessageHandler(previous_handler)
    try:
        install_qt_message_handler()
        qWarning("real Qt warning route marker")
    finally:
        qInstallMessageHandler(previous_handler)

    matches = [
        record
        for record in project_log_records
        if "real Qt warning route marker" in record.getMessage()
    ]
    assert len(matches) == 1
    assert matches[0].levelno == logging.WARNING
    assert matches[0].tag == "QML"


def test_qt_warning_includes_source_context_and_replays_breadcrumbs_once(
    project_log_records,
):
    from PySide6.QtCore import QtMsgType
    from prismqml.python.core.logger import _create_qt_message_handler

    handler = _create_qt_message_handler(QtMsgType)
    context = SimpleNamespace(
        category="qml",
        file="qrc:/diagnostics/Page.qml",
        line=77,
        function="onCurrentIndexChanged",
    )
    breadcrumb = (
        "[懒加载诊断] StackedWidget #9 stage=stacked.current_index_changed "
        "target=2 current=2 display=1"
    )

    handler(QtMsgType.QtInfoMsg, context, breadcrumb)
    handler(QtMsgType.QtWarningMsg, context, "Unable to assign [undefined] to QColor")
    handler(QtMsgType.QtWarningMsg, context, "second warning")

    warning_records = [
        record for record in project_log_records if record.levelno == logging.WARNING
    ]
    assert len(warning_records) == 2
    rendered_warning = warning_records[0].getMessage()
    assert "[QtContext]" in rendered_warning
    assert "category=qml" in rendered_warning
    assert "file=qrc:/diagnostics/Page.qml" in rendered_warning
    assert "line=77" in rendered_warning
    assert "function=onCurrentIndexChanged" in rendered_warning

    replay_records = [
        record
        for record in project_log_records
        if getattr(record, "tag", "") == "QML:BREADCRUMB"
    ]
    assert len(replay_records) == 1
    assert breadcrumb in replay_records[0].getMessage()


def test_install_qt_message_handler_failure_logs_traceback(
    monkeypatch, project_log_records
):
    import PySide6.QtCore as qt_core
    from prismqml.python.core import logger as logger_module

    def fail_install(_handler):
        raise RuntimeError("Qt handler install exploded")

    monkeypatch.setattr(qt_core, "qInstallMessageHandler", fail_install)
    logger_module.install_qt_message_handler()

    _assert_traceback_record(
        project_log_records,
        "Failed to install Qt message handler",
        RuntimeError,
        'raise RuntimeError("Qt handler install exploded")',
    )


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_install_qt_message_handler_process_control_propagates(
    monkeypatch, error_type
):
    import PySide6.QtCore as qt_core
    from prismqml.python.core import logger as logger_module

    def stop_install(_handler):
        raise error_type("stop")

    monkeypatch.setattr(qt_core, "qInstallMessageHandler", stop_install)
    with pytest.raises(error_type, match="stop"):
        logger_module.install_qt_message_handler()
