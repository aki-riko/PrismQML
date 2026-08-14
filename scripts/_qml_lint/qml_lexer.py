# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Minimal QML/JavaScript lexical masking. QML/JavaScript 最小词法遮罩。"""

from __future__ import annotations

from collections.abc import Sequence


_REGEX_PREFIX_CHARS = frozenset("([{:;,}=!?&|+-*%^~<>")
_REGEX_PREFIX_WORDS = frozenset(
    {
        "await", "case", "delete", "do", "else", "instanceof", "return",
        "throw", "typeof", "void", "yield",
    }
)
_CONTROL_CONDITION_WORDS = frozenset({"catch", "for", "if", "while", "with"})
_ECMASCRIPT_LINEBREAK_CHARS = frozenset("\r\n\u2028\u2029")
_SOURCE_LINEBREAK_CHARS = frozenset("\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029")


def _blank(segment: str) -> str:
    return "".join(
        char if char in _SOURCE_LINEBREAK_CHARS else " " for char in segment
    )


def _marked_value_blank(segment: str, marker: str) -> str:
    result = list(_blank(segment))
    for index in range(len(segment) - 1, -1, -1):
        if segment[index] not in _SOURCE_LINEBREAK_CHARS:
            result[index] = marker
            break
    return "".join(result)


def _quoted_end(text: str, start: int, quote: str) -> int:
    index = start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == quote:
            return index + 1
        index += 1
    return len(text)


def _previous_nonspace(text: Sequence[str], start: int) -> int:
    index = start - 1
    while (
        index >= 0
        and text[index].isspace()
        and text[index] not in _ECMASCRIPT_LINEBREAK_CHARS
    ):
        index -= 1
    return index


def _previous_word(text: Sequence[str], end: int) -> str:
    start = end
    while start >= 0 and (text[start].isalnum() or text[start] in "_$"):
        start -= 1
    return "".join(text[start + 1 : end + 1])


def _matching_open_paren(text: Sequence[str], close: int) -> int | None:
    depth = 0
    for index in range(close, -1, -1):
        if text[index] == ")":
            depth += 1
        elif text[index] == "(":
            depth -= 1
            if depth == 0:
                return index
    return None


def _follows_control_condition(text: Sequence[str], previous: int) -> bool:
    if text[previous] != ")":
        return False
    opening = _matching_open_paren(text, previous)
    if opening is None:
        return False
    word_end = _previous_nonspace(text, opening)
    return word_end >= 0 and _previous_word(text, word_end) in _CONTROL_CONDITION_WORDS


def _is_regex_start(text: Sequence[str], start: int) -> bool:
    previous = _previous_nonspace(text, start)
    if previous < 0 or text[previous] in _ECMASCRIPT_LINEBREAK_CHARS:
        return True
    if _follows_control_condition(text, previous):
        return True
    if text[previous] in _REGEX_PREFIX_CHARS:
        return True
    if text[previous].isalnum() or text[previous] in "_$":
        return _previous_word(text, previous) in _REGEX_PREFIX_WORDS
    return False


def _regex_end(text: str, start: int) -> int | None:
    index = start + 1
    in_character_class = False
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char in _ECMASCRIPT_LINEBREAK_CHARS:
            return None
        if char == "[":
            in_character_class = True
        elif char == "]":
            in_character_class = False
        elif char == "/" and not in_character_class:
            index += 1
            while index < len(text) and text[index].isalpha():
                index += 1
            return index
        index += 1
    return None


def _line_comment_end(text: str, start: int) -> int:
    index = start + 2
    while index < len(text) and text[index] not in _ECMASCRIPT_LINEBREAK_CHARS:
        index += 1
    return index


def _lexeme(
    text: str, start: int, context_text: Sequence[str] | None = None
) -> tuple[int, str] | None:
    if text.startswith("//", start):
        return _line_comment_end(text, start), "comment"
    if text.startswith("/*", start):
        end = text.find("*/", start + 2)
        return (len(text) if end < 0 else end + 2, "comment")
    regex_context = context_text if context_text is not None else text
    regex_start = len(context_text) if context_text is not None else start
    if text[start] == "/" and _is_regex_start(regex_context, regex_start):
        if (end := _regex_end(text, start)) is not None:
            return end, "regex"
    if text[start] in {'"', "'", "`"}:
        return _quoted_end(text, start, text[start]), "string"
    return None


def sanitize_qml(
    text: str, *, mask_strings: bool, mark_values: bool = False
) -> str:
    result: list[str] = []
    context_result: list[str] = []
    index = 0
    while index < len(text):
        context_text = context_result if text[index] == "/" else None
        lexeme = _lexeme(text, index, context_text)
        if lexeme is None:
            result.append(text[index])
            context_result.append(text[index])
            index += 1
            continue
        end, kind = lexeme
        segment = text[index:end]
        context_result.extend(_blank(segment))
        if mark_values and kind in {"regex", "string"}:
            result.append(_marked_value_blank(segment, "v"))
        else:
            result.append(_blank(segment) if kind != "string" or mask_strings else segment)
        index = end
    return "".join(result)


def line_comment_lines(text: str) -> frozenset[int]:
    """Return source lines where the lexer sees a real // comment. 返回真实行注释行。"""
    result: set[int] = set()
    context_result: list[str] = []
    index = 0
    line = 1
    while index < len(text):
        context_text = context_result if text[index] == "/" else None
        lexeme = _lexeme(text, index, context_text)
        if lexeme is None:
            context_result.append(text[index])
            if text[index] == "\n":
                line += 1
            index += 1
            continue
        end, kind = lexeme
        segment = text[index:end]
        if kind == "comment" and text.startswith("//", index):
            result.add(line)
        context_result.extend(_blank(segment))
        line += segment.count("\n")
        index = end
    return frozenset(result)
