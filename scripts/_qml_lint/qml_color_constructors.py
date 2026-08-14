# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Detect hardcoded Qt numeric color constructors. 检测 Qt 数值硬编码构色。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from decimal import Decimal, DecimalException, InvalidOperation
import re
from typing import Iterator
import warnings


QT_RECEIVER_PATTERN = r"(?<![\w$])Qt(?P<closing>(?:\s*\))*)"
DOT_CONSTRUCTOR_RE = re.compile(
    rf"{QT_RECEIVER_PATTERN}\s*(?:\?\.\s*|\.\s*)"
    r"(?P<kind>rgba|hsla|hsva)\s*\("
)
BRACKET_CONSTRUCTOR_RE = re.compile(
    rf"{QT_RECEIVER_PATTERN}\s*(?:\?\.\s*)?\[\s*"
    r"(?P<quote>['\"`])(?P<kind>rgba|hsla|hsva)(?P=quote)\s*\]\s*\("
)
EXPRESSION_PREFIX_WORDS = frozenset(
    {
        "await",
        "case",
        "default",
        "delete",
        "do",
        "else",
        "extends",
        "in",
        "instanceof",
        "new",
        "of",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }
)
ECMASCRIPT_LINEBREAK_CHARS = frozenset("\r\n\u2028\u2029")
SOURCE_LINEBREAK_CHARS = frozenset("\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029")
MAX_CONSTRUCTOR_BODY_LENGTH = 4096
MAX_NUMERIC_EXPRESSION_LENGTH = 256
MAX_NUMERIC_AST_NODES = 128
MAX_NUMERIC_AST_DEPTH = 64
MAX_TERNARY_DEPTH = 16


@dataclass(frozen=True)
class NumericColorFinding:
    """Constructor span plus legacy Qt-token report line. 构色区间及旧版 Qt 标记报告行。"""

    line: int
    start: int
    end: int
    qt_start: int


@dataclass(frozen=True)
class _ConstructorCall:
    kind: str
    arguments: tuple[str, ...]
    line: int
    start: int
    end: int
    qt_start: int


def _normalize_views(
    code: str, quoted_code: str | None
) -> tuple[str, str | None]:
    normalized_code = "\n".join(code.splitlines())
    if quoted_code is None:
        return normalized_code, None
    if len(code) != len(quoted_code):
        return normalized_code, None
    normalized_quoted = "\n".join(quoted_code.splitlines())
    if len(normalized_code) != len(normalized_quoted):
        return normalized_code, None
    return normalized_code, normalized_quoted


def _compact(expression: str) -> str:
    return re.sub(r"\s+", "", expression)


def _outer_parentheses_wrap(expression: str) -> bool:
    if not expression.startswith("(") or not expression.endswith(")"):
        return False
    depth = 0
    for index, char in enumerate(expression):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and index != len(expression) - 1:
                return False
    return depth == 0


def _strip_outer_parentheses(expression: str) -> str:
    result = expression.strip()
    while _outer_parentheses_wrap(result):
        result = result[1:-1].strip()
    return result


def _binary_value(node: ast.BinOp, depth: int) -> Decimal | None:
    left = _numeric_node_value(node.left, depth + 1)
    right = _numeric_node_value(node.right, depth + 1)
    if left is None or right is None:
        return None
    try:
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow) and right == right.to_integral_value():
            return left ** int(right) if abs(right) <= 16 else None
    except (ArithmeticError, DecimalException, InvalidOperation, OverflowError):
        return None
    return None


def _numeric_node_value(node: ast.AST, depth: int = 0) -> Decimal | None:
    if depth > MAX_NUMERIC_AST_DEPTH:
        return None
    if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
        return Decimal(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _numeric_node_value(node.operand, depth + 1)
        if value is None:
            return None
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        return _binary_value(node, depth)
    return None


def _number_value(expression: str) -> Decimal | None:
    if not expression or len(expression) > MAX_NUMERIC_EXPRESSION_LENGTH:
        return None
    try:
        candidate = _strip_outer_parentheses(_compact(expression))
        if not candidate or len(candidate) > MAX_NUMERIC_EXPRESSION_LENGTH:
            return None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            node = ast.parse(candidate, mode="eval").body
        if sum(1 for _ in ast.walk(node)) > MAX_NUMERIC_AST_NODES:
            return None
        return _numeric_node_value(node)
    except (MemoryError, RecursionError, SyntaxError, ValueError):
        return None


def _split_top_level(expression: str, separator: str) -> list[str]:
    result: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(expression):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == separator and depth == 0:
            result.append(expression[start:index].strip())
            start = index + 1
    result.append(expression[start:].strip())
    return result


def _is_non_ternary_question(expression: str, index: int) -> bool:
    if (index > 0 and expression[index - 1] == "?") or expression.startswith("??", index):
        return True
    next_index = index + 2
    return expression.startswith("?.", index) and (
        next_index == len(expression) or not expression[next_index].isdigit()
    )


def _ternary_branches(expression: str) -> tuple[str, str] | None:
    candidate = _strip_outer_parentheses(expression)
    question = None
    nested = 0
    depth = 0
    for index, char in enumerate(candidate):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif depth == 0 and char == "?":
            if _is_non_ternary_question(candidate, index):
                continue
            if question is None:
                question = index
            else:
                nested += 1
        elif depth == 0 and char == ":" and question is not None:
            if nested:
                nested -= 1
            else:
                return candidate[question + 1 : index], candidate[index + 1 :]
    return None


def _fixed_numeric_choice(expression: str, depth: int = 0) -> bool:
    if depth > MAX_TERNARY_DEPTH or len(expression) > MAX_NUMERIC_EXPRESSION_LENGTH:
        return False
    if _number_value(expression) is not None:
        return True
    branches = _ternary_branches(_compact(expression))
    return branches is not None and all(
        _fixed_numeric_choice(item, depth + 1) for item in branches
    )


def is_fixed_numeric_expression(expression: str) -> bool:
    """Return whether an expression is a fixed numeric choice. 返回表达式是否为固定数值选择。"""
    return _fixed_numeric_choice(expression)


def _parenthesis_ends(code: str) -> dict[int, int]:
    stack: list[int] = []
    result: dict[int, int] = {}
    for index, char in enumerate(code):
        if char == "(":
            stack.append(index)
        elif char == ")" and stack:
            result[stack.pop()] = index + 1
    return result


def _previous_word(code: str, end: int) -> str:
    start = end
    while start >= 0 and (code[start].isalnum() or code[start] in "_$"):
        start -= 1
    return code[start + 1 : end + 1]


def _has_external_receiver(code: str, start: int) -> bool:
    index = start - 1
    saw_linebreak = False
    while index >= 0 and code[index].isspace():
        saw_linebreak = saw_linebreak or code[index] in ECMASCRIPT_LINEBREAK_CHARS
        index -= 1
    if index < 0:
        return False
    if code[index] == ".":
        return True
    if saw_linebreak and code[start] == "Q":
        return False
    if code[index] in ")]":
        return True
    if code[index].isalnum() or code[index] in "_$":
        return _previous_word(code, index) not in EXPRESSION_PREFIX_WORDS
    return False


def _linebreak_count(code: str, start: int, end: int) -> int:
    count = 0
    index = start
    while index < end:
        char = code[index]
        if char in SOURCE_LINEBREAK_CHARS:
            count += 1
            if char == "\r" and index + 1 < end and code[index + 1] == "\n":
                index += 1
        index += 1
    return count


def _receiver_start(code: str, match: re.Match[str]) -> int | None:
    start = match.start()
    index = start - 1
    for _ in range(match.group("closing").count(")")):
        while index >= 0 and code[index].isspace():
            index -= 1
        if index < 0 or code[index] != "(":
            return None
        start = index
        index -= 1
    return start


def _constructor_matches(
    code: str, quoted_code: str | None
) -> list[re.Match[str]]:
    matches = list(DOT_CONSTRUCTOR_RE.finditer(code))
    if quoted_code is not None and len(quoted_code) == len(code):
        matches.extend(
            match
            for match in BRACKET_CONSTRUCTOR_RE.finditer(quoted_code)
            if code[match.start()] == "Q"
        )
    return sorted(matches, key=lambda match: match.start())


def _constructor_calls(
    code: str, quoted_code: str | None = None
) -> Iterator[_ConstructorCall]:
    ends = _parenthesis_ends(code)
    line = 1
    cursor = 0
    for match in _constructor_matches(code, quoted_code):
        line += _linebreak_count(code, cursor, match.start())
        cursor = match.start()
        start = _receiver_start(code, match)
        if start is None or _has_external_receiver(code, start):
            continue
        open_index = match.end() - 1
        end = ends.get(open_index)
        if end is None or end - open_index > MAX_CONSTRUCTOR_BODY_LENGTH:
            continue
        body = code[match.end() : end - 1]
        yield _ConstructorCall(
            match.group("kind"),
            tuple(_split_top_level(body, ",")),
            line,
            start,
            end,
            match.start(),
        )


def _channel_base(expression: str, channel: str) -> str | None:
    if len(expression) > MAX_NUMERIC_EXPRESSION_LENGTH:
        return None
    candidate = _strip_outer_parentheses(_compact(expression))
    suffix = f".{channel}"
    if not candidate.endswith(suffix):
        return None
    base = _strip_outer_parentheses(candidate[: -len(suffix)])
    return base or None


def _matching_channel_base(arguments: list[str]) -> str | None:
    bases = [_channel_base(value, channel) for value, channel in zip(arguments, "rgb")]
    if bases[0] is None or any(base != bases[0] for base in bases[1:]):
        return None
    return bases[0]


def _scaled_channel(expression: str, channel: str) -> tuple[str, Decimal] | None:
    if len(expression) > MAX_NUMERIC_EXPRESSION_LENGTH:
        return None
    parts = _split_top_level(_strip_outer_parentheses(expression), "*")
    if len(parts) != 2:
        return None
    for channel_part, number_part in (parts, parts[::-1]):
        base = _channel_base(channel_part, channel)
        factor = _number_value(number_part)
        if base is not None and factor is not None:
            return base, factor
    return None


def _matching_scaled_base(arguments: list[str]) -> str | None:
    scaled = [_scaled_channel(value, channel) for value, channel in zip(arguments, "rgb")]
    if scaled[0] is None or any(item is None for item in scaled[1:]):
        return None
    base, factor = scaled[0]
    if any(item != (base, factor) for item in scaled[1:]):
        return None
    return base


def _fixed_alpha(expression: str, base: str | None = None) -> bool:
    if len(expression) > MAX_NUMERIC_EXPRESSION_LENGTH:
        return False
    candidate = _strip_outer_parentheses(_compact(expression))
    if _fixed_numeric_choice(candidate):
        return True
    if base is None:
        return False
    parts = _split_top_level(candidate, "*")
    for alpha_part, factor_part in (parts, parts[::-1]) if len(parts) == 2 else ():
        if _channel_base(alpha_part, "a") == base and _number_value(factor_part) is not None:
            return True
    return False


def _is_hardcoded_constructor(kind: str, arguments: list[str] | tuple[str, ...]) -> bool:
    if len(arguments) != 4:
        return False
    if all(_number_value(argument) is not None for argument in arguments[:3]):
        return True
    if kind != "rgba":
        return False
    if base := _matching_channel_base(arguments[:3]):
        return _fixed_alpha(arguments[3], base)
    if base := _matching_scaled_base(arguments[:3]):
        return _fixed_alpha(arguments[3], base)
    return False


def numeric_color_constructor_lines(
    code: str, quoted_code: str | None = None
) -> set[int]:
    """Return start lines for hardcoded Qt color calls. 返回 Qt 硬编码构色起始行。"""
    return {
        finding.line
        for finding in numeric_color_constructor_findings(code, quoted_code)
    }


def numeric_color_constructor_findings(
    code: str, quoted_code: str | None = None
) -> tuple[NumericColorFinding, ...]:
    """Return hardcoded Qt color call locations. 返回 Qt 硬编码构色调用位置。"""
    normalized_code, normalized_quoted = _normalize_views(code, quoted_code)
    return tuple(
        NumericColorFinding(call.line, call.start, call.end, call.qt_start)
        for call in _constructor_calls(normalized_code, normalized_quoted)
        if _is_hardcoded_constructor(call.kind, call.arguments)
    )
