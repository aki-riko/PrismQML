# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared SQL lexical boundaries. SQL 共享词法边界。"""

from __future__ import annotations

import re
from typing import Optional


_PARAMETER_PREFIXES = ":@$"
_SQLITE_SUFFIX_TERMINATORS = " \t\n\v\f\r\x00"
_SQLITE_BOM = "\ufeff"
_SIMPLE_NAMED_PARAMETER = re.compile(
    r":[A-Za-z_][A-Za-z0-9_]*"
    r"(?![A-Za-z0-9_$(]|::|[^\x00-\x7f])"
)


def _is_surrogate(char: str) -> bool:
    value = ord(char)
    return 0xD800 <= value <= 0xDFFF


def _is_identifier_char(char: str) -> bool:
    return (
        char in "_$"
        or char.isalnum()
        or (ord(char) >= 0x80 and not _is_surrogate(char))
    )


def _is_identifier_start(char: str) -> bool:
    return (
        char != _SQLITE_BOM
        and char != "$"
        and char not in "0123456789"
        and _is_identifier_char(char)
    )


def _identifier_span_end(sql: str, index: int, length: int) -> int:
    while index < length and _is_identifier_char(sql[index]):
        index += 1
    return index


def _digit_span_end(
    sql: str, index: int, length: int, hexadecimal: bool
) -> int:
    digits = "0123456789abcdefABCDEF" if hexadecimal else "0123456789"
    while index < length and (sql[index] in digits or sql[index] == "_"):
        index += 1
    return index


def _numeric_exponent_end(sql: str, index: int, length: int) -> int:
    if index >= length or sql[index] not in "eE":
        return index
    exponent = index + 1
    if exponent < length and sql[exponent] in "+-":
        exponent += 1
    if exponent >= length or sql[exponent] not in "0123456789":
        return index
    return _digit_span_end(sql, exponent, length, False)


def _numeric_span_end(sql: str, index: int, length: int) -> int:
    if sql[index] == ".":
        index = _digit_span_end(sql, index + 1, length, False)
        return _identifier_span_end(sql, index, length)
    is_hex = (
        index + 2 < length
        and sql[index] == "0"
        and sql[index + 1] in "xX"
        and sql[index + 2] in "0123456789abcdefABCDEF"
    )
    if is_hex:
        index = _digit_span_end(sql, index + 2, length, True)
        return _identifier_span_end(sql, index, length)
    index = _digit_span_end(sql, index, length, False)
    if index < length and sql[index] == ".":
        index = _digit_span_end(sql, index + 1, length, False)
    index = _numeric_exponent_end(sql, index, length)
    return _identifier_span_end(sql, index, length)


def _numbered_parameter_span_end(sql: str, index: int, length: int) -> int:
    index += 1
    while index < length and sql[index] in "0123456789":
        index += 1
    return index


def _bom_context_token_span(
    sql: str, index: int, length: int
) -> tuple[int, bool]:
    char = sql[index]
    if char == _SQLITE_BOM:
        return index + 1, False
    if char in "0123456789" or (
        char == "." and index + 1 < length
        and sql[index + 1] in "0123456789"
    ):
        return _numeric_span_end(sql, index, length), True
    if char == "?":
        return _numbered_parameter_span_end(sql, index, length), False
    if char == "#":
        return _extended_parameter_span(sql, index, length)
    if _is_identifier_start(char):
        return _identifier_span_end(sql, index, length), True
    return index + 1, False


def _dollar_starts_parameter(sql: str, start: int, index: int) -> bool:
    absorbed = False
    while start < index:
        start, absorbed = _bom_context_token_span(sql, start, index)
    return not absorbed


def _dollar_is_embedded(sql: str, start: int, index: int) -> bool:
    return not _dollar_starts_parameter(sql, start, index)


def _quoted_span_end(
    sql: str, index: int, length: int, closing: str, doubled: bool
) -> int:
    index += 1
    while index < length:
        if sql[index] != closing:
            index += 1
            continue
        if doubled and index + 1 < length and sql[index + 1] == closing:
            index += 2
            continue
        return index + 1
    return length


def _line_comment_span_end(sql: str, index: int, length: int) -> int:
    index += 2
    while index < length and sql[index] != "\n":
        index += 1
    return index


def _block_comment_span_end(sql: str, index: int, length: int) -> int:
    index += 2
    while index < length - 1:
        if sql[index] == "*" and sql[index + 1] == "/":
            return index + 2
        index += 1
    return length


def _parenthesized_suffix_span(
    sql: str, index: int, length: int
) -> tuple[int, bool]:
    index += 1
    while index < length:
        if sql[index] == ")":
            return index + 1, True
        if sql[index] in _SQLITE_SUFFIX_TERMINATORS or _is_surrogate(sql[index]):
            return index, False
        index += 1
    return length, False


def protected_sql_span_end(
    sql: str, index: int, length: int
) -> Optional[int]:
    char = sql[index]
    if char in "'\"`":
        return _quoted_span_end(sql, index, length, char, True)
    if char == "[":
        return _quoted_span_end(sql, index, length, "]", False)
    if char == "-" and index + 1 < length and sql[index + 1] == "-":
        return _line_comment_span_end(sql, index, length)
    if char == "/" and index + 1 < length and sql[index + 1] == "*":
        return _block_comment_span_end(sql, index, length)
    return None


def _extended_parameter_span(
    sql: str, index: int, length: int
) -> tuple[int, bool]:
    end, identifier_count = index + 1, 0
    while end < length:
        if _is_identifier_char(sql[end]):
            identifier_count += 1
            end += 1
            continue
        if sql[end] == ":" and end + 1 < length and sql[end + 1] == ":":
            end += 2
            continue
        if sql[end] == "(" and identifier_count:
            return _parenthesized_suffix_span(sql, end, length)
        break
    return end, identifier_count > 0


def named_parameter_span(
    sql: str, index: int, length: int, scan_start: int
) -> tuple[int, bool]:
    if index >= length or sql[index] not in _PARAMETER_PREFIXES:
        return min(index + 1, length), False
    if sql[index] == "$" and _dollar_is_embedded(sql, scan_start, index):
        return _identifier_span_end(sql, index, length), False
    match = _SIMPLE_NAMED_PARAMETER.match(sql, index)
    if match is not None:
        return match.end(), True
    return _extended_parameter_span(sql, index, length)
