# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Logger exception formatting regressions. 日志异常格式化回归。"""

import logging
import sys

import pytest

from prismqml.python.core.logger import ColoredFormatter, PlainFormatter


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
