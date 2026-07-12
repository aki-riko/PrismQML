# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color-array callable owner regressions. 颜色数组可调用所有者回归。"""

from pathlib import PurePosixPath
from time import perf_counter

import pytest

from scripts.qml_conventions import scan_source_text


JAVASCRIPT_PATH = PurePosixPath("prismqml/PrismQML/Test.js")
QML_PATH = PurePosixPath("prismqml/PrismQML/Test.qml")


def _qml010_lines(source: str, path: PurePosixPath = JAVASCRIPT_PATH) -> list[int]:
    return [
        item.line
        for item in scan_source_text(source, path)
        if item.rule == "QML010"
    ]


CALLABLE_TEMPLATES = (
    "function fallbackColors(){{return {expression}}}",
    "const fallbackColors=function(){{return {expression}}}",
    "const api={{fallbackColors(){{return {expression}}}}}",
    "const fallbackColors=()=>{{return {expression}}}",
    "const fallbackColors=()=>{expression}",
)


@pytest.mark.parametrize(
    "expression",
    (
        '["red"]',
        '(["red"])',
        'enabled ? ["red"] : ["blue"]',
        'value || ["red"]',
        'value && ["red"]',
        'value ?? ["red"]',
    ),
)
@pytest.mark.parametrize("template", CALLABLE_TEMPLATES)
def test_all_callable_forms_report_direct_result_branches(
    expression: str, template: str
):
    source = template.format(expression=expression) + "\n"
    assert _qml010_lines(source) == [1], source


@pytest.mark.parametrize(
    "source",
    (
        'async function fallbackColors(){return await ["red"]}',
        'const fallbackColors=async function(){return await ["red"]}',
        'const api={async fallbackColors(){return await ["red"]}}',
        'const fallbackColors=async()=>{return await ["red"]}',
        'const fallbackColors=async()=>await ["red"]',
    ),
)
def test_all_async_callable_forms_report_awaited_arrays(source: str):
    assert _qml010_lines(source + "\n") == [1]


@pytest.mark.parametrize(
    "expression",
    (
        'make(["red"])',
        'value + ["red"]',
        'value * ["red"]',
        'value < ["red"]',
        'value === ["red"]',
        '["red"] + value',
        '["red"] < value',
        '["red"] === value',
    ),
)
@pytest.mark.parametrize("template", CALLABLE_TEMPLATES)
def test_all_callable_forms_exclude_non_result_array_operands(
    expression: str, template: str
):
    source = template.format(expression=expression) + "\n"
    assert _qml010_lines(source) == [], source


@pytest.mark.parametrize(
    "source",
    (
        'const fallbackColors=(function(){return ["red"]})',
        'const fallbackColors=(async function(){return ["red"]})',
        'const fallbackColors=(()=>["red"])',
        'const fallbackColors=(()=>{return ["red"]})',
        'const api={fallbackColors:(function(){return ["red"]})}',
        'const api={fallbackColors:(()=>["red"])}',
    ),
)
def test_grouped_callable_values_keep_their_collection_owner(source: str):
    assert _qml010_lines(source + "\n") == [1]


def test_qml_callable_bindings_share_the_javascript_return_policy():
    positive = """Item {
    property var fallbackColors: () => enabled ? ["red"] : ["blue"]
    property var fallbackPalette: (function() { return ["white"] })
}
"""
    negative = """Item {
    function fallbackColors() { return value + ["red"] }
    property var fallbackPalette: () => make(["blue"])
}
"""

    assert _qml010_lines(positive, QML_PATH) == [2, 3]
    assert _qml010_lines(negative, QML_PATH) == []


def test_callable_owners_expand_beyond_the_fast_prefix_window():
    padding = "/*" + "x" * 600 + "*/"
    source = f"""const fallbackColors={padding}function(){{return ["red"]}}
const fallbackPalette={padding}()=>{{return ["blue"]}}
const moreColors={padding}()=>["white"]
const api={{fallbackColors:{padding}(()=>["black"])}}
"""

    assert _qml010_lines(source) == [1, 2, 3, 4]


def test_callable_and_parameter_indexes_scale_to_thousands_of_spans():
    functions = "\n".join(
        f'function fallback{index}Colors(){{return ["red"]}}'
        for index in range(6000)
    )
    parameters = "\n".join(
        f'function label{index}(value=["red"]){{return value}}'
        for index in range(6000)
    )
    started = perf_counter()

    function_lines = _qml010_lines(functions)
    parameter_lines = _qml010_lines(parameters)

    assert len(function_lines) == 6000
    assert parameter_lines == []
    assert perf_counter() - started < 3.0


def test_many_returns_within_one_callable_remain_linear():
    returns = "\n".join(
        f'if (value === {index}) return ["red"];'
        for index in range(4000)
    )
    source = f"function fallbackColors(value) {{\n{returns}\n}}\n"
    started = perf_counter()

    lines = _qml010_lines(source)

    assert len(lines) == 4000
    assert perf_counter() - started < 2.0
