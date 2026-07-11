# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Minimal QML/JavaScript lexical masking. QML/JavaScript 最小词法遮罩。"""

from __future__ import annotations


_REGEX_PREFIX_CHARS = frozenset("([{:;,=!?&|+-*%^~<>")
_REGEX_PREFIX_WORDS = frozenset(
    {"await", "case", "delete", "instanceof", "return", "throw", "typeof", "void", "yield"}
)


def _blank(segment: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in segment)


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


def _previous_nonspace(text: str, start: int) -> int:
    index = start - 1
    while index >= 0 and text[index] in " \t\r":
        index -= 1
    return index


def _previous_word(text: str, end: int) -> str:
    start = end
    while start >= 0 and (text[start].isalnum() or text[start] in "_$"):
        start -= 1
    return text[start + 1 : end + 1]


def _is_regex_start(text: str, start: int) -> bool:
    previous = _previous_nonspace(text, start)
    if previous < 0 or text[previous] == "\n":
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
        if char == "\n":
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


def _lexeme(text: str, start: int) -> tuple[int, str] | None:
    if text.startswith("//", start):
        end = text.find("\n", start)
        return (len(text) if end < 0 else end, "comment")
    if text.startswith("/*", start):
        end = text.find("*/", start + 2)
        return (len(text) if end < 0 else end + 2, "comment")
    if text[start] == "/" and _is_regex_start(text, start):
        if (end := _regex_end(text, start)) is not None:
            return end, "regex"
    if text[start] in {'"', "'", "`"}:
        return _quoted_end(text, start, text[start]), "string"
    return None


def sanitize_qml(text: str, *, mask_strings: bool) -> str:
    result: list[str] = []
    index = 0
    while index < len(text):
        lexeme = _lexeme(text, index)
        if lexeme is None:
            result.append(text[index])
            index += 1
            continue
        end, kind = lexeme
        segment = text[index:end]
        result.append(_blank(segment) if kind != "string" or mask_strings else segment)
        index = end
    return "".join(result)
