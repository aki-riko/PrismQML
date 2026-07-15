# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel refresh atomicity regressions. SQL 列表刷新原子性回归。"""

import sqlite3
from contextlib import closing

import pytest
from PySide6.QtCore import Qt

from prismqml.python.models import sql_list_model


_QUERY = "SELECT id, name FROM records ORDER BY id"
_COUNT_QUERY = "SELECT COUNT(*) FROM records"
_FAILURE_STAGES = ("count", "resolve", "fetch")
_ERROR_TYPES = (ValueError, OSError, RuntimeError, KeyboardInterrupt, SystemExit)
_REFERENCE_STATE_FIELDS = ("_cache",)


class _MutatingRouter(sql_list_model.DbRouter):
    def __init__(self, path, failure):
        self._path = path
        self._failure = failure
        self.enabled = False

    def route(self, params):
        if self.enabled:
            params.append("corrupt")
            raise self._failure
        return [self._path]


def _write_db(path, rows=((1, "alpha"), (2, "beta"))) -> str:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE records(id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        connection.executemany("INSERT INTO records VALUES (?, ?)", rows)
        connection.commit()
    return str(path)


def _new_model(path):
    model = sql_list_model.SqlListModel(path, page_size=1, lru_capacity=2)
    model.setQuery(
        _QUERY,
        _COUNT_QUERY,
        cursor_columns=["id"],
        nullable_cursor_column="",
    )
    assert model.getRow(0) == {"id": 1, "name": "alpha"}
    assert model.getRow(1) == {"id": 2, "name": "beta"}
    return model


def _cache_snapshot(cache):
    return (
        cache._capacity,
        tuple(
            (
                page_index,
                _freeze(rows),
                _freeze(cursor),
            )
            for page_index, (rows, cursor) in cache._pages.items()
        )
    )


def _freeze(value):
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple((key, _freeze(item)) for key, item in value.items())
    return value


def _state_snapshot(model):
    first_row = model.getRow(0)
    fields = {
        name: _freeze(getattr(model, name))
        for name in sql_list_model._QUERY_STATE_FIELDS
        if name != "_cache"
    }
    return (
        fields,
        _cache_snapshot(model._cache),
        model.count(),
        first_row,
        tuple(model.roleNames().items()),
    )


def _state_references(model):
    return {name: getattr(model, name) for name in _REFERENCE_STATE_FIELDS}


def _refresh_events(model):
    events = []
    reset_snapshots = []

    def on_model_reset():
        events.append("end")
        reset_snapshots.append(_state_snapshot(model))

    model.modelAboutToBeReset.connect(lambda: events.append("begin"))
    model.modelReset.connect(on_model_reset)
    model.queryChanged.connect(lambda: events.append("query"))
    model.countChanged.connect(lambda: events.append(("count", model.count())))
    return events, reset_snapshots


def _assert_state_restored(model, snapshot, references):
    assert _state_snapshot(model) == snapshot
    for name, value in references.items():
        assert getattr(model, name) is value, name


def _install_refresh_failure(monkeypatch, model, stage, failure):
    calls = []

    def compute_count():
        calls.append("count")
        model._row_count = 901
        if stage == "count":
            raise failure
        return 1

    def resolve_columns():
        calls.append("resolve")
        model._columns = ["mutated"]
        model._role_to_col = {999: 0}
        if stage == "resolve":
            raise failure

    def fetch_page(_page_index, end_cursor_of_prev=None):
        del end_cursor_of_prev
        calls.append("fetch")
        model._cursor_directions = ["MUTATED"]
        if stage == "fetch":
            raise failure
        return {"rows": [[999, "mutated"]], "end_cursor": [999]}

    monkeypatch.setattr(model, "_compute_count", compute_count)
    monkeypatch.setattr(model, "_resolve_columns", resolve_columns)
    monkeypatch.setattr(model, "_fetch_page", fetch_page)
    return calls


def test_rust_deleted_database_refresh_restores_cached_state(tmp_path, qapp):
    if not sql_list_model._HAS_RUST:
        pytest.skip("real deleted-database contract requires prismqml_rs")
    path = tmp_path / "records.sqlite"
    model = _new_model(_write_db(path))
    snapshot = _state_snapshot(model)
    references = _state_references(model)
    events, reset_snapshots = _refresh_events(model)
    path.unlink()

    with pytest.raises(RuntimeError, match="unable to open database file"):
        model.refresh()

    assert not path.exists()
    assert events == ["begin", "end"]
    assert reset_snapshots == [snapshot]
    _assert_state_restored(model, snapshot, references)


@pytest.mark.parametrize("stage", _FAILURE_STAGES)
@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_refresh_failure_restores_state_by_identity(
    tmp_path, qapp, monkeypatch, stage, error_type
):
    model = _new_model(_write_db(tmp_path / "records.sqlite"))
    snapshot = _state_snapshot(model)
    references = _state_references(model)
    failure = error_type(f"refresh {stage} failure")
    events, reset_snapshots = _refresh_events(model)
    calls = _install_refresh_failure(monkeypatch, model, stage, failure)

    with pytest.raises(error_type) as caught:
        model.refresh()

    assert caught.value is failure
    assert calls == {
        "count": ["count"],
        "resolve": ["count", "resolve"],
        "fetch": ["count", "resolve", "fetch"],
    }[stage]
    assert events == ["begin", "end"]
    assert reset_snapshots == [snapshot]
    _assert_state_restored(model, snapshot, references)


def test_router_param_mutation_failure_restores_state(tmp_path, qapp):
    failure = RuntimeError("router failed after mutating params")
    router = _MutatingRouter(_write_db(tmp_path / "records.sqlite"), failure)
    model = _new_model(router)
    snapshot = _state_snapshot(model)
    references = _state_references(model)
    events, reset_snapshots = _refresh_events(model)
    router.enabled = True

    with pytest.raises(RuntimeError) as caught:
        model.refresh()

    assert caught.value is failure
    assert events == ["begin", "end"]
    assert reset_snapshots == [snapshot]
    _assert_state_restored(model, snapshot, references)


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_formatter_mutation_process_control_restores_state(
    tmp_path, qapp, error_type
):
    model = sql_list_model.SqlListModel(
        _write_db(tmp_path / "records.sqlite"), page_size=1, lru_capacity=2
    )
    enabled = False
    failure = error_type("formatter mutated state")

    def formatter(value):
        if enabled:
            model._formatters["corrupt"] = str
            raise failure
        return value.upper()

    model.setQuery(_QUERY, _COUNT_QUERY, formatters={"name": formatter})
    snapshot = _state_snapshot(model)
    references = _state_references(model)
    events, reset_snapshots = _refresh_events(model)
    enabled = True
    with pytest.raises(error_type) as caught:
        model.refresh()
    assert caught.value is failure
    assert events == ["begin", "end"]
    assert reset_snapshots == [snapshot]
    _assert_state_restored(model, snapshot, references)


def test_successful_refresh_commits_new_rows_and_emits_once(tmp_path, qapp):
    path = tmp_path / "records.sqlite"
    model = _new_model(_write_db(path))
    events, reset_snapshots = _refresh_events(model)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("INSERT INTO records VALUES (?, ?)", (3, "gamma"))
        connection.commit()

    model.refresh()

    assert reset_snapshots == [_state_snapshot(model)]
    assert model.count() == 3
    assert model.getRow(2) == {"id": 3, "name": "gamma"}
    roles = {role: bytes(name) for role, name in model.roleNames().items()}
    assert roles == {Qt.UserRole + 1: b"id", Qt.UserRole + 2: b"name"}
    assert model._role_to_col == {Qt.UserRole + 1: 0, Qt.UserRole + 2: 1}
    assert model.data(model.index(2, 0), Qt.UserRole + 2) == "gamma"
    assert events == ["begin", "end", ("count", 3)]
