# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

from __future__ import annotations

import re
from typing import Optional, Union

from ._sql_lexing import (
    _SIMPLE_NAMED_PARAMETER,
    named_parameter_span,
    protected_sql_span_end,
)
from ._sql_keyset_builder import build_keyset_query


_SIMPLE_ORDER_TERM = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+COLLATE\s+BINARY)?"
    r"(?:\s+(ASC|DESC))?\s*$",
    re.IGNORECASE,
)
_FORBIDDEN_KEYSET_SOURCE = re.compile(
    r"\b(?:UNION|INTERSECT|EXCEPT|HAVING)\b|\bGROUP\s+BY\b",
    re.IGNORECASE,
)
_WINDOW_KEYWORD = re.compile(r"\b(?:WINDOW|OVER)\b", re.IGNORECASE)
_NUMBERED_PLACEHOLDER = re.compile(r"\?\d+")
_SELECT_KEYWORD = re.compile(r"\bSELECT\b", re.IGNORECASE)
_NAMED_SQL_SPECIALS = "'\"`[-/:@$"
_SIMPLE_IN_SUBQUERY = re.compile(
    r"^\s*SELECT\s+[A-Za-z_][A-Za-z0-9_]*\s+"
    r"FROM\s+[A-Za-z_][A-Za-z0-9_]*\s+WHERE\s+\S[\s\S]*$",
    re.IGNORECASE,
)
_FORBIDDEN_IN_SUBQUERY = re.compile(
    r"\b(?:WITH|DISTINCT|UNION|INTERSECT|EXCEPT|HAVING|LIMIT|OFFSET|"
    r"WINDOW|OVER)\b|\b(?:GROUP|ORDER)\s+BY\b",
    re.IGNORECASE,
)


def _copy_protected_span(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    end = protected_sql_span_end(sql, index, length)
    if end is None:
        out.append(sql[index])
        return index + 1
    out.append(sql[index:end])
    return end


def _copy_single_quoted(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    return _copy_protected_span(sql, index, length, out)


def _copy_double_quoted(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    return _copy_protected_span(sql, index, length, out)


def _copy_backtick_quoted(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    return _copy_protected_span(sql, index, length, out)


def _copy_bracket_quoted(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    return _copy_protected_span(sql, index, length, out)


def _copy_line_comment(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    return _copy_protected_span(sql, index, length, out)


def _copy_block_comment(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    return _copy_protected_span(sql, index, length, out)


def _copy_plain_sql(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    start = index
    while index < length and sql[index] not in _NAMED_SQL_SPECIALS:
        index += 1
    if index > start:
        out.append(sql[start:index])
    return index


def _copy_protected_sql(
    sql: str, index: int, length: int, out: list[str]
) -> int:
    char = sql[index]
    if char == "'":
        return _copy_single_quoted(sql, index, length, out)
    if char == '"':
        return _copy_double_quoted(sql, index, length, out)
    if char == "`":
        return _copy_backtick_quoted(sql, index, length, out)
    if char == "[":
        return _copy_bracket_quoted(sql, index, length, out)
    if char == "-" and index + 1 < length and sql[index + 1] == "-":
        return _copy_line_comment(sql, index, length, out)
    if char == "/" and index + 1 < length and sql[index + 1] == "*":
        return _copy_block_comment(sql, index, length, out)
    out.append(char)
    return index + 1


def _copy_unresolved_parameter(
    sql: str, index: int, end: int, out: list[str]
) -> int:
    out.append(sql[index:end])
    return end


def _normalize_dict_params(sql: str, params: dict) -> tuple[str, list]:
    ordered, out = [], []
    index, length, scan_start = 0, len(sql), 0
    while index < length:
        if sql[index] not in _NAMED_SQL_SPECIALS:
            index = _copy_plain_sql(sql, index, length, out)
            continue
        if sql[index] not in ":@$":
            scan_start = index = _copy_protected_sql(sql, index, length, out)
            continue
        match = _SIMPLE_NAMED_PARAMETER.match(sql, index)
        end, is_parameter = (
            (match.end(), True) if match is not None
            else named_parameter_span(sql, index, length, scan_start)
        )
        name = sql[index + 1:end] if is_parameter else None
        if name is None or name not in params:
            scan_start = index = _copy_unresolved_parameter(
                sql, index, end, out
            )
            continue
        out.append("?")
        ordered.append(params[name])
        scan_start = index = end
        plain_start = index
        while index < length and sql[index] not in _NAMED_SQL_SPECIALS:
            index += 1
        if index > plain_start:
            out.append(sql[plain_start:index])
    return "".join(out), ordered


def normalize_one(
    sql: str,
    params: Optional[Union[list, tuple, dict]],
) -> tuple[str, list]:
    """Normalize one SQL fragment from named params to positional params."""
    if params is None:
        return sql, []
    if isinstance(params, (list, tuple)):
        return sql, list(params)
    if isinstance(params, dict):
        return _normalize_dict_params(sql, params)
    raise TypeError(f"params must be list/tuple/dict/None, got {type(params)}")


def strip_strings_and_comments(sql: str) -> str:
    """Mask SQL protected spans with spaces for structural scanning."""
    result = list(sql)
    index, length = 0, len(sql)
    while index < length:
        end = protected_sql_span_end(sql, index, length)
        if end is None:
            index += 1
            continue
        result[index:end] = [" "] * (end - index)
        index = end
    return "".join(result)


def find_top_level_order_by(sql: str) -> int:
    """Find the top-level ORDER BY clause start."""
    masked = strip_strings_and_comments(sql)
    upper = masked.upper()
    i = len(masked) - 1
    depth = 0
    while i >= 0:
        ch = masked[i]
        if ch == ")":
            depth += 1
        elif ch == "(":
            depth -= 1
        elif depth == 0 and i + 10 <= len(masked) and upper[i:i + 10] == " ORDER BY ":
            return i
        i -= 1
    return -1


def _top_level_sql(sql: str) -> str:
    """Mask nested SQL while preserving top-level tokens."""
    masked = strip_strings_and_comments(sql)
    result = list(masked)
    depth = 0
    for index, char in enumerate(masked):
        if char == "(":
            result[index] = " "
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
            result[index] = " "
        elif depth:
            result[index] = " "
    return "".join(result)


def _parenthesized_ranges(masked_sql: str) -> list[tuple[int, int]]:
    stack: list[int] = []
    ranges: list[tuple[int, int]] = []
    for index, char in enumerate(masked_sql):
        if char == "(":
            stack.append(index)
        elif char == ")":
            if not stack:
                raise ValueError("keyset sql 括号不匹配")
            ranges.append((stack.pop(), index))
    if stack:
        raise ValueError("keyset sql 括号不匹配")
    return ranges


def _validate_simple_in_subquery(masked: str, top_level: str) -> None:
    candidates = []
    for start, end in _parenthesized_ranges(masked):
        inner = masked[start + 1:end]
        if re.match(r"\s*SELECT\b", inner, re.IGNORECASE):
            candidates.append((start, inner))
    if len(candidates) != 1:
        raise ValueError("keyset sql 最多支持一个简单 IN (SELECT ...) 子查询")
    start, inner = candidates[0]
    prefix = masked[:start].rstrip()
    where_match = re.search(r"\bWHERE\b", top_level, re.IGNORECASE)
    if where_match is None or start < where_match.end():
        raise ValueError("keyset 子查询只能位于顶层 WHERE")
    if re.search(r"\bNOT\s+IN\s*$", prefix, re.IGNORECASE):
        raise ValueError("keyset sql 不支持 NOT IN 子查询")
    if re.search(r"\bIN\s*$", prefix, re.IGNORECASE) is None:
        raise ValueError("keyset sql 只支持简单 IN (SELECT ...) 子查询")
    if "(" in inner or ")" in inner:
        raise ValueError("keyset IN 子查询不支持继续嵌套")
    if _FORBIDDEN_IN_SUBQUERY.search(inner) or not _SIMPLE_IN_SUBQUERY.fullmatch(inner):
        raise ValueError("keyset IN 子查询仅支持 SELECT 单列 FROM 单表 WHERE 条件")


def _validate_keyset_source(head: str) -> None:
    masked = strip_strings_and_comments(head)
    top_level = _top_level_sql(head)
    if re.match(r"\s*SELECT\b", top_level, re.IGNORECASE) is None:
        raise ValueError("keyset sql 必须是简单顶层 SELECT，不支持 WITH/CTE")
    if _WINDOW_KEYWORD.search(masked):
        raise ValueError("keyset sql 不支持 WINDOW/OVER；请改用 OFFSET")
    if _FORBIDDEN_KEYSET_SOURCE.search(top_level):
        raise ValueError(
            "keyset sql 不支持 compound/GROUP BY/HAVING/WINDOW；请改用 OFFSET"
        )
    if _NUMBERED_PLACEHOLDER.search(masked):
        raise ValueError("keyset sql 仅支持匿名 ? 占位符，不支持 ?NNN")
    if _has_named_placeholder(head):
        raise ValueError("keyset sql 的命名占位符必须先通过 dict params 归一化")
    select_count = len(_SELECT_KEYWORD.findall(masked))
    if select_count == 2:
        _validate_simple_in_subquery(masked, top_level)
    elif select_count != 1:
        raise ValueError("keyset sql 最多支持一个简单 IN (SELECT ...) 子查询")


def _source_has_subquery(head: str) -> bool:
    masked = strip_strings_and_comments(head)
    return len(_SELECT_KEYWORD.findall(masked)) > 1


def _has_named_placeholder(sql: str) -> bool:
    length = len(sql)
    index, scan_start = 0, 0
    while index < length:
        is_prefix = sql[index] in ":@$"
        end, is_parameter = (
            named_parameter_span(sql, index, length, scan_start)
            if is_prefix else (index, False)
        )
        if is_parameter:
            return True
        if is_prefix:
            scan_start = index = end
            continue
        end = protected_sql_span_end(sql, index, length)
        if end is not None:
            scan_start = index = end
            continue
        index += 1
    return False


def _parse_keyset_order(tail: str) -> list[tuple[str, str]]:
    clause = tail[len(" ORDER BY "):]
    terms: list[tuple[str, str]] = []
    for segment in clause.split(","):
        match = _SIMPLE_ORDER_TERM.fullmatch(segment)
        if match is None:
            raise ValueError(
                "keyset ORDER BY 仅支持未限定输出列、可选 COLLATE BINARY "
                "及 ASC/DESC，不支持函数、其他 COLLATE、NULLS、LIMIT/OFFSET"
            )
        terms.append((match.group(1), (match.group(2) or "ASC").upper()))
    return terms


def validate_keyset_query(
    sql: str,
    cursor_columns: list[str],
    cursor_directions: Optional[list[str]] = None,
) -> list[str]:
    """Validate the deliberately strict high-performance keyset contract."""
    head, tail = _split_ordered_sql(sql)
    _validate_keyset_source(head)
    terms = _parse_keyset_order(tail)
    normalized_columns = [column.casefold() for column in cursor_columns]
    if len(set(normalized_columns)) != len(normalized_columns):
        raise ValueError("cursor_columns 必须互不重复")
    if len(terms) != len(cursor_columns):
        raise ValueError("keyset ORDER BY 必须与 cursor_columns 完全一致")
    ordered_columns = [column.casefold() for column, _ in terms]
    if ordered_columns != normalized_columns:
        raise ValueError("keyset ORDER BY 必须按 cursor_columns 原顺序排列")
    directions = [direction for _, direction in terms]
    if cursor_directions is not None:
        configured = [str(direction).upper() for direction in cursor_directions]
        if len(configured) != len(directions) or any(
            direction not in ("ASC", "DESC") for direction in configured
        ):
            raise ValueError("cursor_directions 只能包含匹配 ORDER BY 的 ASC/DESC")
        if configured != directions:
            raise ValueError("cursor_directions 必须与 SQL ORDER BY 完全一致")
    return directions


def normalize_keyset_order(
    sql: str,
    cursor_columns: list[str],
    cursor_directions: Optional[list[str]] = None,
) -> str:
    """Rewrite the validated ORDER BY to explicit SQLite BINARY semantics."""
    head, _tail = _split_ordered_sql(sql)
    directions = validate_keyset_query(
        sql, cursor_columns, cursor_directions
    )
    terms = [
        f"{column} COLLATE BINARY {direction}"
        for column, direction in zip(cursor_columns, directions)
    ]
    return f"{head} ORDER BY {', '.join(terms)}"


def resolve_nullable_cursor_index(
    cursor_columns: list[str],
    nullable_cursor_column: Optional[str],
) -> Optional[int]:
    """Resolve the sole cursor column whose schema may allow NULL."""
    if nullable_cursor_column is None:
        return len(cursor_columns) - 2 if len(cursor_columns) > 1 else None
    if nullable_cursor_column == "":
        return None
    normalized = [column.casefold() for column in cursor_columns]
    try:
        index = normalized.index(nullable_cursor_column.casefold())
    except ValueError as exc:
        raise ValueError("nullable_cursor_column 必须属于 cursor_columns") from exc
    if index == len(cursor_columns) - 1:
        raise ValueError("最终 cursor tie-breaker 必须声明为 UNIQUE NOT NULL")
    return index


def _split_ordered_sql(sql: str) -> tuple[str, str]:
    order_idx = find_top_level_order_by(sql)
    if order_idx < 0:
        raise ValueError("setQuery 的 sql 必须包含 ORDER BY 子句以使用 keyset 分页")
    return sql[:order_idx], sql[order_idx:]


def inject_keyset_predicate(
    sql: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    cursor_directions: list[str],
    nullable_cursor_index: Optional[int] = None,
) -> tuple[str, list]:
    """Insert a null-aware keyset predicate before ORDER BY."""
    head, tail = _split_ordered_sql(sql)
    return build_keyset_query(
        head,
        tail,
        params,
        cursor_values,
        cursor_columns,
        cursor_directions,
        nullable_cursor_index,
        _source_has_subquery,
    )
