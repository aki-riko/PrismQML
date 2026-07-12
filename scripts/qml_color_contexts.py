# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Detect hardcoded QML color strings in style contexts. 检测样式上下文中的 QML 硬编码颜色。"""

from __future__ import annotations

import re
from typing import Iterable, Sequence


# Qt 6.9 QColor.colorNames() snapshot; kept stdlib-only for the lint CI job.
# Qt 6.9 QColor.colorNames() 快照；保持纯标准库以供轻量 lint CI 使用。
QML_NAMED_COLORS = frozenset(
    """
    aliceblue antiquewhite aqua aquamarine azure beige bisque black
    blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse
    chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan
    darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta
    darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen
    darkslateblue darkslategray darkslategrey darkturquoise darkviolet
    deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite
    forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green
    greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender
    lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
    lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon
    lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue
    lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue
    mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
    mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
    navajowhite navy oldlace olive olivedrab orange orangered orchid
    palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff
    peru pink plum powderblue purple red rosybrown royalblue saddlebrown salmon
    sandybrown seagreen seashell sienna silver skyblue slateblue slategray
    slategrey snow springgreen steelblue tan teal thistle tomato transparent
    turquoise violet wheat white whitesmoke yellow yellowgreen
    """.split()
)

PROPERTY_BINDING_RE = re.compile(
    r"^\s*(?:(?:default|required|readonly)\s+)*property\s+"
    r"(?P<type>alias|[A-Za-z_]\w*(?:<[^>]+>)?)\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*:(?P<expression>.*)$"
)
ASSIGNMENT_BINDING_RE = re.compile(
    r"^\s*(?P<name>(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\s*:"
    r"(?P<expression>.*)$"
)
INLINE_BINDING_RE = re.compile(
    r"(?=(?:^|[({;,])\s*"
    r"(?P<name>(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\s*:"
    r"(?P<expression>[^,;}]+))"
)
CANVAS_ASSIGNMENT_RE = re.compile(
    r"\b(?:[A-Za-z_]\w*\.)*(?:fillStyle|strokeStyle|shadowColor)\s*="
    r"(?P<expression>[^;]+)"
)
COLOR_STOP_RE = re.compile(
    r"\b(?:[A-Za-z_]\w*\.)*addColorStop\s*\(\s*[^,]+,"
    r"(?P<expression>[^)]+)"
)
COLOR_FUNCTION_RE = re.compile(
    r"^\s*function\s+(?P<name>[A-Za-z_]\w*)\s*\([^)]*\)\s*\{"
    r"(?P<body>.*)$"
)
RETURN_RE = re.compile(r"\breturn\b(?P<expression>[^;}]*)(?:[;}])?")
QUOTED_COLOR_RE = re.compile(
    r"(?P<quote>['\"`])(?P<value>#[0-9A-Fa-f]{3,8}|[A-Za-z]+)(?P=quote)"
)
NON_VALUE_BEFORE_RE = re.compile(r"(?:===|!==|==|!=|\[|\bcase)\s*$")
NON_VALUE_AFTER_RE = re.compile(r"^\s*(?:===|!==|==|!=)")
BLOCK_EXPRESSION_RE = re.compile(r"^\s*(?:\{|function\b)")
CONTINUATION_PREFIXES = ("?", ":", "&&", "||", ".")


def _is_color_name(name: str) -> bool:
    return "color" in name.rsplit(".", 1)[-1].casefold()


def _binding_match(code: str) -> re.Match[str] | None:
    if match := PROPERTY_BINDING_RE.match(code):
        if match.group("type") == "color" or _is_color_name(match.group("name")):
            return match
    if match := ASSIGNMENT_BINDING_RE.match(code):
        if _is_color_name(match.group("name")):
            return match
    return None


def _is_literal_value(expression: str, match: re.Match[str]) -> bool:
    value = match.group("value")
    if not value.startswith("#") and value.casefold() not in QML_NAMED_COLORS:
        return False
    prefix = expression[: match.start()].rstrip()
    suffix = expression[match.end() :]
    if NON_VALUE_BEFORE_RE.search(prefix) or NON_VALUE_AFTER_RE.match(suffix):
        return False
    if suffix.lstrip().startswith(":") and re.search(r"(?:^|[{,])\s*$", prefix):
        return False
    return True


def _has_color_literal(expression: str) -> bool:
    return any(
        _is_literal_value(expression, match)
        for match in QUOTED_COLOR_RE.finditer(expression)
    )


def _source_group(source: str, match: re.Match[str], name: str) -> str:
    return source[match.start(name) : match.end(name)]


def _return_literals(code: str, source: str) -> bool:
    return any(
        _has_color_literal(_source_group(source, match, "expression"))
        for match in RETURN_RE.finditer(code)
    )


def _return_context_lines(
    code_lines: Sequence[str], source_lines: Sequence[str]
) -> set[int]:
    result: set[int] = set()
    depth = 0
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        if depth:
            if _return_literals(code, source):
                result.add(number)
            depth += code.count("{") - code.count("}")
            depth = max(depth, 0)
            continue
        binding = _binding_match(code)
        function = COLOR_FUNCTION_RE.match(code)
        if binding is not None:
            segment = _source_group(source, binding, "expression")
            code_segment = _source_group(code, binding, "expression")
            if not BLOCK_EXPRESSION_RE.match(code_segment):
                continue
            context_code = code_segment
        elif function is not None and _is_color_name(function.group("name")):
            segment = _source_group(source, function, "body")
            code_segment = _source_group(code, function, "body")
            context_code = code[function.start() :]
        else:
            continue
        if _return_literals(code_segment, segment):
            result.add(number)
        depth = max(context_code.count("{") - context_code.count("}"), 0)
    return result


def _continuation_lines(
    code_lines: Sequence[str], source_lines: Sequence[str]
) -> set[int]:
    result: set[int] = set()
    pending = False
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        binding = _binding_match(code)
        if binding is not None:
            expression = binding.group("expression")
            pending = not BLOCK_EXPRESSION_RE.match(expression)
            continue
        stripped = code.strip()
        if not pending or not stripped:
            continue
        if stripped.startswith(CONTINUATION_PREFIXES):
            if _has_color_literal(source):
                result.add(number)
            continue
        pending = False
    return result


def _direct_context_expressions(code: str, source: str) -> Iterable[str]:
    binding = _binding_match(code)
    if binding is not None and not BLOCK_EXPRESSION_RE.match(binding.group("expression")):
        yield _source_group(source, binding, "expression")
    for match in INLINE_BINDING_RE.finditer(code):
        if _is_color_name(match.group("name")):
            yield _source_group(source, match, "expression")
    for pattern in (CANVAS_ASSIGNMENT_RE, COLOR_STOP_RE):
        for match in pattern.finditer(code):
            yield _source_group(source, match, "expression")


def color_literal_lines(
    code_lines: Sequence[str], source_lines: Sequence[str]
) -> set[int]:
    """Return 1-based source lines containing style color literals. 返回样式颜色字面量行。"""
    result = _return_context_lines(code_lines, source_lines)
    result.update(_continuation_lines(code_lines, source_lines))
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        if any(_has_color_literal(item) for item in _direct_context_expressions(code, source)):
            result.add(number)
    return result
