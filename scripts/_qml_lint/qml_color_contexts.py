# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Detect hardcoded QML color strings in style contexts. 检测样式上下文中的 QML 硬编码颜色。"""

from __future__ import annotations

import re
from typing import Iterable, Iterator, Sequence


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
    r"(?P<expression>.*))"
)
INLINE_PROPERTY_BINDING_RE = re.compile(
    r"(?=(?:^|[({;,])\s*(?:(?:default|required|readonly)\s+)*property\s+"
    r"(?P<type>alias|[A-Za-z_]\w*(?:<[^>]+>)?)\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*:(?P<expression>.*))"
)
CANVAS_ASSIGNMENT_RE = re.compile(
    r"\b(?:[A-Za-z_]\w*\.)*(?:fillStyle|strokeStyle|shadowColor)\s*="
    r"(?P<expression>[^;]+)"
)
COLOR_STOP_CALL_RE = re.compile(r"\b(?:[A-Za-z_]\w*\.)*addColorStop\s*\(")
COLOR_FUNCTION_RE = re.compile(
    r"^\s*function\s+(?P<name>[A-Za-z_]\w*)\s*\([^)]*\)\s*\{"
    r"(?P<body>.*)$"
)
RETURN_RE = re.compile(r"\breturn\b(?P<expression>[^;}]*)(?:[;}])?")
QUOTED_COLOR_RE = re.compile(
    r"(?P<quote>['\"`])(?P<value>#[0-9A-Fa-f]{3,8}|[A-Za-z]+)(?P=quote)"
)
NON_VALUE_OPERATORS = ("===", "!==", "==", "!=")
BLOCK_EXPRESSION_RE = re.compile(r"^\s*(?:\{|function\b)")
CONTINUATION_PREFIXES = ("?", ":", "&&", "||", ".")
CLOSING_OPENERS = {"}": "{", "]": "[", ")": "("}


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


def _previous_nonspace_index(text: str, index: int) -> int:
    current = index - 1
    while current >= 0 and text[current].isspace():
        current -= 1
    return current


def _next_nonspace_index(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _previous_word(text: str, end: int) -> str:
    start = end
    while start >= 0 and (text[start].isalnum() or text[start] in "_$"):
        start -= 1
    return text[start + 1:end + 1]


def _has_non_value_operator_before(text: str, start: int) -> bool:
    previous = _previous_nonspace_index(text, start)
    if previous < 0:
        return False
    if _previous_word(text, previous) == "case":
        return True
    return any(
        text[max(0, previous - len(operator) + 1):previous + 1] == operator
        for operator in NON_VALUE_OPERATORS
    )


def _has_non_value_operator_after(text: str, end: int) -> bool:
    following = _next_nonspace_index(text, end)
    return any(text.startswith(operator, following) for operator in NON_VALUE_OPERATORS)


def _is_literal_value(
    expression: str, match: re.Match[str], allow_array_items: bool
) -> bool:
    value = match.group("value")
    if not value.startswith("#") and value.casefold() not in QML_NAMED_COLORS:
        return False
    previous = _previous_nonspace_index(expression, match.start())
    following = _next_nonspace_index(expression, match.end())
    if _has_non_value_operator_before(
        expression, match.start()
    ) or _has_non_value_operator_after(expression, match.end()):
        return False
    if not allow_array_items and previous >= 0 and expression[previous] == "[":
        return False
    if (
        following < len(expression)
        and expression[following] == ":"
        and (previous < 0 or expression[previous] in "{,")
    ):
        return False
    return True


def iter_color_literals(
    expression: str, *, allow_array_items: bool = False
) -> Iterator[re.Match[str]]:
    """Yield direct QML color literals. 迭代直接 QML 颜色字面量。"""
    return (
        match
        for match in QUOTED_COLOR_RE.finditer(expression)
        if _is_literal_value(expression, match, allow_array_items)
    )


def _outside_array_starts(code: str, starts: Iterable[int]) -> set[int]:
    targets = set(starts)
    result: set[int] = set()
    depth = 0
    for index, char in enumerate(code):
        if index in targets and depth == 0:
            result.add(index)
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(depth - 1, 0)
    return result


def _has_color_literal(code: str, source: str) -> bool:
    return bool(_color_literal_spans(code, source))


def _color_literal_spans(code: str, source: str) -> list[tuple[int, int]]:
    if len(code) != len(source):
        return []
    matches = list(iter_color_literals(source))
    allowed = _outside_array_starts(code, (match.start() for match in matches))
    return [
        (match.start(), match.end())
        for match in matches
        if match.start() in allowed
    ]


def _source_group(source: str, match: re.Match[str], name: str) -> str:
    return source[match.start(name) : match.end(name)]


def _expression_pair(
    code: str, source: str, match: re.Match[str], name: str
) -> tuple[str, str]:
    return _source_group(code, match, name), _source_group(source, match, name)


def _inline_expression_end(code: str, start: int) -> int:
    stack: list[str] = []
    for index in range(start, len(code)):
        char = code[index]
        if char in "{[(":
            stack.append(char)
        elif char in CLOSING_OPENERS:
            if not stack or stack[-1] != CLOSING_OPENERS[char]:
                return index
            stack.pop()
        elif char == ";" and not stack:
            return index
    return len(code)


def _inline_expression_pair(
    code: str, source: str, match: re.Match[str]
) -> tuple[str, str]:
    start = match.start("expression")
    end = _inline_expression_end(code, start)
    return code[start:end], source[start:end]


def _color_stop_argument_span(code: str, opening: int) -> tuple[int, int] | None:
    stack = ["("]
    argument_start: int | None = None
    for index in range(opening + 1, len(code)):
        char = code[index]
        if char in "{[(":
            stack.append(char)
        elif char in CLOSING_OPENERS:
            if not stack or stack[-1] != CLOSING_OPENERS[char]:
                return None
            stack.pop()
            if not stack:
                return (argument_start, index) if argument_start is not None else None
        elif char == "," and len(stack) == 1 and argument_start is None:
            argument_start = index + 1
    return None


def _color_stop_expression_pairs(
    code: str, source: str
) -> Iterable[tuple[str, str]]:
    for match in COLOR_STOP_CALL_RE.finditer(code):
        span = _color_stop_argument_span(code, match.end() - 1)
        if span is not None:
            start, end = span
            yield code[start:end], source[start:end]


def _return_literals(code: str, source: str) -> bool:
    return any(
        _has_color_literal(*_expression_pair(code, source, match, "expression"))
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
            if _has_color_literal(code, source):
                result.add(number)
            continue
        pending = False
    return result


def _direct_context_expressions(
    code: str, source: str
) -> Iterable[tuple[str, str]]:
    binding = _binding_match(code)
    if binding is not None and not BLOCK_EXPRESSION_RE.match(binding.group("expression")):
        yield _expression_pair(code, source, binding, "expression")
    for match in INLINE_BINDING_RE.finditer(code):
        if _is_color_name(match.group("name")):
            yield _inline_expression_pair(code, source, match)
    for match in INLINE_PROPERTY_BINDING_RE.finditer(code):
        if match.group("type") == "color" or _is_color_name(match.group("name")):
            yield _inline_expression_pair(code, source, match)
    for match in CANVAS_ASSIGNMENT_RE.finditer(code):
        yield _expression_pair(code, source, match, "expression")
    yield from _color_stop_expression_pairs(code, source)


def color_literal_lines(
    code_lines: Sequence[str], source_lines: Sequence[str]
) -> set[int]:
    """Return 1-based source lines containing style color literals. 返回样式颜色字面量行。"""
    result = _return_context_lines(code_lines, source_lines)
    result.update(_continuation_lines(code_lines, source_lines))
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        if any(
            _has_color_literal(*item)
            for item in _direct_context_expressions(code, source)
        ):
            result.add(number)
    return result
