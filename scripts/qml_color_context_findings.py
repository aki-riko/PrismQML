# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Position-level color context findings. 颜色上下文位置级结果。"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

if __package__:
    from . import qml_color_contexts as _contexts
else:
    import qml_color_contexts as _contexts


@dataclass(frozen=True)
class ColorLiteralFinding:
    """Color literal location in normalized source. 规范化源码中的颜色字面量位置。"""

    line: int
    start: int
    end: int
    expression_start: int
    expression_end: int


def _trimmed_bounds(text: str) -> tuple[int, int]:
    start = 0
    end = len(text)
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _expression_segment(
    code: str, source: str, match: re.Match[str], name: str
) -> tuple[str, str, int]:
    start = match.start(name)
    return code[start:match.end(name)], source[start:match.end(name)], start


def _inline_expression_segment(
    code: str, source: str, match: re.Match[str]
) -> tuple[str, str, int]:
    start = match.start("expression")
    end = _contexts._inline_expression_end(code, start)
    return code[start:end], source[start:end], start


def _color_stop_expression_segments(
    code: str, source: str
) -> Iterable[tuple[str, str, int]]:
    for match in _contexts.COLOR_STOP_CALL_RE.finditer(code):
        span = _contexts._color_stop_argument_span(code, match.end() - 1)
        if span is not None:
            start, end = span
            yield code[start:end], source[start:end], start


def _return_literal_spans(
    code: str, source: str
) -> list[tuple[int, int, int, int]]:
    result: list[tuple[int, int, int, int]] = []
    for match in _contexts.RETURN_RE.finditer(code):
        code_segment, source_segment, offset = _expression_segment(
            code, source, match, "expression"
        )
        expression_start, expression_end = _trimmed_bounds(source_segment)
        result.extend(
            (
                offset + start,
                offset + end,
                offset + expression_start,
                offset + expression_end,
            )
            for start, end in _contexts._color_literal_spans(
                code_segment, source_segment
            )
        )
    return result


def _return_context_segment(
    code: str, source: str
) -> tuple[str, str, str, int] | None:
    if binding := _contexts._binding_match(code):
        code_segment, source_segment, offset = _expression_segment(
            code, source, binding, "expression"
        )
        if _contexts.BLOCK_EXPRESSION_RE.match(code_segment):
            return code_segment, code_segment, source_segment, offset
    function = _contexts.COLOR_FUNCTION_RE.match(code)
    if function is not None and _contexts._is_color_name(function.group("name")):
        code_segment, source_segment, offset = _expression_segment(
            code, source, function, "body"
        )
        return code[function.start():], code_segment, source_segment, offset
    return None


def _line_findings(
    number: int, line_start: int, spans: Iterable[tuple[int, int, int, int]]
) -> list[ColorLiteralFinding]:
    return [
        ColorLiteralFinding(
            number,
            line_start + start,
            line_start + end,
            line_start + expression_start,
            line_start + expression_end,
        )
        for start, end, expression_start, expression_end in spans
    ]


def _return_context_findings(
    code_lines: Sequence[str], source_lines: Sequence[str], offsets: Sequence[int]
) -> list[ColorLiteralFinding]:
    result: list[ColorLiteralFinding] = []
    depth = 0
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        if depth:
            spans = _return_literal_spans(code, source)
            result.extend(_line_findings(number, offsets[number - 1], spans))
            depth = max(depth + code.count("{") - code.count("}"), 0)
            continue
        context = _return_context_segment(code, source)
        if context is None:
            continue
        context_code, code_segment, source_segment, offset = context
        spans = (
            (
                offset + start,
                offset + end,
                offset + expression_start,
                offset + expression_end,
            )
            for start, end, expression_start, expression_end
            in _return_literal_spans(code_segment, source_segment)
        )
        result.extend(_line_findings(number, offsets[number - 1], spans))
        depth = max(context_code.count("{") - context_code.count("}"), 0)
    return result


def _continuation_findings(
    code_lines: Sequence[str], source_lines: Sequence[str], offsets: Sequence[int]
) -> list[ColorLiteralFinding]:
    result: list[ColorLiteralFinding] = []
    pending = False
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        binding = _contexts._binding_match(code)
        if binding is not None:
            pending = not _contexts.BLOCK_EXPRESSION_RE.match(
                binding.group("expression")
            )
            continue
        stripped = code.strip()
        if not pending or not stripped:
            continue
        if stripped.startswith(_contexts.CONTINUATION_PREFIXES):
            expression_start, expression_end = _trimmed_bounds(source)
            spans = (
                (start, end, expression_start, expression_end)
                for start, end in _contexts._color_literal_spans(code, source)
            )
            result.extend(_line_findings(number, offsets[number - 1], spans))
            continue
        pending = False
    return result


def _direct_context_segments(
    code: str, source: str
) -> Iterable[tuple[str, str, int]]:
    binding = _contexts._binding_match(code)
    if binding is not None and not _contexts.BLOCK_EXPRESSION_RE.match(
        binding.group("expression")
    ):
        yield _expression_segment(code, source, binding, "expression")
    for match in _contexts.INLINE_BINDING_RE.finditer(code):
        if _contexts._is_color_name(match.group("name")):
            yield _inline_expression_segment(code, source, match)
    for match in _contexts.INLINE_PROPERTY_BINDING_RE.finditer(code):
        if match.group("type") == "color" or _contexts._is_color_name(
            match.group("name")
        ):
            yield _inline_expression_segment(code, source, match)
    for match in _contexts.CANVAS_ASSIGNMENT_RE.finditer(code):
        yield _expression_segment(code, source, match, "expression")
    yield from _color_stop_expression_segments(code, source)


def _line_offsets(lines: Sequence[str]) -> list[int]:
    offsets: list[int] = []
    current = 0
    for line in lines:
        offsets.append(current)
        current += len(line) + 1
    return offsets


def _deduplicated_findings(
    findings: Iterable[ColorLiteralFinding],
) -> tuple[ColorLiteralFinding, ...]:
    by_literal: dict[tuple[int, int, int], ColorLiteralFinding] = {}
    for finding in findings:
        key = (finding.line, finding.start, finding.end)
        previous = by_literal.get(key)
        current_width = finding.expression_end - finding.expression_start
        previous_width = (
            previous.expression_end - previous.expression_start
            if previous is not None else None
        )
        if previous_width is None or current_width < previous_width:
            by_literal[key] = finding
    return tuple(sorted(by_literal.values(), key=lambda item: (item.start, item.end)))


def color_literal_findings(
    code_lines: Sequence[str], source_lines: Sequence[str]
) -> tuple[ColorLiteralFinding, ...]:
    """Return style-context color literal locations. 返回样式上下文颜色字面量位置。"""
    offsets = _line_offsets(source_lines)
    result = _return_context_findings(code_lines, source_lines, offsets)
    result.extend(_continuation_findings(code_lines, source_lines, offsets))
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        for code_segment, source_segment, offset in _direct_context_segments(code, source):
            expression_start, expression_end = _trimmed_bounds(source_segment)
            spans = (
                (
                    offset + start,
                    offset + end,
                    offset + expression_start,
                    offset + expression_end,
                )
                for start, end in _contexts._color_literal_spans(
                    code_segment, source_segment
                )
            )
            result.extend(_line_findings(number, offsets[number - 1], spans))
    return _deduplicated_findings(result)
