# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Logger exception formatting regressions. 日志异常格式化回归。"""

import logging
import sys
from types import SimpleNamespace

import pytest

from prismqml.python.core.logger import Colors, ColoredFormatter, PlainFormatter


_INFO_RGB = (96, 165, 250)
_WARNING_RGB = (217, 119, 6)


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


def _level_record(level: int) -> logging.LogRecord:
    return logging.LogRecord(
        "PrismQML",
        level,
        __file__,
        1,
        "CLI color probe",
        (),
        None,
    )


def _truecolor_code(rgb: tuple[int, int, int]) -> str:
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def _weighted_brightness(rgb: tuple[int, int, int]) -> float:
    red, green, blue = rgb
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


@pytest.mark.parametrize(
    ("level", "expected_rgb"),
    (
        (logging.INFO, _INFO_RGB),
        (logging.WARNING, _WARNING_RGB),
    ),
)
def test_colored_formatter_uses_distinct_info_warning_palette(level, expected_rgb):
    output = ColoredFormatter(datefmt="%H:%M:%S").format(_level_record(level))

    level_name = logging.getLevelName(level)
    expected_color = _truecolor_code(expected_rgb)
    assert f"{expected_color}[{level_name}]{Colors.RESET}" in output


def test_warning_cli_color_is_darker_than_info():
    info_brightness = _weighted_brightness(_INFO_RGB)
    warning_brightness = _weighted_brightness(_WARNING_RGB)

    assert info_brightness - warning_brightness >= 20


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

    handler(QtMsgType.QtDebugMsg, context, breadcrumb)
    handler(QtMsgType.QtWarningMsg, context, " \n\t")
    handler(
        QtMsgType.QtWarningMsg,
        context,
        "qrc:/diagnostics/Page.qml:77:9: ",
    )
    handler(QtMsgType.QtWarningMsg, context, "Unable to assign [undefined] to QColor")
    handler(QtMsgType.QtWarningMsg, context, "qrc:/diagnostics/Page.qml:77:9: second warning")

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
    assert "second warning" in warning_records[1].getMessage()

    replay_records = [
        record
        for record in project_log_records
        if getattr(record, "tag", "") == "QML:BREADCRUMB"
    ]
    assert len(replay_records) == 1
    assert replay_records[0].levelno == logging.DEBUG
    assert breadcrumb in replay_records[0].getMessage()


def test_qt_clipboard_retry_is_debug_but_other_mime_warnings_remain_visible(
    project_log_records,
):
    from PySide6.QtCore import QtMsgType
    from prismqml.python.core.logger import _create_qt_message_handler

    handler = _create_qt_message_handler(QtMsgType)
    context = SimpleNamespace(
        category="qt.qpa.mime",
        file=None,
        line=0,
        function=None,
    )

    handler(QtMsgType.QtWarningMsg, context, "Retrying to obtain clipboard.")
    handler(QtMsgType.QtWarningMsg, context, "Clipboard conversion failed.")

    clipboard_records = [
        record
        for record in project_log_records
        if "clipboard" in record.getMessage().lower()
    ]
    assert [record.levelno for record in clipboard_records] == [
        logging.DEBUG,
        logging.WARNING,
    ]
    assert clipboard_records[0].tag == "QML:QT.QPA.MIME"
    assert "[QtContext]" not in clipboard_records[0].getMessage()
    assert "[QtContext]" in clipboard_records[1].getMessage()


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
