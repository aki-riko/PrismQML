# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Keyset predicate construction. Keyset 分页谓词构造。"""

from __future__ import annotations

from typing import Callable, Optional


def _normalize_cursor_directions(
    cursor_columns: list[str],
    cursor_directions: list[str],
) -> list[str]:
    directions = cursor_directions or ["ASC"] * len(cursor_columns)
    if len(directions) != len(cursor_columns):
        raise ValueError("cursor_directions 长度必须与 cursor_columns 一致")
    normalized = [str(direction).upper() for direction in directions]
    if any(direction not in ("ASC", "DESC") for direction in normalized):
        raise ValueError("cursor_directions 只能包含 ASC/DESC")
    return normalized


def _build_row_value_predicate(
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    operator: str,
) -> tuple[str, list]:
    columns = ", ".join(cursor_columns)
    placeholders = ", ".join(["? COLLATE BINARY"] * len(cursor_columns))
    predicate = f"({columns}) {operator} ({placeholders})"
    return predicate, list(params) + list(cursor_values)


def _build_null_branch_predicate(
    cursor_values: list,
    cursor_columns: list[str],
    nullable_index: int,
) -> tuple[str, list]:
    parts = []
    values = []
    for prefix in range(nullable_index):
        sql, params = _cursor_column_equal(
            cursor_columns[prefix], cursor_values[prefix]
        )
        parts.append(sql)
        values.extend(params)
    parts.append(f"{cursor_columns[nullable_index]} IS NULL")
    return "(" + " AND ".join(parts) + ")", values


def _wrap_keyset_branch(head: str, predicate: str) -> str:
    return (
        f"SELECT * FROM ({head}) AS _prism_keyset_source "
        f"WHERE {predicate}"
    )


def _build_desc_nullable_union(
    head: str,
    tail: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    nullable_index: int,
) -> tuple[str, list]:
    tuple_sql, tuple_params = _build_row_value_predicate(
        [], cursor_values, cursor_columns, "<"
    )
    null_sql, null_params = _build_null_branch_predicate(
        cursor_values, cursor_columns, nullable_index
    )
    branches = [
        _wrap_keyset_branch(head, tuple_sql),
        _wrap_keyset_branch(head, null_sql),
    ]
    compound = " UNION ALL ".join(branches)
    sql = f"SELECT * FROM ({compound}) AS _prism_keyset_page{tail}"
    new_params = list(params) + tuple_params + list(params) + null_params
    return sql, new_params


def _cursor_column_equal(column: str, value) -> tuple[str, list]:
    if value is None:
        return f"{column} IS NULL", []
    return f"{column} = ? COLLATE BINARY", [value]


def _cursor_column_after(
    column: str,
    value,
    direction: str,
) -> tuple[str, list]:
    if direction == "DESC":
        if value is None:
            return "0", []
        return f"({column} < ? COLLATE BINARY OR {column} IS NULL)", [value]
    if value is None:
        return f"{column} IS NOT NULL", []
    return f"{column} > ? COLLATE BINARY", [value]


def _build_expanded_keyset_predicate(
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    directions: list[str],
) -> tuple[str, list]:
    clauses = []
    new_params = list(params)
    for index, column in enumerate(cursor_columns):
        level_parts = []
        level_params: list = []
        for prefix in range(index):
            sql, values = _cursor_column_equal(
                cursor_columns[prefix], cursor_values[prefix]
            )
            level_parts.append(sql)
            level_params.extend(values)
        sql, values = _cursor_column_after(
            column, cursor_values[index], directions[index]
        )
        level_parts.append(sql)
        level_params.extend(values)
        clauses.append("(" + " AND ".join(level_parts) + ")")
        new_params.extend(level_params)
    return "(" + " OR ".join(clauses) + ")", new_params


def _build_guarded_expanded_query(
    head: str,
    tail: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    directions: list[str],
) -> tuple[str, list]:
    operator = "<=" if directions[0] == "DESC" else ">="
    guard = f"{cursor_columns[0]} {operator} ? COLLATE BINARY"
    predicate, predicate_params = _build_expanded_keyset_predicate(
        [], cursor_values, cursor_columns, directions
    )
    sql = _wrap_keyset_branch(head, f"({guard} AND {predicate})") + tail
    new_params = list(params) + [cursor_values[0]] + predicate_params
    return sql, new_params


def _build_uniform_keyset_query(
    head: str,
    tail: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    directions: list[str],
    nullable_cursor_index: Optional[int],
) -> tuple[str, list]:
    all_desc = all(direction == "DESC" for direction in directions)
    if all_desc and nullable_cursor_index is not None:
        if not 0 <= nullable_cursor_index < len(cursor_columns) - 1:
            raise ValueError("nullable cursor 必须是非末 cursor 列")
        return _build_desc_nullable_union(
            head,
            tail,
            params,
            cursor_values,
            cursor_columns,
            nullable_cursor_index,
        )
    operator = "<" if all_desc else ">"
    predicate, predicate_params = _build_row_value_predicate(
        [], cursor_values, cursor_columns, operator
    )
    sql = _wrap_keyset_branch(head, predicate) + tail
    return sql, list(params) + predicate_params


def _try_build_guarded_subquery(
    head: str,
    tail: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    directions: list[str],
    nullable_cursor_index: Optional[int],
    source_has_subquery: Callable[[str], bool],
) -> Optional[tuple[str, list]]:
    if (
        not source_has_subquery(head)
        or nullable_cursor_index == 0
        or not cursor_values
        or cursor_values[0] is None
    ):
        return None
    return _build_guarded_expanded_query(
        head, tail, params, cursor_values, cursor_columns, directions
    )


def build_keyset_query(
    head: str, tail: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    cursor_directions: list[str],
    nullable_cursor_index: Optional[int],
    source_has_subquery: Callable[[str], bool],
) -> tuple[str, list]:
    """Build one null-aware keyset query. 构造支持空值的 keyset 查询。"""
    directions = _normalize_cursor_directions(cursor_columns, cursor_directions)
    has_null_cursor = any(value is None for value in cursor_values)
    all_desc = all(direction == "DESC" for direction in directions)
    all_asc = all(direction == "ASC" for direction in directions)
    guarded = _try_build_guarded_subquery(
        head, tail, params, cursor_values, cursor_columns, directions,
        nullable_cursor_index, source_has_subquery,
    )
    if guarded is not None:
        return guarded
    if (all_desc or all_asc) and not has_null_cursor:
        return _build_uniform_keyset_query(
            head, tail, params, cursor_values, cursor_columns, directions,
            nullable_cursor_index,
        )
    predicate, predicate_params = _build_expanded_keyset_predicate(
        [], cursor_values, cursor_columns, directions
    )
    sql = _wrap_keyset_branch(head, predicate) + tail
    return sql, list(params) + predicate_params
