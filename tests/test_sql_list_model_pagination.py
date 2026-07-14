# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel keyset pagination contracts. SQL 列表游标分页合同。"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from prismqml.python.models import sql_list_model
from prismqml.python.models._sql_query_tools import inject_keyset_predicate


# rank intentionally repeats; id is the globally unique final tie-breaker.
_ROWS = [
    (1, None),
    (2, None),
    (3, 3),
    (4, 4),
    (5, 2),
    (6, 3),
    (7, 2),
    (8, 2),
    (9, 5),
    (10, 5),
    (11, None),
    (12, 1),
]
_ORDER_CASES = [
    pytest.param("rank COLLATE BINARY ASC, id COLLATE BINARY ASC", id="asc"),
    pytest.param("rank COLLATE BINARY DESC, id COLLATE BINARY DESC", id="desc"),
    pytest.param("rank COLLATE BINARY DESC, id COLLATE BINARY ASC", id="mixed"),
]
_DEEP_NULL_ROWS = [
    (1, 3, 2),
    (2, 3, None),
    (3, 2, 5),
    (4, 2, 1),
    (5, 1, None),
]


class _StaticRouter(sql_list_model.DbRouter):
    def __init__(self, paths):
        self._paths = list(paths)

    def route(self, _params):
        return list(self._paths)


def _write_db(path, rows) -> str:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, rank INTEGER)")
        conn.executemany("INSERT INTO items (id, rank) VALUES (?, ?)", rows)
        conn.commit()
    return str(path)


def _single_db(tmp_path) -> str:
    return _write_db(tmp_path / "single.sqlite", _ROWS)


def _sharded_dbs(tmp_path) -> tuple[list[str], str]:
    first = _write_db(tmp_path / "shard-a.sqlite", _ROWS[::2])
    second = _write_db(tmp_path / "shard-b.sqlite", _ROWS[1::2])
    oracle = _write_db(tmp_path / "oracle.sqlite", _ROWS)
    return [first, second], oracle


def _expected_ids(db_path: str, order_by: str) -> list[int]:
    with closing(sqlite3.connect(db_path)) as conn:
        return [
            row[0]
            for row in conn.execute(
                f"SELECT id FROM items ORDER BY {order_by}"
            ).fetchall()
        ]


def _write_deep_null_db(path) -> str:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, "
            "c1 INTEGER NOT NULL, c2 INTEGER)"
        )
        conn.executemany(
            "INSERT INTO items (id, c1, c2) VALUES (?, ?, ?)",
            _DEEP_NULL_ROWS,
        )
        conn.commit()
    return str(path)


def _collect_expected_deep_ids(db_path: str) -> list[int]:
    with closing(sqlite3.connect(db_path)) as conn:
        return [
            row[0]
            for row in conn.execute(
                "SELECT id FROM items ORDER BY c1 COLLATE BINARY DESC, "
                "c2 COLLATE BINARY DESC, id COLLATE BINARY DESC"
            )
        ]


def _new_model(source, order_by: str):
    model = sql_list_model.SqlListModel(source, page_size=2, lru_capacity=1)
    model.setQuery(
        f"SELECT id, rank FROM items ORDER BY {order_by}",
        "SELECT COUNT(*) FROM items",
        cursor_columns=["rank", "id"],
        nullable_cursor_column="rank",
    )
    return model


def _collect_ids(model) -> list[int]:
    rows = [model.getRow(index) for index in range(model.count())]
    assert all(rows), rows
    ids = [row["id"] for row in rows]
    assert len(ids) == model.count()
    assert len(set(ids)) == len(ids)
    return ids


@pytest.mark.parametrize("order_by", _ORDER_CASES)
@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_single_db_keyset_matches_sqlite_oracle(
    tmp_path, monkeypatch, order_by, rust_enabled
):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _single_db(tmp_path)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)

    model = _new_model(db_path, order_by)

    assert model.count() == len(_ROWS)
    assert _collect_ids(model) == _expected_ids(db_path, order_by)


@pytest.mark.parametrize("order_by", _ORDER_CASES)
def test_fan_out_keyset_matches_global_sqlite_oracle(
    tmp_path, monkeypatch, order_by
):
    if sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    paths, oracle = _sharded_dbs(tmp_path)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", True)

    model = _new_model(_StaticRouter(paths), order_by)

    assert model.count() == len(_ROWS)
    assert _collect_ids(model) == _expected_ids(oracle, order_by)


@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_later_nullable_cursor_key_matches_oracle(
    tmp_path, monkeypatch, rust_enabled
):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _write_deep_null_db(tmp_path / "deep-null.sqlite")
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    model = sql_list_model.SqlListModel(db_path, page_size=1, lru_capacity=1)
    model.setQuery(
        "SELECT id, c1, c2 FROM items ORDER BY c1 COLLATE BINARY DESC, "
        "c2 COLLATE BINARY DESC, id COLLATE BINARY DESC",
        "SELECT COUNT(*) FROM items",
        cursor_columns=["c1", "c2", "id"],
        nullable_cursor_column="c2",
    )
    assert _collect_ids(model) == _collect_expected_deep_ids(db_path)


@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_bare_order_uses_binary_and_default_later_nullable_column(
    tmp_path, monkeypatch, rust_enabled
):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _write_deep_null_db(tmp_path / "bare-order.sqlite")
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    model = sql_list_model.SqlListModel(db_path, page_size=1, lru_capacity=1)
    model.setQuery(
        "SELECT id, c1, c2 FROM items ORDER BY c1 DESC, c2 DESC, id DESC",
        "SELECT COUNT(*) FROM items",
        cursor_columns=["c1", "c2", "id"],
    )

    assert model._sql.endswith(
        "ORDER BY c1 COLLATE BINARY DESC, c2 COLLATE BINARY DESC, "
        "id COLLATE BINARY DESC"
    )
    assert model._cursor_nullable_index == 1
    assert _collect_ids(model) == _collect_expected_deep_ids(db_path)


@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_desc_union_repeats_base_params(tmp_path, monkeypatch, rust_enabled):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _single_db(tmp_path)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    model = sql_list_model.SqlListModel(db_path, page_size=2, lru_capacity=1)
    model.setQuery(
        "SELECT id, rank FROM items WHERE id >= :minimum "
        "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
        "SELECT COUNT(*) FROM items WHERE id >= :minimum",
        params={"minimum": 4},
        cursor_columns=["rank", "id"],
        nullable_cursor_column="rank",
    )
    expected = [
        value
        for value in _expected_ids(
            db_path,
            "rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
        )
        if value >= 4
    ]
    assert _collect_ids(model) == expected


def test_desc_union_sql_and_params_are_branch_ordered():
    sql, params = inject_keyset_predicate(
        "SELECT id, rank FROM items WHERE id >= ? "
        "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
        [4],
        [3, 2],
        ["rank", "id"],
        ["DESC", "DESC"],
        0,
    )
    assert sql.count("UNION ALL") == 1
    assert params == [4, 3, 2, 4]


def test_nullable_final_tie_breaker_is_rejected(tmp_path):
    model = sql_list_model.SqlListModel(_single_db(tmp_path), page_size=1)
    with pytest.raises(ValueError, match="UNIQUE NOT NULL"):
        model.setQuery(
            "SELECT id, rank FROM items ORDER BY rank COLLATE BINARY DESC, "
            "id COLLATE BINARY DESC",
            "SELECT COUNT(*) FROM items",
            cursor_columns=["rank", "id"],
            nullable_cursor_column="id",
        )


def test_unknown_nullable_cursor_column_is_rejected(tmp_path):
    model = sql_list_model.SqlListModel(_single_db(tmp_path), page_size=1)
    with pytest.raises(ValueError, match="必须属于 cursor_columns"):
        model.setQuery(
            "SELECT id, rank FROM items ORDER BY rank COLLATE BINARY DESC, "
            "id COLLATE BINARY DESC",
            "SELECT COUNT(*) FROM items",
            cursor_columns=["rank", "id"],
            nullable_cursor_column="missing",
        )


@pytest.mark.parametrize(
    "sql",
    [
        "WITH source AS (SELECT * FROM items) SELECT id, rank FROM source ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
        "SELECT id, rank FROM items GROUP BY rank ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
        "SELECT id, rank FROM items ORDER BY items.rank COLLATE BINARY DESC, items.id COLLATE BINARY DESC",
        "SELECT id, rank FROM items ORDER BY rank COLLATE NOCASE DESC, id COLLATE BINARY DESC",
        "SELECT id, rank FROM items ORDER BY rank COLLATE BINARY DESC NULLS FIRST, id COLLATE BINARY DESC",
        "SELECT id, rank FROM items ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC LIMIT 2",
        "SELECT id, row_number() OVER (ORDER BY rank) AS rank FROM items ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
        "SELECT id, rank FROM (SELECT id, row_number() OVER (ORDER BY rank) AS rank FROM items) ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
    ],
)
def test_unsupported_keyset_sql_is_rejected(tmp_path, sql):
    model = sql_list_model.SqlListModel(_single_db(tmp_path), page_size=1)
    with pytest.raises(ValueError, match="keyset|ORDER BY"):
        model.setQuery(
            sql,
            "SELECT COUNT(*) FROM items",
            cursor_columns=["rank", "id"],
            nullable_cursor_column="rank",
        )


def test_numbered_keyset_placeholder_is_rejected(tmp_path):
    model = sql_list_model.SqlListModel(_single_db(tmp_path), page_size=1)
    with pytest.raises(ValueError, match=r"不支持 \?NNN"):
        model.setQuery(
            "SELECT id, rank FROM items WHERE id >= ?1 "
            "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
            "SELECT COUNT(*) FROM items WHERE id >= ?1",
            params=[1],
            cursor_columns=["rank", "id"],
            nullable_cursor_column="rank",
        )


def test_duplicate_output_names_are_rejected(tmp_path):
    model = _new_model(
        _single_db(tmp_path),
        "rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
    )
    snapshot = _model_snapshot(model)
    with pytest.raises(ValueError, match="输出列名必须唯一"):
        model.setQuery(
            "SELECT id AS rank, rank FROM items ORDER BY rank COLLATE BINARY DESC, "
            "id COLLATE BINARY DESC",
            "SELECT COUNT(*) FROM items",
            cursor_columns=["rank", "id"],
            nullable_cursor_column="rank",
        )
    assert _model_snapshot(model) == snapshot


def test_cursor_direction_override_must_match_sql(tmp_path):
    model = sql_list_model.SqlListModel(_single_db(tmp_path), page_size=1)
    model.setQuery(
        "SELECT id, rank FROM items ORDER BY rank COLLATE BINARY DESC, "
        "id COLLATE BINARY DESC",
        "SELECT COUNT(*) FROM items",
        cursor_columns=["rank", "id"],
        nullable_cursor_column="rank",
    )
    original_count = model.count()
    original_first = model.getRow(0)
    with pytest.raises(ValueError, match="cursor_directions"):
        model.setQuery(
            "SELECT id, rank FROM items ORDER BY rank COLLATE BINARY DESC, "
            "id COLLATE BINARY DESC",
            "SELECT COUNT(*) FROM items",
            cursor_columns=["rank", "id"],
            cursor_directions=["ASC", "ASC"],
            nullable_cursor_column="rank",
        )
    assert model.count() == original_count
    assert model.getRow(0) == original_first


@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_output_alias_keyset_matches_oracle(tmp_path, monkeypatch, rust_enabled):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _single_db(tmp_path)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    model = sql_list_model.SqlListModel(db_path, page_size=2, lru_capacity=1)
    sql = (
        "SELECT id, -rank AS rank FROM items "
        "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC"
    )
    model.setQuery(
        sql,
        "SELECT COUNT(*) FROM items",
        cursor_columns=["rank", "id"],
        nullable_cursor_column="rank",
    )
    with closing(sqlite3.connect(db_path)) as conn:
        expected = [row[0] for row in conn.execute(sql)]
    assert _collect_ids(model) == expected


@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_newline_where_keyset_matches_oracle(
    tmp_path, monkeypatch, rust_enabled
):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _single_db(tmp_path)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    model = sql_list_model.SqlListModel(db_path, page_size=2, lru_capacity=1)
    sql = (
        "SELECT id, rank FROM items\nWHERE id >= ? "
        "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC"
    )
    model.setQuery(
        sql,
        "SELECT COUNT(*) FROM items WHERE id >= ?",
        params=[4],
        cursor_columns=["rank", "id"],
        nullable_cursor_column="rank",
    )
    with closing(sqlite3.connect(db_path)) as conn:
        expected = [row[0] for row in conn.execute(sql, [4])]
    assert _collect_ids(model) == expected


def _model_snapshot(model) -> tuple:
    first_row = model.getRow(0)
    cache_pages = tuple(
        (
            page_index,
            tuple(tuple(row) for row in rows),
            tuple(end_cursor) if end_cursor is not None else None,
        )
        for page_index, (rows, end_cursor) in model._cache._pages.items()
    )
    return (
        model.count(), first_row, model._sql, model._count_sql,
        tuple(model._params), tuple(model._count_params),
        tuple(model._columns), tuple(model.roleNames().items()),
        tuple(model._cursor_columns), tuple(model._cursor_directions),
        model._cursor_nullable_index, id(model._cache), cache_pages,
    )


@pytest.mark.parametrize(
    "placeholder",
    [":minimum", ":最小", "@名字", "$名字", ":1", "@1", "$1"],
)
def test_residual_named_placeholder_preserves_previous_query(
    tmp_path, placeholder
):
    model = _new_model(
        _single_db(tmp_path),
        "rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
    )
    original_count = model.count()
    original_first = model.getRow(0)
    with pytest.raises(ValueError, match="命名占位符"):
        model.setQuery(
            f"SELECT id, rank FROM items WHERE id >= {placeholder} "
            "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
            f"SELECT COUNT(*) FROM items WHERE id >= {placeholder}",
            params=[1],
            cursor_columns=["rank", "id"],
            nullable_cursor_column="rank",
        )
    assert model.count() == original_count
    assert model.getRow(0) == original_first


@pytest.mark.parametrize(
    ("sql", "params", "count_params", "error"),
    [
        pytest.param(
            "SELECT id, rank FROM items WHERE id >= ? AND rank >= ? "
            "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
            [1], [], sqlite3.ProgrammingError, id="bind-mismatch",
        ),
        pytest.param(
            "SELECT rank FROM items ORDER BY rank COLLATE BINARY DESC, "
            "id COLLATE BINARY DESC",
            [], None, ValueError, id="missing-cursor-output",
        ),
    ],
)
def test_query_prepare_failure_restores_previous_state(
    tmp_path, sql, params, count_params, error
):
    model = _new_model(
        _single_db(tmp_path),
        "rank COLLATE BINARY DESC, id COLLATE BINARY DESC",
    )
    snapshot = _model_snapshot(model)
    with pytest.raises(error):
        model.setQuery(
            sql,
            "SELECT COUNT(*) FROM items",
            params=params,
            count_params=count_params,
            cursor_columns=["rank", "id"],
            nullable_cursor_column="rank",
        )
    assert _model_snapshot(model) == snapshot


def _write_text_db(path, rows) -> str:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, "
            "name TEXT NOT NULL COLLATE NOCASE)"
        )
        conn.executemany("INSERT INTO items VALUES (?, ?)", rows)
        conn.commit()
    return str(path)


def test_fan_out_explicit_binary_collation_matches_sqlite(tmp_path):
    if sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    first = _write_text_db(tmp_path / "text-a.sqlite", [(1, "a"), (3, "c")])
    second = _write_text_db(tmp_path / "text-b.sqlite", [(2, "B"), (4, "Z")])
    oracle = _write_text_db(
        tmp_path / "text-oracle.sqlite",
        [(1, "a"), (2, "B"), (3, "c"), (4, "Z")],
    )
    order_by = "name COLLATE BINARY ASC, id COLLATE BINARY ASC"
    model = sql_list_model.SqlListModel(
        _StaticRouter([first, second]), page_size=2, lru_capacity=1
    )
    model.setQuery(
        f"SELECT id, name FROM items ORDER BY {order_by}",
        "SELECT COUNT(*) FROM items",
        cursor_columns=["name", "id"],
    )
    assert _collect_ids(model) == _expected_ids(oracle, order_by)
