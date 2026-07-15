# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel named-token integration tests. 命名参数模型集成回归。"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from prismqml.python.models import sql_list_model


_ROWS = (
    (1, "alpha", 10, "m1", "o1", 100),
    (2, "alpha", 20, "m2", "o2", 200),
    (3, "alpha", 30, "m3", "o3", 300),
    (4, "beta", 20, "m4", "o4", 400),
)


class _StaticRouter(sql_list_model.DbRouter):
    def __init__(self, paths):
        self._paths = list(paths)

    def route(self, _params):
        return list(self._paths)


def _write_named_db(path, rows) -> str:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE records("
            "id INTEGER PRIMARY KEY, category TEXT, score INTEGER, "
            "[metric:x] TEXT, `owner@id` TEXT, a$b INTEGER)"
        )
        connection.executemany("INSERT INTO records VALUES (?, ?, ?, ?, ?, ?)", rows)
        connection.commit()
    return str(path)


def _set_named_query(model) -> None:
    model.setQuery(
        "SELECT id, [metric:x] AS metric, `owner@id` AS owner, a$b AS cash "
        "FROM records WHERE category=:category "
        "AND score>=@minimum::score(bound) AND score<=$maximum ORDER BY id",
        "SELECT COUNT(*) FROM records WHERE category=@category "
        "AND score>=$minimum::score(bound) AND score<=:maximum",
        params={
            "category": "alpha",
            "minimum::score(bound)": 20,
            "maximum": 30,
        },
        cursor_columns=["id"],
    )


def _role_id(model, name):
    return next(
        role
        for role, role_name in model.roleNames().items()
        if bytes(role_name).decode("utf-8") == name
    )


@pytest.mark.parametrize("rust_enabled", (True, False), ids=("rust", "python"))
def test_sql_list_model_named_tokens_match_sqlite(
    tmp_path, monkeypatch, rust_enabled
):
    if rust_enabled and sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    db_path = _write_named_db(tmp_path / "named.sqlite", _ROWS)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    model = sql_list_model.SqlListModel(db_path, page_size=1, lru_capacity=1)

    _set_named_query(model)

    assert model.count() == 2
    assert list(bytes(name).decode("utf-8") for name in model.roleNames().values()) == [
        "id", "metric", "owner", "cash",
    ]
    assert model.getRow(0) == {
        "id": 2, "metric": "m2", "owner": "o2", "cash": 200,
    }
    assert model.getRow(1) == {
        "id": 3, "metric": "m3", "owner": "o3", "cash": 300,
    }
    assert model.data(model.index(1, 0), _role_id(model, "owner")) == "o3"


def test_rust_fan_out_preserves_named_parameter_order(tmp_path, monkeypatch):
    if sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    first = _write_named_db(tmp_path / "first.sqlite", _ROWS[::2])
    second = _write_named_db(tmp_path / "second.sqlite", _ROWS[1::2])
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", True)
    model = sql_list_model.SqlListModel(
        _StaticRouter([first, second]), page_size=1, lru_capacity=1
    )

    _set_named_query(model)

    assert model.count() == 2
    assert [model.getRow(index)["id"] for index in range(model.count())] == [2, 3]
