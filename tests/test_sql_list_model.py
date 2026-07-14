# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel behavior tests."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest


class _RecordCapture(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def project_log_records():
    from prismqml.python.core.logger import getLogger

    capture = _RecordCapture()
    logger = getLogger().logger
    logger.addHandler(capture)
    try:
        yield capture.records
    finally:
        logger.removeHandler(capture)


def _role_id(model, name):
    return next(
        role
        for role, role_name in model.roleNames().items()
        if bytes(role_name).decode("utf-8") == name
    )


def _assert_traceback_record(records, marker, error_type, source_text):
    from prismqml.python.core.logger import PlainFormatter

    matches = [record for record in records if marker in record.getMessage()]
    assert len(matches) == 1
    assert matches[0].exc_info is not None
    assert matches[0].exc_info[0] is error_type
    rendered = PlainFormatter(datefmt="%H:%M:%S").format(matches[0])
    assert "Traceback (most recent call last):" in rendered
    assert source_text in rendered


def _exercise_deleted_database_boundary(
    tmp_path, records, sql_model, expected_error
):
    db_path = _seed_records_db(tmp_path)
    model = sql_model.SqlListModel(db_path, page_size=1, lru_capacity=2)
    model.setQuery(
        "SELECT id, name FROM records ORDER BY id",
        "SELECT COUNT(*) FROM records",
    )
    name_role = _role_id(model, "name")
    assert model.data(model.index(0, 0), name_role) == "alice"
    assert model.getRow(0) == {"id": 1, "name": "alice"}

    Path(db_path).unlink()
    assert model.data(model.index(1, 0), name_role) is None
    assert model.getRow(1) == {}
    assert model.data(model.index(0, 0), name_role) == "alice"
    assert model.getRow(0) == {"id": 1, "name": "alice"}

    for consumer in ("data", "getRow"):
        _assert_traceback_record(
            records,
            f"SqlListModel.{consumer} page fetch failed",
            expected_error,
            "return self._get_page(page_idx)",
        )


def _seed_records_db(tmp_path) -> str:
    db_path = tmp_path / "records.sqlite"
    with closing(sqlite3.connect(db_path)) as conn:
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
        conn.commit()
    return str(db_path)


def _assert_keyset_record_rows(model) -> None:
    assert model.count() == 4
    assert model.rowCount() == 4
    assert model.getRow(0) == {
        "id": 2,
        "category": "alpha",
        "name": "BOB",
        "score": 30,
        "marker": ":category",
    }
    assert [model.getRow(index)["id"] for index in range(1, 4)] == [1, 4, 3]
    assert model.getRow(4) == {}


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
        ORDER BY score COLLATE BINARY DESC, id COLLATE BINARY ASC
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
    _assert_keyset_record_rows(model)


def test_sql_list_model_count_params_dict_uses_own_values(tmp_path):
    from prismqml.python.models.sql_list_model import SqlListModel

    model = SqlListModel(_seed_records_db(tmp_path))
    model.setQuery(
        "SELECT id, name FROM records ORDER BY id",
        "SELECT :expected_count",
        params={"expected_count": 1},
        count_params={"expected_count": 3},
    )

    assert model.count() == 3


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


def test_page_access_deleted_database_logs_traceback_and_keeps_cached_rows(
    tmp_path, project_log_records
):
    from prismqml.python.models import sql_list_model

    expected_error = (
        RuntimeError
        if sql_list_model.is_rust_accelerated()
        else sqlite3.OperationalError
    )
    _exercise_deleted_database_boundary(
        tmp_path, project_log_records, sql_list_model, expected_error
    )


def test_page_access_deleted_database_python_fallback(
    tmp_path, project_log_records, monkeypatch
):
    from prismqml.python.models import sql_list_model

    monkeypatch.setattr(sql_list_model, "_HAS_RUST", False)
    _exercise_deleted_database_boundary(
        tmp_path,
        project_log_records,
        sql_list_model,
        sqlite3.OperationalError,
    )


def test_formatter_failure_keeps_raw_cell_and_logs_traceback(
    tmp_path, project_log_records
):
    from prismqml.python.models.sql_list_model import SqlListModel

    def format_name(value):
        if value in {"bob", "dora"}:
            raise RuntimeError("formatter exploded")
        return value.upper()

    model = SqlListModel(_seed_records_db(tmp_path), page_size=5)
    model.setQuery(
        "SELECT id, name FROM records ORDER BY id",
        "SELECT COUNT(*) FROM records",
        formatters={"name": format_name},
    )

    assert model.getRow(0)["name"] == "ALICE"
    assert model.getRow(1)["name"] == "bob"
    assert model.getRow(2)["name"] == "CAROL"
    assert model.getRow(3)["name"] == "dora"
    assert model.getRow(4)["name"] == "ERIC"
    _assert_traceback_record(
        project_log_records,
        "SqlListModel formatter failed for column name",
        RuntimeError,
        'raise RuntimeError("formatter exploded")',
    )


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_formatter_process_control_exceptions_propagate(tmp_path, error_type):
    from prismqml.python.models.sql_list_model import SqlListModel

    def stop_formatter(_value):
        raise error_type("stop")

    model = SqlListModel(_seed_records_db(tmp_path))
    with pytest.raises(error_type, match="stop"):
        model.setQuery(
            "SELECT id, name FROM records ORDER BY id",
            "SELECT COUNT(*) FROM records",
            formatters={"name": stop_formatter},
        )


@pytest.mark.parametrize("consumer", ["data", "getRow"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_page_access_process_control_exceptions_propagate(
    tmp_path, error_type, consumer
):
    from prismqml.python.models.sql_list_model import DbRouter, SqlListModel

    class StopRouter(DbRouter):
        def route(self, _params):
            raise error_type("stop")

    model = SqlListModel(_seed_records_db(tmp_path), page_size=1)
    model.setQuery(
        "SELECT id, name FROM records ORDER BY id",
        "SELECT COUNT(*) FROM records",
    )
    model._router = StopRouter()
    name_role = _role_id(model, "name")
    with pytest.raises(error_type, match="stop"):
        if consumer == "data":
            model.data(model.index(1, 0), name_role)
        else:
            model.getRow(1)
