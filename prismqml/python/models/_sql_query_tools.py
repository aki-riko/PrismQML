# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

from __future__ import annotations

import re
from typing import Optional, Union


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
        ordered: list = []
        out: list[str] = []
        i = 0
        n = len(sql)
        while i < n:
            ch = sql[i]
            if ch == "'":
                out.append(ch)
                i += 1
                while i < n:
                    if sql[i] == "'":
                        if i + 1 < n and sql[i + 1] == "'":
                            out.append("''")
                            i += 2
                            continue
                        out.append("'")
                        i += 1
                        break
                    out.append(sql[i])
                    i += 1
                continue
            if ch == '"':
                out.append(ch)
                i += 1
                while i < n and sql[i] != '"':
                    out.append(sql[i])
                    i += 1
                if i < n:
                    out.append('"')
                    i += 1
                continue
            if ch == "-" and i + 1 < n and sql[i + 1] == "-":
                while i < n and sql[i] != "\n":
                    out.append(sql[i])
                    i += 1
                continue
            if ch == "/" and i + 1 < n and sql[i + 1] == "*":
                out.append("/")
                out.append("*")
                i += 2
                while i < n - 1 and not (sql[i] == "*" and sql[i + 1] == "/"):
                    out.append(sql[i])
                    i += 1
                if i < n - 1:
                    out.append("*")
                    out.append("/")
                    i += 2
                continue
            if ch == ":" and i + 1 < n and (
                sql[i + 1].isalpha() or sql[i + 1] == "_"
            ):
                j = i + 1
                while j < n and (sql[j].isalnum() or sql[j] == "_"):
                    j += 1
                name = sql[i + 1 : j]
                if name in params:
                    out.append("?")
                    ordered.append(params[name])
                    i = j
                    continue
            out.append(ch)
            i += 1
        return "".join(out), ordered
    raise TypeError(f"params must be list/tuple/dict/None, got {type(params)}")


def normalize_sql(
    sql: str,
    count_sql: str,
    params: Optional[Union[list, tuple, dict]],
) -> tuple[str, str, list, list]:
    """Normalize main and count SQL while preserving each placeholder order."""
    new_sql, main_ordered = normalize_one(sql, params)
    new_count_sql, count_ordered = normalize_one(count_sql, params)
    return new_sql, new_count_sql, main_ordered, count_ordered


def parse_cursor_directions(sql: str, cursor_columns: list[str]) -> list[str]:
    """Parse ASC/DESC direction for each cursor column from ORDER BY."""
    upper = sql.upper()
    order_idx = upper.rfind(" ORDER BY ")
    if order_idx < 0:
        return ["ASC"] * len(cursor_columns)
    order_clause = sql[order_idx + len(" ORDER BY "):]
    for kw in (" LIMIT ", " OFFSET "):
        cut = order_clause.upper().find(kw)
        if cut >= 0:
            order_clause = order_clause[:cut]

    depth = 0
    seg_start = 0
    segments: list[str] = []
    for i, ch in enumerate(order_clause):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            segments.append(order_clause[seg_start:i])
            seg_start = i + 1
    segments.append(order_clause[seg_start:])

    seg_to_dir: dict[str, str] = {}
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        tokens = re.split(r"\s+", seg)
        if not tokens:
            continue
        col_name = tokens[0].strip('"`[]')
        direction = "ASC"
        for token in tokens[1:]:
            token_upper = token.upper()
            if token_upper in ("ASC", "DESC"):
                direction = token_upper
                break
        seg_to_dir[col_name.lower()] = direction

    return [seg_to_dir.get(col.lower(), "ASC") for col in cursor_columns]


def strip_strings_and_comments(sql: str) -> str:
    """Mask SQL strings and comments with spaces for structural scanning."""
    n = len(sql)
    result = list(sql)
    i = 0
    while i < n:
        ch = sql[i]
        if ch == "'":
            result[i] = " "
            i += 1
            while i < n:
                if sql[i] == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        result[i] = " "
                        result[i + 1] = " "
                        i += 2
                        continue
                    result[i] = " "
                    i += 1
                    break
                result[i] = " "
                i += 1
            continue
        if ch == '"':
            result[i] = " "
            i += 1
            while i < n and sql[i] != '"':
                result[i] = " "
                i += 1
            if i < n:
                result[i] = " "
                i += 1
            continue
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] != "\n":
                result[i] = " "
                i += 1
            continue
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            result[i] = " "
            result[i + 1] = " "
            i += 2
            while i < n - 1 and not (sql[i] == "*" and sql[i + 1] == "/"):
                result[i] = " "
                i += 1
            if i < n - 1:
                result[i] = " "
                result[i + 1] = " "
                i += 2
            continue
        i += 1
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


def has_top_level_where(sql: str) -> bool:
    """Return whether SQL has a top-level WHERE clause."""
    masked = strip_strings_and_comments(sql)
    upper = masked.upper()
    i = 0
    depth = 0
    while i < len(masked):
        ch = masked[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and upper[i:i + 7] == " WHERE ":
            return True
        i += 1
    return False


def inject_keyset_predicate(
    sql: str,
    params: list,
    cursor_values: list,
    cursor_columns: list[str],
    cursor_directions: list[str],
) -> tuple[str, list]:
    """Insert a keyset predicate before ORDER BY."""
    order_idx = find_top_level_order_by(sql)
    if order_idx < 0:
        raise ValueError("setQuery 的 sql 必须包含 ORDER BY 子句以使用 keyset 分页")
    head = sql[:order_idx]
    tail = sql[order_idx:]

    directions = cursor_directions or ["ASC"] * len(cursor_columns)
    if len(directions) != len(cursor_columns):
        directions = ["ASC"] * len(cursor_columns)

    has_null_cursor = any(v is None for v in cursor_values)
    all_desc = all(d == "DESC" for d in directions)
    all_asc = all(d == "ASC" for d in directions)
    if (all_desc or all_asc) and not has_null_cursor:
        cursor_cols_str = ", ".join(cursor_columns)
        placeholders = ", ".join(["?"] * len(cursor_columns))
        op = "<" if all_desc else ">"
        predicate = f"({cursor_cols_str}) {op} ({placeholders})"
        new_params = list(params) + list(cursor_values)
    else:
        clauses = []
        new_params = list(params)

        def col_eq(col_idx: int) -> tuple[str, list]:
            col_name = cursor_columns[col_idx]
            value = cursor_values[col_idx]
            if value is None:
                return f"{col_name} IS NULL", []
            return f"{col_name} = ?", [value]

        def col_gt(col_idx: int, direction: str) -> tuple[str, list]:
            col_name = cursor_columns[col_idx]
            value = cursor_values[col_idx]
            if direction == "DESC":
                if value is None:
                    return "0", []
                return f"({col_name} < ? OR {col_name} IS NULL)", [value]
            if value is None:
                return f"{col_name} IS NOT NULL", []
            return f"{col_name} > ?", [value]

        for i in range(len(cursor_columns)):
            level_parts = []
            level_params: list = []
            for k in range(i):
                eq_sql, eq_params = col_eq(k)
                level_parts.append(eq_sql)
                level_params.extend(eq_params)
            gt_sql, gt_params = col_gt(i, directions[i])
            level_parts.append(gt_sql)
            level_params.extend(gt_params)
            clauses.append("(" + " AND ".join(level_parts) + ")")
            new_params.extend(level_params)
        predicate = "(" + " OR ".join(clauses) + ")"

    if has_top_level_where(head):
        head_new = f"{head} AND {predicate}"
    else:
        head_new = f"{head} WHERE {predicate}"
    new_sql = head_new + tail
    return new_sql, new_params
