# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SQL named-parameter normalization contracts. SQL 命名参数归一化合同。"""

import sqlite3
from contextlib import closing

import pytest

from prismqml.python.models._sql_query_tools import normalize_one


_NAMED_CASES = (
    pytest.param(
        "SELECT :beta, :alpha, :beta, :missing",
        {"alpha": 1, "beta": 2, "unused": 3},
        "SELECT ?, ?, ?, :missing",
        [2, 1, 2],
        id="sql-order-repeat-missing",
    ),
    pytest.param(
        "SELECT :_private2, :名字2, :Case, :case",
        {"_private2": 3, "名字2": 4, "Case": 5, "case": 6},
        "SELECT ?, ?, ?, ?",
        [3, 4, 5, 6],
        id="underscore-unicode-case-sensitive",
    ),
    pytest.param(
        "SELECT ':alpha', 'it''s :beta', \"quoted:gamma\", :delta "
        "-- :line\r\n, :epsilon /* :block */",
        {"alpha": 1, "beta": 2, "gamma": 3, "delta": 4, "epsilon": 5},
        "SELECT ':alpha', 'it''s :beta', \"quoted:gamma\", ? "
        "-- :line\r\n, ? /* :block */",
        [4, 5],
        id="quotes-and-comments",
    ),
    pytest.param(
        "SELECT ':value",
        {"value": 7},
        "SELECT ':value",
        [],
        id="unterminated-single-quote",
    ),
    pytest.param(
        'SELECT "column:value',
        {"value": 8},
        'SELECT "column:value',
        [],
        id="unterminated-double-quote",
    ),
    pytest.param(
        "SELECT /* :value",
        {"value": 9},
        "SELECT /* :value",
        [],
        id="unterminated-block-comment",
    ),
)


class _TrackingParams(dict):
    def __init__(self, values):
        super().__init__(values)
        self.events = []

    def __contains__(self, key):
        self.events.append(("contains", key))
        return super().__contains__(key)

    def __getitem__(self, key):
        self.events.append(("getitem", key))
        return super().__getitem__(key)


class _ExplodingParams(dict):
    def __init__(self, stage, failure):
        super().__init__({"value": 1})
        self.stage = stage
        self.failure = failure

    def __contains__(self, key):
        if self.stage == "contains":
            raise self.failure
        return super().__contains__(key)

    def __getitem__(self, key):
        if self.stage == "getitem":
            raise self.failure
        return super().__getitem__(key)


class _ExplodingList(list):
    def __init__(self, failure):
        super().__init__([object()])
        self.failure = failure

    def __iter__(self):
        raise self.failure


class _ExplodingSql(str):
    def __len__(self):
        raise AssertionError("sequence fast path scanned SQL length")

    def __getitem__(self, key):
        raise AssertionError(f"sequence fast path scanned SQL at {key!r}")

    def __iter__(self):
        raise AssertionError("sequence fast path iterated SQL")


def test_none_params_preserve_sql_identity_without_scanning():
    sql = _ExplodingSql("SELECT :value")

    normalized, params = normalize_one(sql, None)

    assert normalized is sql
    assert params == []


@pytest.mark.parametrize("container_type", (list, tuple))
def test_sequence_params_preserve_sql_and_return_shallow_list(container_type):
    marker = object()
    sql = _ExplodingSql("SELECT :value")
    source = container_type([marker])
    before = list(source)

    normalized, params = normalize_one(sql, source)

    assert normalized is sql
    assert params == [marker]
    assert params is not source
    assert params[0] is marker
    assert list(source) == before


@pytest.mark.parametrize(
    ("sql", "source", "expected_sql", "expected_params"), _NAMED_CASES
)
def test_dict_params_follow_sql_tokens(
    sql, source, expected_sql, expected_params
):
    before = dict(source)

    normalized, params = normalize_one(sql, source)

    assert normalized == expected_sql
    assert params == expected_params
    assert source == before


def test_dict_access_order_tracks_each_visible_occurrence():
    source = _TrackingParams({"first": 1, "second": 2})
    sql = "SELECT ':hidden', :first, :missing, :first -- :ignored\n, :second"

    normalized, params = normalize_one(sql, source)

    assert normalized == "SELECT ':hidden', ?, :missing, ? -- :ignored\n, ?"
    assert params == [1, 1, 2]
    assert source.events == [
        ("contains", "first"),
        ("getitem", "first"),
        ("contains", "missing"),
        ("contains", "first"),
        ("getitem", "first"),
        ("contains", "second"),
        ("getitem", "second"),
    ]


def test_dict_params_preserve_value_identity():
    marker = object()

    normalized, params = normalize_one("SELECT :marker", {"marker": marker})

    assert normalized == "SELECT ?"
    assert params == [marker]
    assert params[0] is marker


@pytest.mark.parametrize("stage", ("contains", "getitem"))
@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize(
    "error_type", (ValueError, RuntimeError, KeyboardInterrupt, SystemExit)
)
def test_dict_callback_exception_identity_is_preserved(
    stage, prefix, error_type
):
    failure = error_type(f"{stage} failed")
    source = _ExplodingParams(stage, failure)

    with pytest.raises(error_type) as caught:
        normalize_one(f"SELECT {prefix}value", source)

    assert caught.value is failure


@pytest.mark.parametrize(
    "error_type", (ValueError, RuntimeError, KeyboardInterrupt, SystemExit)
)
def test_sequence_iteration_exception_identity_is_preserved(error_type):
    failure = error_type("iteration failed")

    with pytest.raises(error_type) as caught:
        normalize_one("SELECT :value", _ExplodingList(failure))

    assert caught.value is failure


@pytest.mark.parametrize(
    "source",
    (0, True, "value", b"value", {"value"}, object()),
    ids=("int", "bool", "str", "bytes", "set", "object"),
)
def test_unsupported_param_type_has_exact_error(source):
    with pytest.raises(TypeError) as caught:
        normalize_one("SELECT 1", source)

    assert str(caught.value) == (
        f"params must be list/tuple/dict/None, got {type(source)}"
    )


def test_normalized_named_query_executes_against_real_sqlite():
    sql = (
        'SELECT id, "value:kind", \':category\' AS marker FROM records '
        "WHERE category=:category AND label='it''s :literal' "
        "AND score >= :minimum -- :line\r\n"
        "AND score <= :maximum /* :block */ ORDER BY id"
    )
    source = {"maximum": 30, "category": "alpha", "minimum": 20}

    normalized, params = normalize_one(sql, source)

    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute(
            'CREATE TABLE records('
            'id INTEGER, category TEXT, label TEXT, score INTEGER, "value:kind" INTEGER)'
        )
        connection.executemany(
            "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
            (
                (1, "alpha", "it's :literal", 20, 100),
                (2, "alpha", "it's :literal", 30, 200),
                (3, "beta", "it's :literal", 25, 300),
            ),
        )
        rows = connection.execute(normalized, params).fetchall()

    assert params == ["alpha", 20, 30]
    assert rows == [(1, 100, ":category"), (2, 200, ":category")]
