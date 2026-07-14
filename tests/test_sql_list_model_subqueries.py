# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel simple IN-subquery contracts. 简单 IN 子查询合同。"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from prismqml.python.models import sql_list_model
from prismqml.python.models._sql_query_tools import inject_keyset_predicate


_ROWS = [
    (1, 3, 2),
    (2, 3, None),
    (3, 2, 5),
    (4, 2, 1),
    (5, 1, None),
    (6, 1, 4),
    (7, 4, 9),
]
_ORDER_CASES = [
    pytest.param("c1 DESC, c2 DESC, id DESC", id="desc"),
    pytest.param("c1 ASC, c2 ASC, id ASC", id="asc"),
]


def _write_subquery_db(path) -> str:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, "
            "c1 INTEGER NOT NULL, c2 INTEGER)"
        )
        conn.execute(
            "CREATE TABLE matches (item_id INTEGER PRIMARY KEY, token TEXT NOT NULL)"
        )
        conn.executemany("INSERT INTO items VALUES (?, ?, ?)", _ROWS)
        conn.executemany(
            "INSERT INTO matches VALUES (?, ?)",
            [(item_id, "keep") for item_id in range(1, 7)] + [(7, "drop")],
        )
        conn.commit()
    return str(path)


def _query(order_by: str) -> str:
    return (
        "SELECT id, c1, c2 FROM items WHERE id IN "
        "(SELECT item_id FROM matches WHERE token = ?) "
        f"ORDER BY {order_by}"
    )


def _expected_ids(db_path: str, sql: str) -> list[int]:
    with closing(sqlite3.connect(db_path)) as conn:
        return [row[0] for row in conn.execute(sql, ["keep"])]


def _collect_ids(model) -> list[int]:
    rows = [model.getRow(index) for index in range(model.count())]
    assert all(rows), rows
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)) == model.count()
    return ids


@pytest.mark.parametrize("order_by", _ORDER_CASES)
@pytest.mark.parametrize("rust_enabled", [True, False], ids=["rust", "python"])
def test_simple_in_subquery_matches_sqlite_oracle(
    tmp_path, monkeypatch, order_by, rust_enabled
):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _write_subquery_db(tmp_path / "subquery.sqlite")
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    sql = _query(order_by)
    model = sql_list_model.SqlListModel(db_path, page_size=1, lru_capacity=1)
    model.setQuery(
        sql,
        "SELECT COUNT(*) FROM items WHERE id IN "
        "(SELECT item_id FROM matches WHERE token = ?)",
        params=["keep"],
        cursor_columns=["c1", "c2", "id"],
    )

    assert model._cursor_nullable_index == 1
    assert _collect_ids(model) == _expected_ids(db_path, sql)


def test_simple_in_subquery_uses_one_guarded_source():
    sql, params = inject_keyset_predicate(
        _query(
            "c1 COLLATE BINARY DESC, c2 COLLATE BINARY DESC, "
            "id COLLATE BINARY DESC"
        ),
        ["keep"],
        [3, 2, 1],
        ["c1", "c2", "id"],
        ["DESC", "DESC", "DESC"],
        1,
    )

    assert sql.count("SELECT item_id FROM matches") == 1
    assert "c1 <= ? COLLATE BINARY AND" in sql
    assert "UNION ALL" not in sql
    assert params == ["keep", 3, 3, 3, 2, 3, 2, 1]


@pytest.mark.parametrize(
    "predicate",
    [
        "id NOT IN (SELECT item_id FROM matches WHERE token = 'keep')",
        "id IN (SELECT item_id, token FROM matches WHERE token = 'keep')",
        "id IN (SELECT DISTINCT item_id FROM matches WHERE token = 'keep')",
        "id IN (SELECT item_id FROM matches)",
        "id IN (SELECT item_id FROM matches WHERE token = 'keep' ORDER BY item_id)",
        "id IN (SELECT item_id FROM matches WHERE (token = 'keep'))",
        (
            "id IN (SELECT item_id FROM matches WHERE token = 'keep') OR "
            "id IN (SELECT item_id FROM matches WHERE token = 'drop')"
        ),
    ],
)
def test_unsupported_in_subquery_shapes_are_rejected(tmp_path, predicate):
    model = sql_list_model.SqlListModel(
        _write_subquery_db(tmp_path / "rejected.sqlite"), page_size=1
    )
    with pytest.raises(ValueError, match="IN|子查询|嵌套"):
        model.setQuery(
            f"SELECT id, c1, c2 FROM items WHERE {predicate} "
            "ORDER BY c1 DESC, c2 DESC, id DESC",
            "SELECT COUNT(*) FROM items",
            cursor_columns=["c1", "c2", "id"],
        )
