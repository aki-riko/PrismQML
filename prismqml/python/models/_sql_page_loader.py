# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""SqlListModel page loading pipeline. SQL 列表模型分页读取管线。"""

from __future__ import annotations

from contextlib import closing
from typing import Optional

from PySide6.QtCore import QByteArray, Qt

from ..core.logger import exception
from ._sqlite_connection import open_read_only as _open_read_only
from ._sql_query_tools import validate_keyset_query


def _read_column_names(path: str, sql: str, params: list) -> list[str]:
    with closing(_open_read_only(path)) as conn:
        cursor = conn.execute(f"{sql} LIMIT 0", params)
        return [description[0] for description in cursor.description]


class SqlPageLoaderMixin:
    """Own page routing, loading and formatting. 负责分页路由、读取与格式化。"""

    def _get_page_for_access(
        self, page_idx: int, row: int, consumer: str
    ) -> Optional[tuple[list, Optional[list]]]:
        try:
            return self._get_page(page_idx)
        except Exception as exc:
            exception(
                f"SqlListModel.{consumer} page fetch failed: "
                f"page={page_idx} row={row} {type(exc).__name__}: {exc}"
            )
            return None

    def _compute_count(self) -> int:
        if not self._count_sql:
            return 0
        paths = self._router.route(self._count_params)
        if not paths:
            return 0
        total = 0
        for path in paths:
            if self._rust_is_available():
                total += int(
                    self._rust_module().count_rows(
                        path, self._count_sql, self._count_params or None
                    )
                )
            else:
                with closing(_open_read_only(path)) as conn:
                    cursor = conn.execute(self._count_sql, self._count_params)
                    row = cursor.fetchone()
                    total += int(row[0]) if row else 0
        return total

    def _apply_formatter(
        self, row: list, column_index: int, formatter, log_failure: bool
    ) -> bool:
        try:
            row[column_index] = formatter(row[column_index])
        except Exception as exc:
            if log_failure:
                exception(
                    "SqlListModel formatter failed for column "
                    f"{self._columns[column_index]}; further failures in this page "
                    f"are suppressed: {type(exc).__name__}: {exc}"
                )
            return False
        return True

    def _apply_formatters(self, rows: list) -> None:
        if not self._formatters:
            return
        formatters = [
            (index, self._formatters[column])
            for index, column in enumerate(self._columns)
            if column in self._formatters
        ]
        failed_columns = set()
        for row in rows:
            for column_index, formatter in formatters:
                if not self._apply_formatter(
                    row,
                    column_index,
                    formatter,
                    column_index not in failed_columns,
                ):
                    failed_columns.add(column_index)

    def _route_page(
        self, page_idx: int, end_cursor_of_prev: Optional[list]
    ) -> tuple[list[str], bool]:
        paths = self._router.route(self._params)
        if not paths:
            return [], False
        is_multi_shard = len(paths) > 1
        if is_multi_shard and not self._cursor_columns:
            raise RuntimeError(
                "多 shard 场景必须设置 cursor_columns,无法走 OFFSET。"
                "调用方需要确保 setQuery(cursor_columns=[...]) 已传入。"
            )
        if is_multi_shard and page_idx > 0 and end_cursor_of_prev is None:
            raise RuntimeError(
                f"多 shard random access 不支持 (page_idx={page_idx} 无 prev_cursor)。"
                f"用户应通过连续滚动到达,或扩大 LRU 容量 (lru_capacity={self._lru_capacity})。"
            )
        return paths, is_multi_shard

    def _plan_page(
        self, page_idx: int, end_cursor_of_prev: Optional[list]
    ) -> tuple[str, list, int, bool, Optional[list[int]]]:
        offset_to_use = page_idx * self._page_size
        use_keyset = bool(self._cursor_columns) and (
            page_idx == 0 or end_cursor_of_prev is not None
        )
        if use_keyset and end_cursor_of_prev is not None:
            sql_to_run, params_to_run = self._inject_keyset_predicate(
                self._sql, list(self._params), end_cursor_of_prev,
                self._cursor_columns, self._cursor_directions,
                self._cursor_nullable_index,
            )
            offset_to_use = 0
        else:
            sql_to_run = self._sql
            params_to_run = list(self._params)
            use_keyset = False
        cursor_indices = (
            self._cursor_col_indices
            if self._cursor_columns and self._cursor_col_indices
            else None
        )
        return sql_to_run, params_to_run, offset_to_use, use_keyset, cursor_indices

    def _fetch_fan_out_page(
        self, paths: list[str], sql: str, params: list,
        cursor_indices: Optional[list[int]],
    ) -> tuple[list[str], list, Optional[list]]:
        if not self._rust_is_available():
            raise RuntimeError(
                "多 shard fan-out 需要 prismqml_rs Rust 模块,Python fallback 不支持"
            )
        indices = cursor_indices if cursor_indices else []
        directions = (
            list(self._cursor_directions)
            if self._cursor_directions
            else ["DESC"] * len(self._cursor_columns)
        )
        result = self._rust_module().fan_out_fetch_page(
            paths, sql, params if params else None, self._page_size,
            indices, directions,
        )
        return result["columns"], result["rows"], result.get("last_cursor")

    def _fetch_rust_page(
        self, path: str, sql: str, params: list, offset: int,
        use_keyset: bool, cursor_indices: Optional[list[int]],
    ) -> tuple[list[str], list, Optional[list]]:
        result = self._rust_module().fetch_page(
            path, sql, params if params else None, offset,
            self._page_size, use_keyset, cursor_indices,
        )
        return result["columns"], result["rows"], result.get("last_cursor")

    def _fetch_sqlite_page(
        self, path: str, sql: str, params: list, offset: int,
        use_keyset: bool, cursor_indices: Optional[list[int]],
    ) -> tuple[list[str], list, Optional[list]]:
        paged_sql = f"{sql} LIMIT ?" if use_keyset else f"{sql} LIMIT ? OFFSET ?"
        with closing(_open_read_only(path)) as conn:
            bind = list(params) + [self._page_size]
            if not use_keyset:
                bind.append(offset)
            cursor = conn.execute(paged_sql, bind)
            columns = [description[0] for description in cursor.description]
            rows = [list(row) for row in cursor.fetchall()]
        if not rows or not cursor_indices:
            return columns, rows, None
        last = rows[-1]
        end_cursor = [
            last[index] if index < len(last) else None
            for index in cursor_indices
        ]
        return columns, rows, end_cursor

    def _dispatch_page(
        self, paths: list[str], is_multi_shard: bool, sql: str,
        params: list, offset: int, use_keyset: bool,
        cursor_indices: Optional[list[int]],
    ) -> tuple[list[str], list, Optional[list]]:
        if is_multi_shard:
            return self._fetch_fan_out_page(paths, sql, params, cursor_indices)
        if self._rust_is_available():
            return self._fetch_rust_page(
                paths[0], sql, params, offset, use_keyset, cursor_indices
            )
        return self._fetch_sqlite_page(
            paths[0], sql, params, offset, use_keyset, cursor_indices
        )

    def _fetch_page(
        self, page_idx: int, end_cursor_of_prev: Optional[list] = None
    ) -> dict:
        """Fetch one page through the fixed route-to-return pipeline."""
        paths, is_multi_shard = self._route_page(page_idx, end_cursor_of_prev)
        if not paths:
            return {"rows": [], "end_cursor": None}
        plan = self._plan_page(page_idx, end_cursor_of_prev)
        columns, rows, end_cursor = self._dispatch_page(
            paths, is_multi_shard, *plan
        )
        if not self._columns:
            self._install_resolved_columns(columns, validate_unique=False)
        self._apply_formatters(rows)
        return {"rows": rows, "end_cursor": end_cursor}

    def _install_resolved_columns(
        self, columns: list[str], *, validate_unique: bool = True
    ) -> None:
        self._columns = list(columns)
        if validate_unique:
            normalized = [column.casefold() for column in self._columns]
            if len(set(normalized)) != len(normalized):
                raise ValueError("SqlListModel SELECT 输出列名必须唯一")
        base = Qt.UserRole + 1
        self._role_to_col = {base + i: i for i in range(len(self._columns))}
        self._role_names = {
            base + i: QByteArray(self._columns[i].encode("utf-8"))
            for i in range(len(self._columns))
        }
        if self._cursor_columns:
            col_to_idx = {name: i for i, name in enumerate(self._columns)}
            self._cursor_col_indices = [
                col_to_idx[column]
                for column in self._cursor_columns
                if column in col_to_idx
            ]
            if len(self._cursor_col_indices) != len(self._cursor_columns):
                missing = [
                    column
                    for column in self._cursor_columns
                    if column not in col_to_idx
                ]
                raise ValueError(
                    f"cursor_columns {missing} not found in SELECT column list {self._columns}"
                )

    def _resolve_columns(self) -> None:
        """Resolve columns and validate the strict keyset contract."""
        if self._columns:
            return
        paths = self._router.route(self._params)
        if not paths:
            return
        directions = (
            validate_keyset_query(self._sql, self._cursor_columns)
            if self._cursor_columns
            else []
        )
        columns = _read_column_names(paths[0], self._sql, self._params)
        self._install_resolved_columns(columns)
        if not self._cursor_columns:
            self._cursor_directions = []
            return
        self._cursor_directions = directions

    def _get_page(self, page_idx: int) -> tuple[list, Optional[list]]:
        """返回 (rows, end_cursor)"""
        cached = self._cache.get(page_idx)
        if cached is not None:
            return cached
        prev_cursor = (
            self._cache.previous_cursor(page_idx)
            if self._cursor_columns and page_idx > 0
            else None
        )
        result = self._fetch_page(page_idx, end_cursor_of_prev=prev_cursor)
        rows = result["rows"]
        end_cursor = result.get("end_cursor")
        self._cache.put(page_idx, rows, end_cursor)
        return rows, end_cursor
