# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

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
    from prismqml import SqlListModel
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

Keyset 分页使用严格合同：ORDER BY 必须与 cursor_columns 完全一致；简单裸列排序
会在库内规范化为 COLLATE BINARY。nullable_cursor_column 最多声明一个可空的
非末列；未传时默认倒数第二列，传空字符串表示全部非空。其余 cursor 列必须有
schema NOT NULL 约束，最终 tie-breaker 还必须跨 shard 全局唯一。
查询主体只支持简单顶层 SELECT；唯一例外是顶层 WHERE 内一个简单的
IN (SELECT 单列 FROM 单表 WHERE 条件) 子查询。
"""
from __future__ import annotations

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

from ._page_cache import PageCache
from ._sql_query_tools import (
    inject_keyset_predicate,
    normalize_keyset_order,
    normalize_one,
    resolve_nullable_cursor_index,
)
from ._sql_page_loader import SqlPageLoaderMixin

# 优先 Rust 实现
try:
    import prismqml_rs as _rs  # noqa: WPS433

    _HAS_RUST = True
except ImportError:
    _rs = None
    _HAS_RUST = False


PAGE_SIZE_DEFAULT = 1000
LRU_CAPACITY_DEFAULT = 64  # 64 页 × 1000 行 = 6.4w 行内存常驻;1B+ 跨片 random access 也少触发淘汰
_QUERY_STATE_FIELDS = (
    "_sql", "_count_sql", "_params", "_count_params", "_formatters",
    "_cursor_columns", "_cursor_nullable_index", "_cursor_col_indices",
    "_cursor_directions", "_row_count", "_columns", "_role_to_col",
    "_role_names", "_cache",
)


def _copy_query_state_value(value):
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _validate_keyset_request(
    sql: str,
    params: Optional[Union[list, tuple, dict]],
    cursor_columns: Optional[list],
    cursor_directions: Optional[list],
    nullable_cursor_column: Optional[str],
) -> tuple[str, list, Optional[int]]:
    columns = list(cursor_columns) if cursor_columns else []
    normalized_sql, normalized_params = normalize_one(sql, params)
    if not columns:
        if nullable_cursor_column not in (None, ""):
            raise ValueError("nullable_cursor_column 需要同时设置 cursor_columns")
        return normalized_sql, normalized_params, None
    normalized_sql = normalize_keyset_order(
        normalized_sql, columns, cursor_directions
    )
    nullable_index = resolve_nullable_cursor_index(
        columns, nullable_cursor_column
    )
    return normalized_sql, normalized_params, nullable_index


def _normalize_count_query(
    count_sql: str,
    params: Optional[Union[list, tuple, dict]],
    count_params: Optional[Union[list, tuple, dict]],
) -> tuple[str, list]:
    effective_params = params if count_params is None else count_params
    return normalize_one(count_sql, effective_params)


def _prepare_query_inputs(
    sql, count_sql, params, formatters, cursor_columns, count_params,
    cursor_directions, nullable_cursor_column,
) -> tuple:
    prepared_sql, prepared_params, nullable_index = _validate_keyset_request(
        sql, params, cursor_columns, cursor_directions, nullable_cursor_column
    )
    return (
        prepared_sql, prepared_params, count_sql, params, count_params,
        formatters, cursor_columns, nullable_index,
    )


def _initialize_empty_query_state(owner: Any) -> None:
    owner._sql: str = ""
    owner._count_sql: str = ""
    owner._params: list = []  # 顺序参数,绑定到 ? 占位符
    owner._count_params: list = []  # count_sql 的独立参数(默认 = owner._params)
    owner._formatters: dict[str, callable] = {}  # column_name -> formatter callable
    # keyset 分页支持: cursor_columns 是 ORDER BY 前缀列名,例如 ['date', 'time', 'id']
    owner._cursor_columns: list[str] = []
    owner._cursor_nullable_index: Optional[int] = None
    owner._cursor_col_indices: list[int] = []  # cursor_columns 在 SELECT 中的下标
    owner._cursor_directions: list[str] = []  # 每个 cursor 列的 ASC/DESC (S3, _resolve_columns 填充)
    # _cursor_keyset_clause 是 "(date, time, id) < (?, ?, ?)" 谓词模板,首次构建后缓存
    owner._row_count: int = 0
    # 列名(roleNames 用) — 首次 fetch 后填充
    owner._columns: list[str] = []
    # role id → column index 映射
    owner._role_to_col: dict[int, int] = {}
    # role name → role id (供 QML)
    owner._role_names: dict[int, QByteArray] = {}
    # LRU page cache: page_idx → (rows, end_cursor)
    owner._cache = PageCache(owner._lru_capacity)


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


class SqlListModel(SqlPageLoaderMixin, QAbstractListModel):
    """SQLite 分页 list model,QML ListView/TableView 直接消费。

    Keyset 查询必须用匿名 ``?`` 或 dict 参数；ORDER BY 必须与
    ``cursor_columns`` 完全一致，简单裸列会被规范化为 ``COLLATE BINARY``。
    ``nullable_cursor_column`` 最多声明一个非末列；未传时默认倒数第二列，传
    空字符串表示全部非空。其余 cursor 输出必须由 schema ``NOT NULL`` 或等价
    表达式构造保证，末列还必须跨 shard 全局唯一。
    查询主体只允许简单顶层 ``SELECT``；唯一例外是顶层 ``WHERE`` 内一个简单
    ``IN (SELECT 单列 FROM 单表 WHERE 条件)`` 子查询。
    """

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
        _initialize_empty_query_state(self)

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
        nullable_cursor_column: Optional[str] = None,
    ) -> None:
        """Set the paged query; see the class keyset contract. 设置分页查询。"""
        query_inputs = _prepare_query_inputs(
            sql, count_sql, params, formatters, cursor_columns, count_params,
            cursor_directions, nullable_cursor_column,
        )
        self._replace_query(query_inputs)
        self.queryChanged.emit()
        self.countChanged.emit()

    def _replace_query(self, query_inputs: tuple) -> None:
        previous_state = self._capture_query_state()
        succeeded = False
        self.beginResetModel()
        try:
            self._set_query_inputs(*query_inputs)
            self._prepare_query_results()
            succeeded = True
        finally:
            if not succeeded:
                self._restore_query_state(previous_state)
            self.endResetModel()

    def _capture_query_state(self) -> dict:
        return {
            name: _copy_query_state_value(getattr(self, name, None))
            for name in _QUERY_STATE_FIELDS
        }

    def _restore_query_state(self, state: dict) -> None:
        for name, value in state.items():
            setattr(self, name, value)

    def _set_query_inputs(
        self, sql, sql_params, count_sql, params, count_params,
        formatters, cursor_columns, nullable_cursor_index,
    ) -> None:
        self._sql = sql
        self._params = list(sql_params)
        self._count_sql, self._count_params = _normalize_count_query(
            count_sql, params, count_params
        )
        self._formatters = dict(formatters) if formatters else {}
        self._cursor_columns = list(cursor_columns) if cursor_columns else []
        self._cursor_nullable_index = nullable_cursor_index
        self._cursor_col_indices = []

    def _prepare_query_results(self) -> None:
        self._cache = PageCache(self._lru_capacity)
        self._row_count = self._compute_count()
        self._columns = []
        self._role_to_col = {}
        self._role_names = {}
        self._resolve_columns()
        if self._row_count > 0:
            first_page = self._fetch_page(0)
            self._cache.put(0, first_page["rows"], first_page.get("end_cursor"))

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
        previous_state = self._capture_query_state()
        succeeded = False
        self.beginResetModel()
        try:
            self._cache = PageCache(self._lru_capacity)
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
                self._cache.put(0, first["rows"], first.get("end_cursor"))
            succeeded = True
        finally:
            if not succeeded:
                self._restore_query_state(previous_state)
            self.endResetModel()
        self.countChanged.emit()

    @Slot(int, result="QVariantMap")
    def getRow(self, row: int) -> dict:
        """按行索引返回该行所有列的 dict (column_name → value),供 QML 弹窗读单条详情"""
        if row < 0 or row >= self._row_count or not self._columns:
            return {}
        page_idx = row // self._page_size
        offset_in_page = row - page_idx * self._page_size
        page = self._get_page_for_access(page_idx, row, "getRow")
        if page is None:
            return {}
        rows, _end_cursor = page
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
        page = self._get_page_for_access(page_idx, row, "data")
        if page is None:
            return None
        rows, _end_cursor = page
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
    # Backend Bridges 后端桥接
    # ============================================================

    @staticmethod
    def _rust_is_available() -> bool:
        return _HAS_RUST

    @staticmethod
    def _rust_module():
        return _rs

    @staticmethod
    def _inject_keyset_predicate(
        sql: str,
        params: list,
        cursor_values: list,
        cursor_columns: list[str],
        cursor_directions: list[str],
        nullable_cursor_index: Optional[int] = None,
    ) -> tuple[str, list]:
        return inject_keyset_predicate(
            sql, params, cursor_values, cursor_columns,
            cursor_directions, nullable_cursor_index,
        )


# 是否启用了 Rust 加速 (供调试/状态显示)
def is_rust_accelerated() -> bool:
    return _HAS_RUST
