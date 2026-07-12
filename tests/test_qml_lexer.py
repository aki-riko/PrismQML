# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML lexer structural regressions. QML 词法结构回归。"""

from pathlib import PurePosixPath
from time import perf_counter

import pytest

from scripts.qml_conventions import scan_source_text
from scripts.qml_lexer import sanitize_qml


JAVASCRIPT_PATH = PurePosixPath("prismqml/PrismQML/Test.js")


def _qml010_lines(source: str) -> list[int]:
    return [
        item.line
        for item in scan_source_text(source, JAVASCRIPT_PATH)
        if item.rule == "QML010"
    ]


@pytest.mark.parametrize(
    "statement",
    (
        'if (fn("(")) /\\{/.test(value);',
        'if (fn(/* ( */ value)) /\\{/.test(value);',
        'if (/\\(/.test(value)) /\\{/.test(value);',
        'if (value) noop(); else /\\{/.test(value);',
        'do /\\{/.test(value); while (false);',
        'if (value) {} /\\{/.test(value);',
    ),
)
def test_regex_context_does_not_corrupt_later_function_frames(statement: str):
    source = f"function fallbackColors(value) {{\n    {statement}\n    return [\"red\"]\n}}\n"

    assert _qml010_lines(source) == [3]


def test_regex_dense_sanitizing_remains_linear():
    source = "\n".join("if (ready) /x/.test(value);" for _ in range(8000))
    started = perf_counter()

    sanitized = sanitize_qml(source, mask_strings=True, mark_values=True)

    assert len(sanitized) == len(source)
    assert perf_counter() - started < 1.5
