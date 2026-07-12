# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Resolve direct JavaScript expression result roles. 解析 JavaScript 表达式直接结果角色。"""

from __future__ import annotations


CLOSING_OPENERS = {"}": "{", "]": "[", ")": "("}
CONTINUATION_SUFFIXES = (
    "?", ":", ",", ".", "+", "-", "*", "/", "%", "=", "&", "|",
    "^", "<", ">", "!", "&&", "||", "??",
)
CONTINUATION_LEADS = frozenset("([.?+-*/%&|^<>=!:,")
CONTINUATION_WORDS = frozenset({"in", "instanceof"})
PREFIX_WORDS = frozenset({"await", "yield"})


def _next_nonspace_index(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _next_word(text: str, start: int) -> str:
    end = start
    while end < len(text) and (text[end].isalnum() or text[end] in "_$"):
        end += 1
    return text[start:end]


def _previous_word(text: str) -> str:
    end = len(text) - 1
    while end >= 0 and text[end].isspace():
        end -= 1
    start = end
    while start >= 0 and (text[start].isalnum() or text[start] in "_$"):
        start -= 1
    return text[start + 1:end + 1]


def _line_continues(text: str, line_start: int, newline: int) -> bool:
    line = text[line_start:newline].rstrip()
    if not line:
        return True
    next_index = _next_nonspace_index(text, newline + 1)
    next_continues = next_index < len(text) and (
        text[next_index] in CONTINUATION_LEADS
        or _next_word(text, next_index) in CONTINUATION_WORDS
    )
    return (
        line.endswith(CONTINUATION_SUFFIXES)
        or next_continues
        or _previous_word(line) in PREFIX_WORDS
    )


def expression_end(
    text: str,
    start: int,
    limit: int,
    pair_ends: dict[str, dict[int, int]],
    *,
    comma_boundary: bool,
) -> int:
    """Return the direct expression boundary. 返回直接表达式边界。"""
    index = start
    line_start = start
    while index < limit:
        char = text[index]
        balanced_end = pair_ends.get(char, {}).get(index)
        if balanced_end is not None and balanced_end <= limit:
            last_newline = text.rfind("\n", index, balanced_end)
            line_start = last_newline + 1 if last_newline >= 0 else line_start
            index = balanced_end
            continue
        if char in CLOSING_OPENERS or char == ";":
            return index
        if comma_boundary and char == ",":
            return index
        if char == "\n":
            if not _line_continues(text, line_start, index):
                return index
            line_start = index + 1
        index += 1
    return limit


def _trim_range(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _starts_word(text: str, start: int, end: int, word: str) -> bool:
    word_end = start + len(word)
    return (
        text.startswith(word, start, end)
        and (word_end >= end or not (text[word_end].isalnum() or text[word_end] in "_$"))
    )


def _normalize_result_range(
    text: str,
    start: int,
    end: int,
    paren_ends: dict[int, int],
) -> tuple[int, int]:
    while True:
        start, end = _trim_range(text, start, end)
        if start < end and text[start] == "(" and paren_ends.get(start) == end:
            start, end = start + 1, end - 1
            continue
        if _starts_word(text, start, end, "await"):
            start += len("await")
            continue
        return start, end


def _conditional_parts(
    text: str,
    start: int,
    end: int,
    pair_ends: dict[str, dict[int, int]],
) -> tuple[int, int] | None:
    question = None
    depth = 0
    index = start
    while index < end:
        if (jump := pair_ends.get(text[index], {}).get(index)) is not None:
            index = jump
            continue
        if text.startswith(("??", "?."), index):
            index += 2
            continue
        if text[index] == "?":
            question = index if question is None else question
            depth += 1
        elif text[index] == ":" and depth:
            depth -= 1
            if depth == 0 and question is not None:
                return question, index
        index += 1
    return None


def _logical_operand(
    text: str,
    start: int,
    end: int,
    array_start: int,
    array_end: int,
    pair_ends: dict[str, dict[int, int]],
) -> tuple[int, int] | None:
    segment_start = start
    found = False
    index = start
    while index < end - 1:
        if (jump := pair_ends.get(text[index], {}).get(index)) is not None:
            index = jump
            continue
        operator = text[index:index + 2]
        if operator in {"||", "&&", "??"} and text[index + 2:index + 3] != "=":
            found = True
            if segment_start <= array_start and array_end <= index:
                return segment_start, index
            segment_start = index + 2
            index += 2
            continue
        index += 1
    if found and segment_start <= array_start and array_end <= end:
        return segment_start, end
    return None


def direct_result_path(
    text: str,
    expression_start: int,
    expression_end: int,
    array_start: int,
    array_end: int,
    pair_ends: dict[str, dict[int, int]],
) -> bool:
    """Return whether an array is a direct result branch. 返回数组是否为直接结果分支。"""
    start, end = expression_start, expression_end
    while True:
        start, end = _normalize_result_range(text, start, end, pair_ends["("])
        if (start, end) == (array_start, array_end):
            return True
        if conditional := _conditional_parts(text, start, end, pair_ends):
            question, colon = conditional
            if question < array_start and array_end <= colon:
                start, end = question + 1, colon
                continue
            if colon < array_start and array_end <= end:
                start = colon + 1
                continue
            return False
        logical = _logical_operand(
            text, start, end, array_start, array_end, pair_ends
        )
        if logical is None or logical == (start, end):
            return False
        start, end = logical
