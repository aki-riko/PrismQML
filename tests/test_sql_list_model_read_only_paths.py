# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel read-only path contracts. SQL 只读路径合同。"""

import ast
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from prismqml.python.models import _sqlite_connection, sql_list_model


_QUERY = "SELECT id, name FROM records ORDER BY id"
_COUNT_QUERY = "SELECT COUNT(*) FROM records"
_PATH_CASES = (
    (
        r"C:\Data Folder\图 表#百分%23?问.sqlite",
        "file:///C:/Data%20Folder/%E5%9B%BE%20%E8%A1%A8%23"
        "%E7%99%BE%E5%88%86%2523%3F%E9%97%AE.sqlite?mode=ro",
    ),
    (
        "/tmp/图 表#百分%23?问.sqlite",
        "file:///tmp/%E5%9B%BE%20%E8%A1%A8%23%E7%99%BE%E5%88%86"
        "%2523%3F%E9%97%AE.sqlite?mode=ro",
    ),
    (
        r"\\server\share name\图 表#百分%23?问.sqlite",
        "file:////server/share%20name/%E5%9B%BE%20%E8%A1%A8%23"
        "%E7%99%BE%E5%88%86%2523%3F%E9%97%AE.sqlite?mode=ro",
    ),
)


def _select_backend(monkeypatch, backend):
    if backend == "rust" and not sql_list_model._HAS_RUST:
        pytest.skip("Rust backend is not available")
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", backend == "rust")


def _write_db(path):
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE records(id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO records VALUES (?, ?)",
            ((1, "甲"), (2, "乙")),
        )
        connection.commit()


def _sqlite_connect_owners(module):
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    owners = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "sqlite3"
            and target.attr == "connect"
        ):
            continue
        owner = parents.get(node)
        while owner is not None and not isinstance(owner, ast.FunctionDef):
            owner = parents.get(owner)
        owners.append(owner.name if owner is not None else "<module>")
    return owners


@pytest.mark.parametrize(("path", "expected"), _PATH_CASES)
def test_sqlite_read_only_uri_encodes_path_once(path, expected):
    assert _sqlite_connection.sqlite_read_only_uri(path) == expected


def test_all_python_sqlite_reads_use_shared_read_only_connection():
    assert _sqlite_connect_owners(_sqlite_connection) == ["open_read_only"]
    assert _sqlite_connect_owners(sql_list_model) == []


@pytest.mark.parametrize("backend", ("python", "rust"))
def test_special_database_path_loads_all_query_stages(
    tmp_path, qapp, monkeypatch, backend
):
    _select_backend(monkeypatch, backend)
    question = "?问" if os.name != "nt" else ""
    path = tmp_path / f"图 表 # 百分%23{question}.sqlite"
    _write_db(path)
    model = sql_list_model.SqlListModel(path, page_size=1, lru_capacity=2)

    model.setQuery(_QUERY, _COUNT_QUERY)

    assert model.count() == 2
    assert model.roleNames() == {
        Qt.UserRole + 1: b"id",
        Qt.UserRole + 2: b"name",
    }
    assert model.getRow(0) == {"id": 1, "name": "甲"}
    assert model.getRow(1) == {"id": 2, "name": "乙"}
