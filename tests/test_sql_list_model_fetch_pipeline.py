# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel page-fetch pipeline contracts. SQL 分页读取管线合同。"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Optional

import pytest
from PySide6.QtCore import QByteArray

from prismqml.python.models import _sqlite_connection, sql_list_model
from prismqml.python.models._page_cache import PageCache


_QUERY = (
    "SELECT id, rank FROM items WHERE id >= ? "
    "ORDER BY rank COLLATE BINARY DESC, id COLLATE BINARY DESC"
)
_PLANNED_QUERY = "SELECT planned"


class _StaticRouter(sql_list_model.DbRouter):
    def __init__(self, paths, events=None):
        self._paths = list(paths)
        self._events = events

    def route(self, params):
        if self._events is not None:
            self._events.append(("route", list(params)))
        return list(self._paths)


class _FakeCursor:
    description = (("id",), ("rank",))

    def fetchall(self):
        return [(7, 9), (6, 8)]


class _FakeConnection:
    def __init__(self, calls):
        self._calls = calls

    def execute(self, sql, params=()):
        self._calls.append((sql, list(params)))
        return _FakeCursor()

    def close(self):
        self._calls.append(("close", []))


class _FakeRust:
    def __init__(self, events=None, error_type=None):
        self.calls = []
        self._events = events
        self._error_type = error_type

    def _result(self):
        if self._error_type is not None:
            raise self._error_type("stop")
        return {
            "columns": ["id", "rank"],
            "rows": [[7, 9], [6, 8]],
            "last_cursor": [8, 6],
        }

    def fetch_page(
        self, path, sql, params, offset, limit, use_keyset, cursor_indices
    ):
        call = {
            "kind": "single",
            "path": path,
            "sql": sql,
            "params": params,
            "offset": offset,
            "limit": limit,
            "use_keyset": use_keyset,
            "cursor_indices": cursor_indices,
        }
        self.calls.append(call)
        if self._events is not None:
            self._events.append(("dispatch", "single"))
        return self._result()

    def fan_out_fetch_page(
        self, paths, sql, params, limit, cursor_indices, sort_directions
    ):
        call = {
            "kind": "sharded",
            "paths": list(paths),
            "sql": sql,
            "params": params,
            "limit": limit,
            "cursor_indices": cursor_indices,
            "sort_directions": sort_directions,
        }
        self.calls.append(call)
        if self._events is not None:
            self._events.append(("dispatch", "sharded"))
        return self._result()

    def count_rows(self, _path, _sql, _params):
        return 3


def _new_model(
    paths,
    *,
    cursor_enabled: bool = True,
    params: Optional[list] = None,
    columns_installed: bool = True,
    events=None,
):
    model = sql_list_model.SqlListModel(
        _StaticRouter(paths, events), page_size=2, lru_capacity=2
    )
    model._sql = _QUERY
    model._params = [4] if params is None else list(params)
    model._cursor_columns = ["rank", "id"] if cursor_enabled else []
    model._cursor_nullable_index = None
    model._cursor_directions = ["DESC", "DESC"] if cursor_enabled else []
    model._cursor_col_indices = []
    if columns_installed:
        model._install_resolved_columns(["id", "rank"])
    return model


def _install_fake_rust(monkeypatch, fake, enabled=True):
    monkeypatch.setattr(sql_list_model, "_rs", fake)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", enabled)


def _install_planner(monkeypatch, calls):
    def plan(sql, params, cursor, columns, directions, nullable_index):
        calls.append(
            (sql, list(params), list(cursor), list(columns), list(directions),
             nullable_index)
        )
        return _PLANNED_QUERY, list(params) + list(cursor)

    monkeypatch.setattr(sql_list_model, "inject_keyset_predicate", plan)


def _install_fake_sqlite(monkeypatch, calls):
    def connect(path, **kwargs):
        calls.append(("connect", path, kwargs))
        return _FakeConnection(calls)

    monkeypatch.setattr(_sqlite_connection.sqlite3, "connect", connect)


def _write_db(path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, rank INTEGER NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO items VALUES (?, ?)",
            [(1, 3), (2, 3), (3, 2), (4, 1)],
        )
        connection.commit()
    return str(path)


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
    fields = tuple(
        (name, _freeze_state(getattr(model, name)))
        for name in sql_list_model._QUERY_STATE_FIELDS
    )
    return fields + (("first_row", _freeze_state(model.getRow(0))),)


def test_empty_route_returns_before_planning_dispatch_or_formatting(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake)
    model = _new_model([], columns_installed=False)
    model._formatters = {"rank": lambda _value: pytest.fail("formatter called")}
    monkeypatch.setattr(
        sql_list_model,
        "inject_keyset_predicate",
        lambda *_args: pytest.fail("planner called"),
    )

    assert model._fetch_page(0) == {"rows": [], "end_cursor": None}
    assert fake.calls == []
    assert model._columns == []


@pytest.mark.parametrize(
    (
        "cursor_enabled",
        "page_idx",
        "previous_cursor",
        "expected_offset",
        "expected_keyset",
    ),
    [
        pytest.param(False, 2, None, 4, False, id="offset-no-cursor"),
        pytest.param(True, 0, None, 0, False, id="keyset-first-page"),
        pytest.param(True, 2, None, 4, False, id="keyset-random-access"),
        pytest.param(True, 2, [9, 7], 0, True, id="keyset-next-page"),
        pytest.param(True, 0, [9, 7], 0, True, id="keyset-explicit-first"),
    ],
)
def test_single_rust_query_plan_contract(
    monkeypatch,
    cursor_enabled,
    page_idx,
    previous_cursor,
    expected_offset,
    expected_keyset,
):
    planner_calls = []
    _install_planner(monkeypatch, planner_calls)
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(["single.sqlite"], cursor_enabled=cursor_enabled)

    result = model._fetch_page(page_idx, previous_cursor)

    call = fake.calls[0]
    assert call["offset"] == expected_offset
    assert call["limit"] == 2
    assert call["use_keyset"] is expected_keyset
    assert call["sql"] == (_PLANNED_QUERY if expected_keyset else _QUERY)
    assert call["params"] == ([4, 9, 7] if expected_keyset else [4])
    expected_indices = [1, 0] if cursor_enabled else None
    assert call["cursor_indices"] == expected_indices
    assert result["end_cursor"] == [8, 6]
    expected_planner_calls = [
        (_QUERY, [4], [9, 7], ["rank", "id"], ["DESC", "DESC"], None)
    ] if expected_keyset else []
    assert planner_calls == expected_planner_calls


def test_single_rust_empty_params_are_passed_as_none(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(
        ["single.sqlite"], cursor_enabled=False, params=[]
    )

    model._fetch_page(0)

    assert fake.calls[0]["params"] is None


def test_real_keyset_routes_with_base_params_only(tmp_path, monkeypatch):
    db_path = _write_db(tmp_path / "route.sqlite")
    events = []
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    model = sql_list_model.SqlListModel(
        _StaticRouter([db_path], events), page_size=1, lru_capacity=2
    )
    model.setQuery(
        _QUERY,
        "SELECT COUNT(*) FROM items WHERE id >= ?",
        params=[1],
        cursor_columns=["rank", "id"],
        nullable_cursor_column="",
    )

    assert model.getRow(1)["id"] == 1
    assert len(events) >= 4
    assert all(params == [1] for _stage, params in events)


def test_sharded_dispatch_preserves_fan_out_arguments(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(["a.sqlite", "b.sqlite"])
    model._formatters = {"rank": lambda value: value * 10}

    result = model._fetch_page(0)

    assert fake.calls == [
        {
            "kind": "sharded",
            "paths": ["a.sqlite", "b.sqlite"],
            "sql": _QUERY,
            "params": [4],
            "limit": 2,
            "cursor_indices": [1, 0],
            "sort_directions": ["DESC", "DESC"],
        }
    ]
    assert result == {"rows": [[7, 90], [6, 80]], "end_cursor": [8, 6]}


def test_sharded_fetch_requires_cursor_columns(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(
        ["a.sqlite", "b.sqlite"], cursor_enabled=False
    )

    with pytest.raises(RuntimeError, match="必须设置 cursor_columns"):
        model._fetch_page(0)
    assert fake.calls == []


def test_sharded_random_access_requires_previous_cursor(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(["a.sqlite", "b.sqlite"])

    with pytest.raises(RuntimeError, match="random access"):
        model._fetch_page(2)
    assert fake.calls == []


def test_sharded_keyset_planning_precedes_rust_availability(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake, enabled=False)
    model = _new_model(["a.sqlite", "b.sqlite"])

    def fail_planning(*_args):
        raise ValueError("planning failed")

    monkeypatch.setattr(
        sql_list_model, "inject_keyset_predicate", fail_planning
    )
    with pytest.raises(ValueError, match="planning failed"):
        model._fetch_page(1, [9, 7])
    assert fake.calls == []


def test_sharded_fetch_requires_rust_after_planning(monkeypatch):
    fake = _FakeRust()
    _install_fake_rust(monkeypatch, fake, enabled=False)
    model = _new_model(["a.sqlite", "b.sqlite"])

    with pytest.raises(RuntimeError, match="需要 prismqml_rs"):
        model._fetch_page(0)
    assert fake.calls == []


def test_python_offset_dispatch_preserves_sql_and_bind_order(monkeypatch):
    calls = []
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    _install_fake_sqlite(monkeypatch, calls)
    model = _new_model(["single.sqlite"], cursor_enabled=False)

    result = model._fetch_page(2)

    assert calls == [
        ("connect", "file:single.sqlite?mode=ro", {"uri": True, "timeout": 5}),
        ("PRAGMA busy_timeout=5000", []),
        (f"{_QUERY} LIMIT ? OFFSET ?", [4, 2, 4]),
        ("close", []),
    ]
    assert result == {"rows": [[7, 9], [6, 8]], "end_cursor": None}


def test_python_keyset_extracts_raw_cursor_before_formatting(monkeypatch):
    calls = []
    planner_calls = []
    _install_planner(monkeypatch, planner_calls)
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    _install_fake_sqlite(monkeypatch, calls)
    model = _new_model(["single.sqlite"])
    model._formatters = {"rank": lambda value: value * 10}

    result = model._fetch_page(1, [9, 7])

    assert calls[2] == (f"{_PLANNED_QUERY} LIMIT ?", [4, 9, 7, 2])
    assert len(planner_calls) == 1
    assert result == {"rows": [[7, 90], [6, 80]], "end_cursor": [8, 6]}


def test_first_fetch_installs_columns_before_formatter(monkeypatch):
    events = []
    fake = _FakeRust(events=events)
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(
        ["single.sqlite"],
        cursor_enabled=False,
        columns_installed=False,
        events=events,
    )

    def format_rank(value):
        assert model._columns == ["id", "rank"]
        events.append(("format", value))
        return value * 10

    model._formatters = {"rank": format_rank}
    result = model._fetch_page(0)

    assert events == [
        ("route", [4]),
        ("dispatch", "single"),
        ("format", 9),
        ("format", 8),
    ]
    assert result["rows"] == [[7, 90], [6, 80]]


def test_zero_row_query_still_installs_roles(tmp_path, monkeypatch):
    db_path = tmp_path / "empty.sqlite"
    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY, rank INTEGER)"
        )
        connection.commit()
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    model = sql_list_model.SqlListModel(str(db_path))

    model.setQuery(
        "SELECT id, rank FROM items ORDER BY id",
        "SELECT COUNT(*) FROM items",
    )

    roles = [bytes(name).decode("utf-8") for name in model.roleNames().values()]
    assert model.count() == 0
    assert roles == ["id", "rank"]


def test_first_page_backend_error_restores_complete_state(tmp_path, monkeypatch):
    db_path = _write_db(tmp_path / "rollback.sqlite")
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    model = sql_list_model.SqlListModel(db_path, page_size=2)
    model.setQuery(
        "SELECT id, rank FROM items ORDER BY id",
        "SELECT COUNT(*) FROM items",
        formatters={"rank": int},
    )
    emitted = []
    model.queryChanged.connect(lambda: emitted.append("query"))
    model.countChanged.connect(lambda: emitted.append("count"))
    before = _model_state(model)
    _install_fake_rust(monkeypatch, _FakeRust(error_type=RuntimeError))

    with pytest.raises(RuntimeError, match="stop"):
        model.setQuery(
            "SELECT id, rank FROM items ORDER BY rank DESC, id DESC",
            "SELECT COUNT(*) FROM items",
            cursor_columns=["rank", "id"],
            nullable_cursor_column="",
        )

    assert _model_state(model) == before
    assert emitted == []


def test_public_page_cache_hit_and_eviction_contract(tmp_path, monkeypatch):
    db_path = _write_db(tmp_path / "cache.sqlite")
    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    model = sql_list_model.SqlListModel(
        db_path, page_size=1, lru_capacity=1
    )
    model.setQuery(
        "SELECT id, rank FROM items ORDER BY id",
        "SELECT COUNT(*) FROM items",
    )
    original_fetch = model._fetch_page
    fetched_pages = []

    def fetch(page_idx, end_cursor_of_prev=None):
        fetched_pages.append(page_idx)
        return original_fetch(page_idx, end_cursor_of_prev)

    monkeypatch.setattr(model, "_fetch_page", fetch)
    assert model.getRow(0)["id"] == 1
    assert model.getRow(1)["id"] == 2
    assert model.getRow(1)["id"] == 2
    assert model.getRow(2)["id"] == 3
    assert model.getRow(1)["id"] == 2
    assert fetched_pages == [1, 2, 1]


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_rust_backend_process_control_exceptions_propagate(
    monkeypatch, error_type
):
    fake = _FakeRust(error_type=error_type)
    _install_fake_rust(monkeypatch, fake)
    model = _new_model(["single.sqlite"])

    with pytest.raises(error_type, match="stop"):
        model._fetch_page(0)
