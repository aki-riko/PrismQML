# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.

"""
SqlListModel — 高性能 SQLite 分页 list model

设计目标
========
QML ListView/TableView 对接 1M+ 行 SQLite 数据,内存恒定 + 滚动 120fps + 任意位置翻页 <50ms。

工作原理
========
- model 持 (db_path, sql_template, params, formatters),不一次性 fetch
- data(idx, role) 命中时,定位 page = idx // PAGE_SIZE,LRU 缓存按页加载
- LRU 容量足以覆盖典型滚动 (默认 16 页 = 16,000 行)
- 加速路径: 优先用 Rust crate prismqml_rs.fetch_page (cargo build,详见 rust/);
  无 Rust 时自动 fallback 到内置 sqlite3 (功能完全等价,只是慢一档)
- formatters: 业务层提供 column_name -> callable 字典,新页加载时对每行该列原始值
  跑一遍 formatter,结果缓存进 page。data() 命中只是查表,无每帧开销。

接入示例
========
    from fluentqml import SqlListModel
    model = SqlListModel("/path/to/db.sqlite", parent=self)
    model.setQuery(
        "SELECT id, date, time, type, character FROM records WHERE book_id=:bid",
        count_sql="SELECT COUNT(*) FROM records WHERE book_id=:bid",
        params={"bid": 4},
        formatters={
            "income": lambda v: format_currency(v),  # JSON 字符串 -> "+492, +6160"
        },
    )
    # QML 端: ListView { model: backend.tableModel; delegate: Item { Label { text: model.income } } }

⚠️ Role 名直接来自 SQL SELECT 字段名,所以 SQL 里写 SELECT col AS xxx 时 QML 用 xxx 引用。
"""
from __future__ import annotations

import sqlite3
from collections import OrderedDict
from contextlib import closing
from pathlib import Path
from typing import Any, Optional, Union

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    Qt,
    Signal,
    Slot,
)

# 优先 Rust 实现
try:
    import prismqml_rs as _rs  # noqa: WPS433

    _HAS_RUST = True
except ImportError:
    _rs = None
    _HAS_RUST = False


PAGE_SIZE_DEFAULT = 1000
LRU_CAPACITY_DEFAULT = 64  # 64 页 × 1000 行 = 6.4w 行内存常驻;1B+ 跨片 random access 也少触发淘汰


class DbRouter:
    """数据库分片路由协议

    实现这个协议的对象传给 SqlListModel 启用跨分片查询:

        class MyRouter(DbRouter):
            def route(self, params): return ['shard1.db', 'shard2.db', ...]

        model = SqlListModel(MyRouter(), parent=self)

    单库场景不需要实现,直接传 db_path 字符串,model 内部包装成 _SingleDbRouter。
    """
    def route(self, params: list) -> list[str]:
        """根据 SQL 占位符参数返回需要查询的 shard 文件路径列表

        - 返回 1 个: 走单 shard 路径 (与传 db_path 字符串等价)
        - 返回 N 个: 走 fan-out 路径 (Rust shard.fan_out_fetch_page 归并查询)

        Args:
            params: 当前 SQL 的参数 (业务可根据其中的 book_id / date_range 决定 shard)
        Returns:
            shard db_path 列表
        """
        raise NotImplementedError


class _SingleDbRouter(DbRouter):
    """单库默认 router,恒等返回单一 db_path"""
    def __init__(self, db_path: str):
        self._db_path = db_path

    def route(self, params: list) -> list[str]:
        return [self._db_path]


class SqlListModel(QAbstractListModel):
    """SQLite 分页 list model,QML ListView/TableView 直接消费。"""

    queryChanged = Signal()
    countChanged = Signal()

    def __init__(
        self,
        db_path_or_router: Union[str, Path, DbRouter],
        parent=None,
        page_size: int = PAGE_SIZE_DEFAULT,
        lru_capacity: int = LRU_CAPACITY_DEFAULT,
    ) -> None:
        super().__init__(parent)
        # 单 db_path 字符串自动包装成 SingleDbRouter,保持现有调用行为
        if isinstance(db_path_or_router, (str, Path)):
            self._router: DbRouter = _SingleDbRouter(str(db_path_or_router))
            self._db_path: str = str(db_path_or_router)  # 保留供向后兼容/调试
        elif isinstance(db_path_or_router, DbRouter):
            self._router = db_path_or_router
            self._db_path = ""  # 多 shard 时无意义
        else:
            raise TypeError(
                f"db_path_or_router 必须是 str/Path/DbRouter,got {type(db_path_or_router)}"
            )
        self._page_size: int = max(1, int(page_size))
        self._lru_capacity: int = max(1, int(lru_capacity))

        self._sql: str = ""
        self._count_sql: str = ""
        self._params: list = []  # 顺序参数,绑定到 ? 占位符
        self._count_params: list = []  # count_sql 的独立参数(默认 = self._params)
        self._formatters: dict[str, callable] = {}  # column_name -> formatter callable
        # keyset 分页支持: cursor_columns 是 ORDER BY 前缀列名,例如 ['date', 'time', 'id']
        self._cursor_columns: list[str] = []
        self._cursor_col_indices: list[int] = []  # cursor_columns 在 SELECT 中的下标
        self._cursor_directions: list[str] = []  # 每个 cursor 列的 ASC/DESC (S3, _resolve_columns 填充)
        # _cursor_keyset_clause 是 "(date, time, id) < (?, ?, ?)" 谓词模板,首次构建后缓存

        self._row_count: int = 0
        # 列名(roleNames 用) — 首次 fetch 后填充
        self._columns: list[str] = []
        # role id → column index 映射
        self._role_to_col: dict[int, int] = {}
        # role name → role id (供 QML)
        self._role_names: dict[int, QByteArray] = {}

        # LRU: page_idx → (rows, end_cursor)
        # rows: list[list[Any]]
        # end_cursor: list[Any] | None — 末行 cursor_columns 的值,供下页 keyset 用
        self._cache: "OrderedDict[int, tuple[list, Optional[list]]]" = OrderedDict()

    # ============================================================
    # 公开 API
    # ============================================================
    @Slot(str, str, "QVariant")
    def setQuery(
        self,
        sql: str,
        count_sql: str,
        params: Optional[Union[list, tuple, dict]] = None,
        formatters: Optional[dict] = None,
        cursor_columns: Optional[list] = None,
        count_params: Optional[Union[list, tuple, dict]] = None,
        cursor_directions: Optional[list] = None,
    ) -> None:
        """设置查询语句

        Args:
            sql: 主查询(不含 LIMIT/OFFSET,model 会自动追加)
            count_sql: SELECT COUNT(*) 语句(用于 rowCount)
            params: 顺序占位符 ? 的参数列表/元组,或 dict (会按 :name 替换为 ?)
                   推荐 list/tuple,dict 仅作便捷
            formatters: 可选 dict {column_name: callable(raw_value) -> formatted_value}
                       新页加载时对每行该列原始值跑一遍 formatter,结果缓存,QML 拿到的就是格式化后的值。
                       例如把 JSON 字符串 '{"a":1}' 转成显示用的 '+1' 这种业务格式化。
            cursor_columns: 可选列名列表,例如 ['date', 'time', 'id']。
                           设置后启用 keyset 分页:连续翻页用 (cursor) < (?,?,?) 谓词,
                           1B 行末页 fetch 也是 <50ms。要求:
                             - 这些列必须是 ORDER BY 的前缀列
                             - 调用方 SQL **不要**包含 (cursor) 谓词,model 会自动追加
                           不传则走 OFFSET 兼容路径(<100M 行场景仍正常)。
            count_params: 可选,count_sql 的独立参数列表。不传时复用 params。
                         适用于 count_sql 是单独优化路径(例如读 count 缓存表只要 book_id,
                         而主 sql 含搜索 LIKE 占位符)的情况。
        """
        self.beginResetModel()
        try:
            (
                self._sql,
                self._count_sql,
                self._params,
                _count_ordered_from_params,
            ) = self._normalize_sql(sql, count_sql, params)
            # B1 修复: count_params=None 时使用 count 自己的 ordered (从 params 解析),
            # 而非主查询的 self._params。dict params 主/count 占位符顺序不同时不再错位。
            if count_params is None:
                self._count_params = list(_count_ordered_from_params)
            else:
                if isinstance(count_params, (list, tuple)):
                    self._count_params = list(count_params)
                elif isinstance(count_params, dict):
                    # ⚠️ S1 修复: 用 _normalize_one 单段处理,各自 SQL 各自参数,绝不串扰。
                    self._count_sql, self._count_params = self._normalize_one(
                        self._count_sql, count_params
                    )
                else:
                    raise TypeError(f"count_params 类型不支持: {type(count_params)}")
            self._formatters = dict(formatters) if formatters else {}
            self._cursor_columns = list(cursor_columns) if cursor_columns else []
            self._cursor_col_indices: list[int] = []  # 下面 _resolve_columns 填充
            self._cache.clear()
            self._row_count = self._compute_count()
            self._columns = []
            self._role_to_col = {}
            self._role_names = {}
            # 提前解析 SELECT 的列名 (不读数据,只 prepare):
            # 多 shard 场景下,首次 fetch 用 fan_out 必须已知 cursor_indices,
            # 否则会在第二页 keyset 注入时丢失 cursor 参数。
            self._resolve_columns()
            # B2: 显式 cursor_directions 优先 (覆盖 _resolve_columns 启发式解析的结果)
            # 业务侧明确知道 ORDER BY 方向时强烈建议传入,启发式解析对 COLLATE / 函数表达式 / 大小写不敏感
            if cursor_directions is not None:
                if len(cursor_directions) != len(self._cursor_columns):
                    raise ValueError(
                        f"cursor_directions 长度 {len(cursor_directions)} 与 cursor_columns "
                        f"长度 {len(self._cursor_columns)} 不一致"
                    )
                self._cursor_directions = [
                    d.upper() if d.upper() in ("ASC", "DESC") else "ASC"
                    for d in cursor_directions
                ]
            # 触发首次 fetch 来填充 page 0 (此时 cursor_col_indices 已有)
            if self._row_count > 0:
                first_page = self._fetch_page(0)
                self._cache[0] = (first_page["rows"], first_page.get("end_cursor"))
                self._touch_page(0)
        finally:
            self.endResetModel()
        self.queryChanged.emit()
        self.countChanged.emit()

    @Slot(result=int)
    def count(self) -> int:
        """供 QML 读取行数(也可用 rowCount)"""
        return self._row_count

    @Slot()
    def refresh(self) -> None:
        """重新跑当前 query,丢弃所有缓存(数据被外部改动后调用)

        M1 修复: 同时清空 columns / role 表 / cursor_indices,确保 SELECT 列变更
        (业务侧手动改 self._sql 字段) 时不会用 stale role 渲染错列。
        """
        if not self._sql:
            return
        self.beginResetModel()
        try:
            self._cache.clear()
            self._columns = []
            self._role_to_col = {}
            self._role_names = {}
            self._cursor_col_indices = []
            self._cursor_directions = []
            self._row_count = self._compute_count()
            if self._row_count > 0:
                # 重新解析 columns + cursor 方向 + 拉首页
                self._resolve_columns()
                first = self._fetch_page(0)
                self._cache[0] = (first["rows"], first.get("end_cursor"))
                self._touch_page(0)
        finally:
            self.endResetModel()
        self.countChanged.emit()

    @Slot(int, result="QVariantMap")
    def getRow(self, row: int) -> dict:
        """按行索引返回该行所有列的 dict (column_name → value),供 QML 弹窗读单条详情"""
        if row < 0 or row >= self._row_count or not self._columns:
            return {}
        page_idx = row // self._page_size
        offset_in_page = row - page_idx * self._page_size
        rows, _end_cursor = self._get_page(page_idx)
        if not rows or offset_in_page >= len(rows):
            return {}
        cells = rows[offset_in_page]
        return {self._columns[i]: cells[i] for i in range(len(self._columns))}

    # ============================================================
    # QAbstractListModel overrides
    # ============================================================
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.isValid():
            return 0
        return self._row_count

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= self._row_count:
            return None
        col = self._role_to_col.get(role)
        if col is None:
            return None
        page_idx = row // self._page_size
        offset_in_page = row - page_idx * self._page_size
        # M-1 修复: _fetch_page 在多 shard random access 时可能 raise,
        # Qt model.data() 的异常会让 ListView 渲染中断 + 控制台爆栈,严重时 UI 死。
        # 这里捕获 + log,降级返 None,业务侧表现为该 cell 显示空但 ListView 仍可滚。
        try:
            rows, _end_cursor = self._get_page(page_idx)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"SqlListModel.data 取 page {page_idx} 失败 (row={row}): {e}"
            )
            return None
        if not rows or offset_in_page >= len(rows):
            return None
        try:
            return rows[offset_in_page][col]
        except IndexError:
            return None

    def roleNames(self) -> dict[int, QByteArray]:
        if self._role_names:
            return dict(self._role_names)
        # 没 setQuery 前给个空 dict; QML 那边 ListView 会等 model reset
        return {}

    # ============================================================
    # 内部
    # ============================================================
    def _normalize_one(
        self,
        sql: str,
        params: Optional[Union[list, tuple, dict]],
    ) -> tuple[str, list]:
        """单段 SQL 参数归一化: dict :name → 顺序 ?, list/tuple 原样

        H1 修复: 扫描 :name 时跳过字符串字面量 (单/双引号) 和注释 (-- / /* */),
        否则 SELECT 'foo:bar' / -- :note / /* :x */ 里的 :name 会被误替换。
        """
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
                # 单引号字符串: 内含 '' 是单引号转义
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
                # 双引号标识符 (SQLite 也兼容,但用作字符串字面量罕见)
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
                # 行注释 -- ... \n
                if ch == '-' and i + 1 < n and sql[i + 1] == '-':
                    while i < n and sql[i] != '\n':
                        out.append(sql[i])
                        i += 1
                    continue
                # 块注释 /* ... */
                if ch == '/' and i + 1 < n and sql[i + 1] == '*':
                    out.append('/')
                    out.append('*')
                    i += 2
                    while i < n - 1 and not (sql[i] == '*' and sql[i + 1] == '/'):
                        out.append(sql[i])
                        i += 1
                    if i < n - 1:
                        out.append('*')
                        out.append('/')
                        i += 2
                    continue
                # :name placeholder
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

    def _normalize_sql(
        self,
        sql: str,
        count_sql: str,
        params: Optional[Union[list, tuple, dict]],
    ) -> tuple[str, str, list, list]:
        """主查询 + count 查询都解析,各自得到自己的 ordered list

        B1 修复: 之前返回 (new_sql, new_count_sql, main_ordered) 丢弃了 count 的 ordered,
        导致 setQuery 在 count_params=None 分支用 main_ordered 给 count 绑参数。
        现在返回 (new_sql, new_count_sql, main_ordered, count_ordered)。

        list/tuple/None 时 main 与 count 共享同一份(直接 list/tuple),所以两侧 ordered 相同。
        dict 时 main_ordered 按主 sql 占位符顺序、count_ordered 按 count_sql 占位符顺序。
        """
        new_sql, main_ordered = self._normalize_one(sql, params)
        new_count_sql, count_ordered = self._normalize_one(count_sql, params)
        return new_sql, new_count_sql, main_ordered, count_ordered

    def _compute_count(self) -> int:
        if not self._count_sql:
            return 0
        paths = self._router.route(self._count_params)
        if not paths:
            return 0
        total = 0
        for p in paths:
            if _HAS_RUST:
                total += int(_rs.count_rows(p, self._count_sql, self._count_params or None))
            else:
                # M2: 显式 close,避免 Python sqlite3 with 块只 commit 不 close 的坑
                with closing(sqlite3.connect(p)) as conn:
                    cur = conn.execute(self._count_sql, self._count_params)
                    row = cur.fetchone()
                    total += int(row[0]) if row else 0
        return total

    def _fetch_page(self, page_idx: int, end_cursor_of_prev: Optional[list] = None) -> dict:
        """拉一页

        返回 dict {"rows": [...], "end_cursor": [...] | None}

        单 shard:
        1. cursor_columns 已设 + 上页 end_cursor 已知 → keyset 路径,1B 行也飞快
        2. cursor_columns 已设但 end_cursor 未知 (random access page_idx>0) → OFFSET 一次性,
           回填本页 end_cursor 后续再续
        3. cursor_columns 未设 → 老 OFFSET 路径

        多 shard:
        - 走 fan_out_fetch_page: 每 shard 各 fetch limit 行,Rust 端归并取 top-limit
        - 不支持 OFFSET (跨片 OFFSET 无意义),要求 cursor_columns 必须设置
        """
        offset = page_idx * self._page_size
        use_keyset = bool(self._cursor_columns) and (page_idx == 0 or end_cursor_of_prev is not None)

        # 决定走单 shard 还是 fan-out
        paths = self._router.route(self._params)
        if not paths:
            return {"rows": [], "end_cursor": None}
        is_multi_shard = len(paths) > 1

        if is_multi_shard and not self._cursor_columns:
            raise RuntimeError(
                "多 shard 场景必须设置 cursor_columns,无法走 OFFSET。"
                "调用方需要确保 setQuery(cursor_columns=[...]) 已传入。"
            )

        # ⚠️ S2 修复: 多 shard 跳页时如果 prev_cursor 缺失(LRU 淘汰)就 raise,
        # 不能静默 fall-through 到 OFFSET=0,否则每 shard 返回前 N 行,
        # ListView 在第 5000 行渲染 page 0 内容,UI 看不出错但数据完全错位。
        if is_multi_shard and page_idx > 0 and end_cursor_of_prev is None:
            raise RuntimeError(
                f"多 shard random access 不支持 (page_idx={page_idx} 无 prev_cursor)。"
                f"用户应通过连续滚动到达,或扩大 LRU 容量 (lru_capacity={self._lru_capacity})。"
            )

        # 拼 keyset SQL: 在 ORDER BY 前插入 (cursor) < (?,?,...) 谓词
        if use_keyset and end_cursor_of_prev is not None:
            sql_to_run, params_to_run = self._inject_keyset_predicate(
                self._sql, list(self._params), end_cursor_of_prev
            )
            offset_to_use = 0
        else:
            sql_to_run = self._sql
            params_to_run = list(self._params)
            offset_to_use = offset
            use_keyset = False  # 即便 cursor 已设,首页也走 LIMIT (offset=0 等价)

        cursor_indices = self._cursor_col_indices if (self._cursor_columns and self._cursor_col_indices) else None

        # ====== 多 shard fan-out 路径 ======
        if is_multi_shard:
            if not _HAS_RUST:
                raise RuntimeError("多 shard fan-out 需要 prismqml_rs Rust 模块,Python fallback 不支持")
            if not cursor_indices:
                # 还没建过 column 映射,临时按列名匹配 (假设 SELECT 顺序与下面 cursor_columns 一致)
                # 但这种情况只发生在 setQuery 后第一页 fetch,我们用一个 hack: 跑一次 noop fetch 拿 columns
                # 简化: 多 shard 下首次 fetch 必须保证 self._columns 已知,否则用空列表表 indices
                cursor_indices = []
            # S3: 用真实 cursor_directions (Phase _resolve_columns 已解析),不再写死 DESC
            sort_dirs = list(self._cursor_directions) if self._cursor_directions else ["DESC"] * len(self._cursor_columns)
            result = _rs.fan_out_fetch_page(
                paths,
                sql_to_run,
                params_to_run if params_to_run else None,
                self._page_size,
                cursor_indices,
                sort_dirs,
            )
            columns = result["columns"]
            rows = result["rows"]
            end_cursor = result.get("last_cursor")
        # ====== 单 shard 路径 ======
        elif _HAS_RUST:
            result = _rs.fetch_page(
                paths[0],
                sql_to_run,
                params_to_run if params_to_run else None,
                offset_to_use,
                self._page_size,
                use_keyset,
                cursor_indices,
            )
            columns = result["columns"]
            rows = result["rows"]
            end_cursor = result.get("last_cursor")
        else:
            paged_sql = f"{sql_to_run} LIMIT ?" if use_keyset else f"{sql_to_run} LIMIT ? OFFSET ?"
            with closing(sqlite3.connect(paths[0])) as conn:
                bind = list(params_to_run) + [self._page_size]
                if not use_keyset:
                    bind.append(offset_to_use)
                cur = conn.execute(paged_sql, bind)
                columns = [d[0] for d in cur.description]
                rows = [list(r) for r in cur.fetchall()]
            if rows and cursor_indices:
                last = rows[-1]
                end_cursor = [last[i] if i < len(last) else None for i in cursor_indices]
            else:
                end_cursor = None

        # 首次拿到 columns: 建立 role 表 + cursor 列下标
        if not self._columns:
            self._columns = list(columns)
            base = Qt.UserRole + 1
            self._role_to_col = {base + i: i for i in range(len(self._columns))}
            self._role_names = {
                base + i: QByteArray(self._columns[i].encode("utf-8"))
                for i in range(len(self._columns))
            }
            # cursor 列名 → 下标 (用于后续 fetch 提取)
            if self._cursor_columns:
                col_to_idx = {name: i for i, name in enumerate(self._columns)}
                self._cursor_col_indices = [col_to_idx[c] for c in self._cursor_columns if c in col_to_idx]
                if len(self._cursor_col_indices) != len(self._cursor_columns):
                    missing = [c for c in self._cursor_columns if c not in col_to_idx]
                    raise ValueError(
                        f"cursor_columns {missing} not found in SELECT column list {self._columns}"
                    )
        # 应用 formatters: 把指定列的原始值替换为格式化结果
        if self._formatters:
            col_indices_to_format = [
                (i, self._formatters[self._columns[i]])
                for i in range(len(self._columns))
                if self._columns[i] in self._formatters
            ]
            if col_indices_to_format:
                for row in rows:
                    for i, fn in col_indices_to_format:
                        try:
                            row[i] = fn(row[i])
                        except Exception:
                            pass  # formatter 出错不致命,保留原值
        return {"rows": rows, "end_cursor": end_cursor}

    def _resolve_columns(self) -> None:
        """提前确定 SELECT 列名 + roleNames + cursor_col_indices + cursor 方向

        通过 prepare + LIMIT 0 拿到 cursor.description,无需读数据。
        多 shard 场景下,任意 shard 的 schema 一致,取第一个即可。
        S3 修复: 同时解析 ORDER BY 抽出每个 cursor 列的 ASC/DESC 方向。
        B8 修复: 用 file: URI ?mode=ro 只读连接,避免与写线程争锁;加 busy_timeout 防死等。
        """
        if self._columns:
            return
        paths = self._router.route(self._params)
        if not paths:
            return
        # B8: 只读 URI + busy_timeout 5s
        ro_uri = f"file:{paths[0]}?mode=ro"
        with closing(sqlite3.connect(ro_uri, uri=True, timeout=5)) as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            cur = conn.execute(f"{self._sql} LIMIT 0", self._params)
            self._columns = [d[0] for d in cur.description]
        base = Qt.UserRole + 1
        self._role_to_col = {base + i: i for i in range(len(self._columns))}
        self._role_names = {
            base + i: QByteArray(self._columns[i].encode("utf-8"))
            for i in range(len(self._columns))
        }
        if self._cursor_columns:
            col_to_idx = {name: i for i, name in enumerate(self._columns)}
            self._cursor_col_indices = [col_to_idx[c] for c in self._cursor_columns if c in col_to_idx]
            if len(self._cursor_col_indices) != len(self._cursor_columns):
                missing = [c for c in self._cursor_columns if c not in col_to_idx]
                raise ValueError(
                    f"cursor_columns {missing} not found in SELECT column list {self._columns}"
                )
            # S3: 解析 ORDER BY 抽出每个 cursor 列的方向 (默认 ASC,显式 DESC)
            self._cursor_directions = self._parse_cursor_directions()
        else:
            self._cursor_directions = []

    def _parse_cursor_directions(self) -> list:
        """从 self._sql 的 ORDER BY 子句解析 self._cursor_columns 各列的 ASC/DESC

        返回与 cursor_columns 等长的列表,每元素 'ASC' 或 'DESC'。
        SQL 子句形如 'ORDER BY date DESC, time DESC, id DESC',
        匹配每个 cursor 列名后看下一个 token。找不到时默认 'ASC' (SQL 标准)。

        B2 修复:
        - 列名匹配大小写不敏感 (SQL 标识符不敏感)
        - 跳括号内的逗号 (substr(date,1,7) 不会被拆错)
        - 容忍 COLLATE / NULLS FIRST/LAST 修饰: 找最后一个 ASC/DESC token
        - 启发式无法识别时业务可通过 setQuery(cursor_directions=[...]) 显式指定
        """
        import re
        upper = self._sql.upper()
        order_idx = upper.rfind(" ORDER BY ")
        if order_idx < 0:
            return ["ASC"] * len(self._cursor_columns)
        order_clause = self._sql[order_idx + len(" ORDER BY "):]
        # 取 ORDER BY 到下一个 LIMIT/OFFSET/末尾的截断
        for kw in (" LIMIT ", " OFFSET "):
            cut = order_clause.upper().find(kw)
            if cut >= 0:
                order_clause = order_clause[:cut]
        # 按逗号拆但跳过括号内 (substr(date,1,7) 之类)
        depth = 0
        seg_start = 0
        segments: list[str] = []
        for i, ch in enumerate(order_clause):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ',' and depth == 0:
                segments.append(order_clause[seg_start:i])
                seg_start = i + 1
        segments.append(order_clause[seg_start:])

        # 大小写不敏感的 col → direction 映射
        seg_to_dir: dict[str, str] = {}
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            tokens = re.split(r"\s+", seg)
            if not tokens:
                continue
            col_name = tokens[0].strip('"`[]')
            # 容忍修饰: 找任一 ASC/DESC token (例如 "date COLLATE NOCASE DESC")
            direction = "ASC"
            for t in tokens[1:]:
                t_upper = t.upper()
                if t_upper in ("ASC", "DESC"):
                    direction = t_upper
                    break  # 第一个 ASC/DESC 就用 (从左到右扫)
            seg_to_dir[col_name.lower()] = direction

        return [seg_to_dir.get(col.lower(), "ASC") for col in self._cursor_columns]

    @staticmethod
    def _strip_strings_and_comments(sql: str) -> str:
        """生成一个与原 sql 等长的 mask 串,字符串字面量/注释内的字符替换为空格。

        H1+H3 共用: SQL 结构扫描时用 mask 找括号/关键字,避免被字符串里的 ()/keyword 干扰;
        最终返回原 sql,但内部扫描时用 mask 判断"位置 i 是否在字符串/注释里"。

        实现简化: 返回一个"字符串/注释字符替换为空格"的同长 SQL,调用方在 mask 上做关键字扫描,
        然后用同一个索引 i 取原 sql 的 char。
        """
        n = len(sql)
        result = list(sql)
        i = 0
        while i < n:
            ch = sql[i]
            if ch == "'":
                result[i] = ' '
                i += 1
                while i < n:
                    if sql[i] == "'":
                        if i + 1 < n and sql[i + 1] == "'":
                            result[i] = ' '
                            result[i + 1] = ' '
                            i += 2
                            continue
                        result[i] = ' '
                        i += 1
                        break
                    result[i] = ' '
                    i += 1
                continue
            if ch == '"':
                result[i] = ' '
                i += 1
                while i < n and sql[i] != '"':
                    result[i] = ' '
                    i += 1
                if i < n:
                    result[i] = ' '
                    i += 1
                continue
            if ch == '-' and i + 1 < n and sql[i + 1] == '-':
                while i < n and sql[i] != '\n':
                    result[i] = ' '
                    i += 1
                continue
            if ch == '/' and i + 1 < n and sql[i + 1] == '*':
                result[i] = ' '
                result[i + 1] = ' '
                i += 2
                while i < n - 1 and not (sql[i] == '*' and sql[i + 1] == '/'):
                    result[i] = ' '
                    i += 1
                if i < n - 1:
                    result[i] = ' '
                    result[i + 1] = ' '
                    i += 2
                continue
            i += 1
        return "".join(result)

    def _find_top_level_order_by(self, sql: str) -> int:
        """B4+H3 修复: 用括号平衡扫描定位最外层 ORDER BY 子句的起点

        rfind 抓子查询 ORDER BY 的 case:
            SELECT ... WHERE x IN (SELECT y FROM u ORDER BY z) ORDER BY id DESC
        rfind 会取最后一个 ORDER BY (外层正确),但反过来:
            SELECT ... ORDER BY id DESC (子查询里有 ORDER BY z 但靠前)
            FROM (SELECT ... ORDER BY z) ...
        如果外层 ORDER BY 在子查询前面,rfind 会取子查询里的 ORDER BY。

        正确做法: 从右往左扫描,跳过括号包裹区域 + 字符串字面量,找到第一个 depth==0 的 ORDER BY。
        """
        masked = self._strip_strings_and_comments(sql)
        upper = masked.upper()
        # 从末尾向左找,深度 0 的 " ORDER BY "
        i = len(masked) - 1
        depth = 0
        while i >= 0:
            ch = masked[i]
            if ch == ')':
                depth += 1
            elif ch == '(':
                depth -= 1
            elif depth == 0 and i + 10 <= len(masked) and upper[i:i+10] == " ORDER BY ":
                return i
            i -= 1
        return -1

    def _has_top_level_where(self, sql: str) -> bool:
        """H2: 大小写不敏感地检测顶层(深度 0)的 WHERE 子句,跳字符串字面量"""
        masked = self._strip_strings_and_comments(sql)
        upper = masked.upper()
        i = 0
        depth = 0
        while i < len(masked):
            ch = masked[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif depth == 0 and upper[i:i+7] == " WHERE ":
                return True
            i += 1
        return False

    def _inject_keyset_predicate(
        self,
        sql: str,
        params: list,
        cursor_values: list,
    ) -> tuple[str, list]:
        """在 sql 的 ORDER BY 前插入 keyset 谓词

        S3 修复: 支持 ASC/DESC/混向。
        - 全 DESC: (col1, col2, ...) < (?, ?, ...)
        - 全 ASC:  (col1, col2, ...) > (?, ?, ...)
        - 混向: 展开成 OR 链,例如 (date DESC, id ASC):
              date < ? OR (date = ? AND id > ?)
          每个前缀级用对应方向的比较符。
        B4 修复: 用括号平衡扫描定位最外层 ORDER BY,避免抓子查询。
        """
        order_idx = self._find_top_level_order_by(sql)
        if order_idx < 0:
            raise ValueError("setQuery 的 sql 必须包含 ORDER BY 子句以使用 keyset 分页")
        head = sql[:order_idx]
        tail = sql[order_idx:]

        directions = self._cursor_directions or ["ASC"] * len(self._cursor_columns)
        if len(directions) != len(self._cursor_columns):
            directions = ["ASC"] * len(self._cursor_columns)

        # B5: cursor_values 含 None 时,row-value 比较和简单 OR 链都会因为 NULL 三值逻辑丢页
        # 强制走"含 NULL 守卫的 OR 链"
        has_null_cursor = any(v is None for v in cursor_values)

        # 全部同向 + 无 NULL → 用 row-value 比较 (SQLite 高效)
        all_desc = all(d == "DESC" for d in directions)
        all_asc = all(d == "ASC" for d in directions)
        if (all_desc or all_asc) and not has_null_cursor:
            cursor_cols_str = ", ".join(self._cursor_columns)
            placeholders = ", ".join(["?"] * len(self._cursor_columns))
            op = "<" if all_desc else ">"
            predicate = f"({cursor_cols_str}) {op} ({placeholders})"
            new_params = list(params) + list(cursor_values)
        else:
            # 混向 / 含 NULL: 展开 OR 链
            # 每级前缀: prev 列全等 (NULL 用 IS NULL 等价比较),当前列按方向 + NULL 守卫
            #   DESC + NULLS LAST: cursor=val 时 col<val OR col IS NULL
            #                      cursor=NULL 时 false (已末尾)
            #   ASC  + NULLS FIRST: cursor=val 时 col>val
            #                      cursor=NULL 时 col IS NOT NULL
            clauses = []
            new_params = list(params)

            def col_eq(col_idx: int) -> tuple[str, list]:
                """生成 col = cursor[col_idx] 的等价比较 (NULL-safe)"""
                col_name = self._cursor_columns[col_idx]
                v = cursor_values[col_idx]
                if v is None:
                    return f"{col_name} IS NULL", []
                return f"{col_name} = ?", [v]

            def col_gt(col_idx: int, direction: str) -> tuple[str, list]:
                """生成 col 在 cursor[col_idx] 的"下一行"方向的谓词 (NULL-safe)"""
                col_name = self._cursor_columns[col_idx]
                v = cursor_values[col_idx]
                if direction == "DESC":
                    # NULLS LAST: cursor=val → col<val OR col IS NULL
                    #             cursor=NULL → false
                    if v is None:
                        return "0", []  # 永远 false
                    return f"({col_name} < ? OR {col_name} IS NULL)", [v]
                else:
                    # ASC NULLS FIRST: cursor=val → col>val
                    #                  cursor=NULL → col IS NOT NULL
                    if v is None:
                        return f"{col_name} IS NOT NULL", []
                    return f"{col_name} > ?", [v]

            for i in range(len(self._cursor_columns)):
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

        if self._has_top_level_where(head):
            head_new = f"{head} AND {predicate}"
        else:
            head_new = f"{head} WHERE {predicate}"
        new_sql = head_new + tail
        return new_sql, new_params

    def _get_page(self, page_idx: int) -> tuple[list, Optional[list]]:
        """返回 (rows, end_cursor)"""
        cached = self._cache.get(page_idx)
        if cached is not None:
            self._touch_page(page_idx)
            return cached
        # 翻页时优先用上一页的 end_cursor (keyset 快路径)
        prev_cursor = None
        if self._cursor_columns and page_idx > 0:
            prev_entry = self._cache.get(page_idx - 1)
            if prev_entry is not None:
                _prev_rows, prev_cursor = prev_entry
        result = self._fetch_page(page_idx, end_cursor_of_prev=prev_cursor)
        rows = result["rows"]
        end_cursor = result.get("end_cursor")
        self._cache[page_idx] = (rows, end_cursor)
        self._touch_page(page_idx)
        # 淘汰 LRU 末尾
        while len(self._cache) > self._lru_capacity:
            self._cache.popitem(last=False)
        return rows, end_cursor

    def _touch_page(self, page_idx: int) -> None:
        try:
            self._cache.move_to_end(page_idx)
        except KeyError:
            pass


# 是否启用了 Rust 加速 (供调试/状态显示)
def is_rust_accelerated() -> bool:
    return _HAS_RUST
