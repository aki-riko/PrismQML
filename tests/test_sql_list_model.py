# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel behavior tests."""

from __future__ import annotations

import sqlite3


def _seed_records_db(tmp_path) -> str:
    db_path = tmp_path / "records.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE records ("
            "id INTEGER PRIMARY KEY, "
            "category TEXT NOT NULL, "
            "name TEXT NOT NULL, "
            "score INTEGER NOT NULL)"
        )
        conn.executemany(
            "INSERT INTO records (id, category, name, score) VALUES (?, ?, ?, ?)",
            [
                (1, "alpha", "alice", 20),
                (2, "alpha", "bob", 30),
                (3, "alpha", "carol", 10),
                (4, "alpha", "dora", 20),
                (5, "beta", "eric", 90),
            ],
        )
    return str(db_path)


def test_sql_list_model_dict_params_keyset_and_formatters(tmp_path):
    from prismqml.python.models.sql_list_model import SqlListModel

    model = SqlListModel(_seed_records_db(tmp_path), page_size=2, lru_capacity=4)
    model.setQuery(
        """
        SELECT id, category, name, score, ':category' AS marker
        FROM records
        WHERE category=:category
          AND score >= :min_score
          AND name != ':category'
          -- :commented_placeholder
        ORDER BY score DESC, id ASC
        """,
        """
        SELECT COUNT(*)
        FROM records
        WHERE score >= :min_score AND category=:category
        """,
        params={"category": "alpha", "min_score": 0},
        formatters={"name": lambda value: value.upper()},
        cursor_columns=["score", "id"],
    )

    assert model.count() == 4
    assert model.rowCount() == 4

    assert model.getRow(0) == {
        "id": 2,
        "category": "alpha",
        "name": "BOB",
        "score": 30,
        "marker": ":category",
    }
    assert model.getRow(1)["id"] == 1
    assert model.getRow(2)["id"] == 4
    assert model.getRow(3)["id"] == 3
    assert model.getRow(4) == {}


def test_sql_list_model_role_names_are_select_columns(tmp_path):
    from prismqml.python.models.sql_list_model import SqlListModel

    model = SqlListModel(_seed_records_db(tmp_path))
    model.setQuery(
        "SELECT id, name AS display_name FROM records WHERE category=? ORDER BY id",
        "SELECT COUNT(*) FROM records WHERE category=?",
        params=["beta"],
    )

    role_names = {role: bytes(name).decode("utf-8") for role, name in model.roleNames().items()}

    assert list(role_names.values()) == ["id", "display_name"]
    assert model.getRow(0) == {"id": 5, "display_name": "eric"}
