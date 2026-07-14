# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel exhaustive keyset matrices. SQL 列表游标穷举矩阵。"""

from __future__ import annotations

import itertools
import sqlite3
from contextlib import closing
from unittest import mock

import pytest
from PySide6.QtCore import QByteArray

from prismqml.python.models import sql_list_model
from prismqml.python.models._page_cache import PageCache


_DIRECTION_CASES = tuple(itertools.product(("ASC", "DESC"), repeat=3))
_PAGE_SIZES = (1, 2, 5)
_RUST_EXECUTION_MODES = ("rust", "sharded")
_STATE_STAGES = (
    ("normalize-count", sql_list_model, "_normalize_count_query"),
    ("compute-count", sql_list_model.SqlListModel, "_compute_count"),
    ("resolve-columns", sql_list_model.SqlListModel, "_resolve_columns"),
    ("fetch-page", sql_list_model.SqlListModel, "_fetch_page"),
)


class _StaticRouter(sql_list_model.DbRouter):
    def __init__(self, paths):
        self._paths = [str(path) for path in paths]

    def route(self, _params):
        return list(self._paths)


def _write_matrix_db(path, rows, nullable_index) -> str:
    definitions = []
    for index, name in enumerate(("c1", "c2", "c3")):
        nullable = "" if index == nullable_index else " NOT NULL"
        definitions.append(f"{name} INTEGER{nullable}")
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, "
            + ", ".join(definitions)
            + ")"
        )
        connection.executemany(
            "INSERT INTO items (id, c1, c2, c3) VALUES (?, ?, ?, ?)", rows
        )
        connection.commit()
    return str(path)


def _matrix_rows(nullable_index) -> list[tuple]:
    rows = []
    for identifier in range(1, 42):
        values = [(identifier * 3) % 5, (identifier * 5) % 7, (identifier * 7) % 4]
        if identifier % (7, 5, 6)[nullable_index] == 0:
            values[nullable_index] = None
        rows.append((identifier, *values))
    return rows


@pytest.fixture(params=range(3), ids=("nullable-c1", "nullable-c2", "nullable-c3"))
def matrix_sources(tmp_path, request):
    nullable_index = request.param
    rows = _matrix_rows(nullable_index)
    oracle = _write_matrix_db(
        tmp_path / "oracle.sqlite", rows, nullable_index
    )
    shard_a = _write_matrix_db(
        tmp_path / "shard-a.sqlite", rows[::2], nullable_index
    )
    shard_b = _write_matrix_db(
        tmp_path / "shard-b.sqlite", rows[1::2], nullable_index
    )
    return nullable_index, oracle, [shard_a, shard_b]


def _order_by(directions) -> str:
    expanded = (*directions, directions[-1])
    return ", ".join(
        f"{column} COLLATE BINARY {direction}"
        for column, direction in zip(("c1", "c2", "c3", "id"), expanded)
    )


def _oracle_ids(db_path: str, order_by: str) -> list[int]:
    with closing(sqlite3.connect(db_path)) as connection:
        return [
            row[0]
            for row in connection.execute(
                f"SELECT id FROM items ORDER BY {order_by}"
            )
        ]


def _matrix_source(mode, oracle, shards, monkeypatch):
    rust_enabled = mode != "python"
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", rust_enabled)
    return _StaticRouter(shards) if mode == "sharded" else oracle


def _collect_ids(model) -> list[int]:
    rows = [model.getRow(index) for index in range(model.count())]
    assert all(rows), rows
    identifiers = [row["id"] for row in rows]
    assert len(identifiers) == model.count()
    assert len(set(identifiers)) == len(identifiers)
    return identifiers


def _assert_matrix_case(
    source, order_by, nullable_index, page_size, expected
) -> None:
    model = sql_list_model.SqlListModel(
        source, page_size=page_size, lru_capacity=1
    )
    model.setQuery(
        f"SELECT id, c1, c2, c3 FROM items ORDER BY {order_by}",
        "SELECT COUNT(*) FROM items",
        cursor_columns=["c1", "c2", "c3", "id"],
        nullable_cursor_column=f"c{nullable_index + 1}",
    )
    assert _collect_ids(model) == expected


def _run_mode_matrix(matrix_sources, monkeypatch, modes) -> int:
    nullable_index, oracle, shards = matrix_sources
    case_count = 0
    for directions, page_size, mode in itertools.product(
        _DIRECTION_CASES, _PAGE_SIZES, modes
    ):
        order_by = _order_by(directions)
        source = _matrix_source(mode, oracle, shards, monkeypatch)
        _assert_matrix_case(
            source,
            order_by,
            nullable_index,
            page_size,
            _oracle_ids(oracle, order_by),
        )
        case_count += 1
    return case_count


def test_python_keyset_72_case_matrix(matrix_sources, monkeypatch):
    case_count = _run_mode_matrix(matrix_sources, monkeypatch, ("python",))
    assert case_count == 24


def test_rust_keyset_144_case_matrix(matrix_sources, monkeypatch):
    if sql_list_model._rs is None:
        pytest.skip("prismqml_rs is unavailable")
    case_count = _run_mode_matrix(
        matrix_sources, monkeypatch, _RUST_EXECUTION_MODES
    )
    assert case_count == 48


def _write_state_db(path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, rank INTEGER)"
        )
        connection.executemany(
            "INSERT INTO items VALUES (?, ?)",
            [(1, None), (2, 3), (3, 2), (4, 1)],
        )
        connection.commit()
    return str(path)


def _identity_rank(value):
    return value


def _negate_rank(value):
    return -value if value is not None else value


@pytest.fixture
def state_model(tmp_path):
    model = sql_list_model.SqlListModel(
        _write_state_db(tmp_path / "state.sqlite"),
        page_size=2,
        lru_capacity=2,
    )
    model.setQuery(
        "SELECT id, rank FROM items ORDER BY rank DESC, id DESC",
        "SELECT COUNT(*) FROM items",
        formatters={"rank": _identity_rank},
        cursor_columns=["rank", "id"],
        nullable_cursor_column="rank",
    )
    return model


def _freeze_state(value):
    if isinstance(value, PageCache):
        return (id(value), value._capacity, _freeze_state(value._pages))
    if isinstance(value, QByteArray):
        return bytes(value)
    if isinstance(value, dict):
        return tuple((key, _freeze_state(item)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_state(item) for item in value)
    if callable(value):
        return ("callable", id(value))
    return value


def _model_state(model) -> tuple:
    first_row = model.getRow(0)
    fields = tuple(
        (name, _freeze_state(value))
        for name, value in sorted(vars(model).items())
    )
    return fields + (("first_row", _freeze_state(first_row)),)


def _process_control_raiser(error_type):
    def raise_process_control(*_args, **_kwargs):
        raise error_type("stop")

    return raise_process_control


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize(
    ("_stage_name", "target", "attribute"),
    _STATE_STAGES,
    ids=[stage[0] for stage in _STATE_STAGES],
)
def test_set_query_process_control_restores_complete_state(
    state_model, error_type, _stage_name, target, attribute
):
    emitted = []
    state_model.queryChanged.connect(lambda: emitted.append("query"))
    state_model.countChanged.connect(lambda: emitted.append("count"))
    before = _model_state(state_model)
    with mock.patch.object(target, attribute, _process_control_raiser(error_type)):
        with pytest.raises(error_type, match="stop"):
            state_model.setQuery(
                "SELECT id, rank FROM items WHERE id >= ? ORDER BY rank ASC, id ASC",
                "SELECT COUNT(*) FROM items WHERE id >= ?",
                params=[2],
                formatters={"rank": _negate_rank},
                cursor_columns=["rank", "id"],
                nullable_cursor_column="rank",
            )
    assert _model_state(state_model) == before
    assert emitted == []
