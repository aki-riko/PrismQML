# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SQLite named-token regression tests. SQLite 命名词法回归。"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from prismqml.python.models._sql_query_tools import (
    _has_named_placeholder,
    find_top_level_order_by,
    normalize_one,
    strip_strings_and_comments,
    validate_keyset_query,
)


_PARAMETER_NAMES = (
    "alpha",
    "_private2",
    "1",
    "名字2",
    "🙂",
    "\u0301",
    "\u00a0",
    "\u200d",
    "a\u0301",
    "\ufeff",
    "a$b",
    "a::b",
    "a::b(c)",
    "a::b::c(d.e-f)",
    "::b",
    "1a::",
    "::a::",
    "a::::b",
    "a::()",
    "::::a::",
)
_INVALID_PARAMETER_NAMES = ("::", "::::", "::()", ":::a", "a:::b", "a:::")


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


class _CountingSql(str):
    def __new__(cls, value):
        instance = super().__new__(cls, value)
        instance.accesses = 0
        return instance

    def __getitem__(self, key):
        self.accesses += 1
        return super().__getitem__(key)


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize("name", _PARAMETER_NAMES)
def test_sqlite_named_parameter_grammar_matches_real_engine(prefix, name):
    sql = f"SELECT {prefix}{name}"
    source = {name: 7}

    normalized, params = normalize_one(sql, source)

    with closing(sqlite3.connect(":memory:")) as connection:
        oracle = connection.execute(sql, source).fetchone()
        actual = connection.execute(normalized, params).fetchone()

    assert normalized == "SELECT ?"
    assert params == [7]
    assert actual == oracle == (7,)


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize("name", _INVALID_PARAMETER_NAMES)
def test_invalid_namespace_token_keeps_sqlite_failure(prefix, name):
    sql = f"SELECT {prefix}{name}"

    normalized, params = normalize_one(sql, {name: 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(sqlite3.Error):
            connection.execute(sql, {name: 7}).fetchone()
        with pytest.raises(sqlite3.Error):
            connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []


def test_mixed_prefixes_preserve_occurrence_order_and_missing_tokens():
    marker = object()
    source = _TrackingParams({"x": marker, "a::b(c)": 9})
    sql = "SELECT :x, @x, $x, @missing::ns(suffix), :x, $a::b(c)"

    normalized, params = normalize_one(sql, source)

    assert normalized == "SELECT ?, ?, ?, @missing::ns(suffix), ?, ?"
    assert params == [marker, marker, marker, marker, 9]
    assert params[:4] == [marker] * 4
    assert source.events == [
        ("contains", "x"), ("getitem", "x"),
        ("contains", "x"), ("getitem", "x"),
        ("contains", "x"), ("getitem", "x"),
        ("contains", "missing::ns(suffix)"),
        ("contains", "x"), ("getitem", "x"),
        ("contains", "a::b(c)"), ("getitem", "a::b(c)"),
    ]


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize(
    ("separator", "error_type", "message"),
    (
        pytest.param(" ", sqlite3.OperationalError, "unrecognized token", id="space"),
        pytest.param("\t", sqlite3.OperationalError, "unrecognized token", id="tab"),
        pytest.param("\r", sqlite3.OperationalError, "unrecognized token", id="cr"),
        pytest.param("\n", sqlite3.OperationalError, "unrecognized token", id="lf"),
        pytest.param("\v", sqlite3.OperationalError, "unrecognized token", id="vt"),
        pytest.param("\f", sqlite3.OperationalError, "unrecognized token", id="ff"),
        pytest.param("\x00", sqlite3.ProgrammingError, "null character", id="nul"),
    ),
)
def test_invalid_suffix_keeps_sqlite_failure(
    prefix, separator, error_type, message
):
    name = f"a(b{separator}c)"
    sql = f"SELECT {prefix}{name}"

    normalized, params = normalize_one(sql, {name: 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(error_type) as original:
            connection.execute(sql, {name: 7}).fetchone()
        with pytest.raises(error_type) as after:
            connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []
    assert message in str(original.value)
    assert message in str(after.value)


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize(
    "separator", ("\u00a0", "\u1680", "\u2003", "\u2028", "\u3000")
)
def test_unicode_whitespace_remains_a_valid_sqlite_suffix(prefix, separator):
    name = f"a(b{separator}c)"
    sql = f"SELECT {prefix}{name}"

    normalized, params = normalize_one(sql, {name: 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        oracle = connection.execute(sql, {name: 7}).fetchone()
        actual = connection.execute(normalized, params).fetchone()

    assert normalized == "SELECT ?"
    assert params == [7]
    assert actual == oracle == (7,)


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize("name", ("\ud800", "\udfff", "a(\ud800)"))
def test_lone_surrogate_keeps_python_sqlite_encoding_failure(prefix, name):
    sql = f"SELECT {prefix}{name}"

    normalized, params = normalize_one(sql, {name: 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(UnicodeEncodeError) as original:
            connection.execute(sql, {name: 7}).fetchone()
        with pytest.raises(UnicodeEncodeError) as after:
            connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []
    assert str(after.value) == str(original.value)


def test_quoted_identifiers_strings_and_comments_hide_all_prefixes():
    source = _TrackingParams({
        "at": 1, "cash$value": 2, "value": 3, "visible": 4,
    })
    sql = (
        "SELECT [bracket:at@cash$value], `tick``:at@cash$value`, "
        "\"double\"\":at@cash$value\", ':at@cash$value' "
        "-- :at@cash$value\n"
        "/* :at@cash$value */ WHERE id IN (:visible, @visible, $visible)"
    )

    normalized, params = normalize_one(sql, source)

    assert normalized == (
        "SELECT [bracket:at@cash$value], `tick``:at@cash$value`, "
        "\"double\"\":at@cash$value\", ':at@cash$value' "
        "-- :at@cash$value\n"
        "/* :at@cash$value */ WHERE id IN (?, ?, ?)"
    )
    assert params == [4, 4, 4]
    assert source.events == [
        ("contains", "visible"), ("getitem", "visible"),
        ("contains", "visible"), ("getitem", "visible"),
        ("contains", "visible"), ("getitem", "visible"),
    ]


@pytest.mark.parametrize("sql", ("SELECT [a:x", "SELECT `a:x"))
def test_unterminated_quoted_identifier_is_preserved_to_end(sql):
    source = _TrackingParams({"x": 1})

    normalized, params = normalize_one(sql, source)
    masked = strip_strings_and_comments(sql)

    assert normalized == sql
    assert params == []
    assert source.events == []
    assert masked == "SELECT " + " " * (len(sql) - len("SELECT "))


def test_unquoted_dollar_identifier_is_not_a_named_parameter():
    source = _TrackingParams({"b": 7})
    sql = "SELECT a$b FROM ids"

    normalized, params = normalize_one(sql, source)

    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE ids(id INTEGER, a$b INTEGER)")
        connection.execute("INSERT INTO ids VALUES (1, 9)")
        row = connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []
    assert source.events == []
    assert row == (9,)
    assert validate_keyset_query(
        "SELECT id, a$b FROM ids ORDER BY id", ["id"]
    ) == ["ASC"]


@pytest.mark.parametrize(
    ("sql", "expected"),
    (
        ("SELECT \ufeff$x", (7,)),
        ("SELECT (\ufeff$x)", (7,)),
        ("SELECT +\ufeff$x", (7,)),
        ("SELECT \ufeff\ufeff$x", (7,)),
        ("SELECT 1+\ufeff$x", (8,)),
    ),
)
def test_dollar_after_token_start_bom_matches_sqlite(sql, expected):
    normalized, params = normalize_one(sql, {"x": 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        oracle = connection.execute(sql, {"x": 7}).fetchone()
        actual = connection.execute(normalized, params).fetchone()

    assert params == [7]
    assert actual == oracle == expected


@pytest.mark.parametrize(
    "stem", ("a", "_", "名字", "\u2003", "🙂", "\u200d")
)
def test_dollar_after_bom_inside_identifier_is_not_rewritten(stem):
    column = f"{stem}\ufeff$x"
    sql = f"SELECT {column} FROM ids"
    normalized, params = normalize_one(sql, {"x": 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute(f"CREATE TABLE ids({column} INTEGER)")
        connection.execute("INSERT INTO ids VALUES (9)")
        oracle = connection.execute(sql, {"x": 7}).fetchone()
        actual = connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []
    assert actual == oracle == (9,)


def test_dollar_after_bom_inside_numeric_token_is_not_rewritten():
    sql = "SELECT 1.\ufeff$x"

    normalized, params = normalize_one(sql, {"x": 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(sqlite3.Error) as original:
            connection.execute(sql, {"x": 7}).fetchone()
        with pytest.raises(type(original.value)) as after:
            connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []
    assert str(after.value) == str(original.value)


@pytest.mark.parametrize(
    ("sql", "expected"),
    (
        ("SELECT ?1$x", "SELECT ?1?"),
        ("SELECT ?$x", "SELECT ??"),
        ("SELECT 0x1.$x", "SELECT 0x1.?"),
        ("SELECT 0x1.\ufeff$x", "SELECT 0x1.\ufeff?"),
        ("SELECT ?1\ufeff$x", "SELECT ?1\ufeff?"),
        ("SELECT 1.2.\ufeff$x", "SELECT 1.2.\ufeff?"),
    ),
)
def test_dollar_after_completed_token_and_bom_is_rewritten(sql, expected):
    normalized, params = normalize_one(sql, {"x": 7})

    assert normalized == expected
    assert params == [7]
    assert _has_named_placeholder(sql)


@pytest.mark.parametrize("sql", ("SELECT 1$x", "SELECT 1.$x"))
def test_dollar_inside_numeric_token_is_not_rewritten(sql):
    normalized, params = normalize_one(sql, {"x": 7})

    assert normalized == sql
    assert params == []
    assert not _has_named_placeholder(sql)


def test_invalid_colon_run_is_scanned_linearly():
    sql = _CountingSql("SELECT " + ":" * 10_000)

    normalized, params = normalize_one(sql, {})

    assert normalized == sql
    assert params == []
    assert sql.accesses < 50_000


def test_named_placeholder_detection_scans_invalid_colon_run_linearly():
    sql = _CountingSql(":" * 10_000)

    assert not _has_named_placeholder(sql)
    assert sql.accesses < 50_000


def test_bom_context_scans_repeated_embedded_dollars_linearly():
    sql = _CountingSql("1.\ufeff$x+" * 2_000)

    normalized, params = normalize_one(sql, {})

    assert normalized == sql
    assert params == []
    assert sql.accesses < len(sql) * 12


def test_structural_mask_hides_quoted_tokens_and_preserves_indexes():
    sql = (
        "SELECT [SELECT :hidden], `WINDOW``@hidden`, \"GROUP BY $hidden\", "
        "':hidden' -- ORDER BY :line\n"
        "FROM records /* SELECT @block */ WHERE a$b=:visible ORDER BY id"
    )

    masked = strip_strings_and_comments(sql)

    assert len(masked) == len(sql)
    assert [index for index, char in enumerate(masked) if char == "\n"] == [
        index for index, char in enumerate(sql) if char == "\n"
    ]
    assert masked.count("SELECT") == 1
    assert "WINDOW" not in masked
    assert "GROUP BY" not in masked
    assert "ORDER BY :line" not in masked
    assert "SELECT @block" not in masked
    assert "WHERE a$b=:visible ORDER BY id" in masked
    assert find_top_level_order_by(sql) == sql.rfind(" ORDER BY ")


def test_keyset_validation_accepts_quoted_markers_after_normalization():
    sql = (
        "SELECT id, [WINDOW:kind] AS kind, `SELECT@owner` AS owner, "
        "a$b AS cash FROM records WHERE id>=@minimum ORDER BY id"
    )

    normalized, params = normalize_one(sql, {"minimum": 2})

    assert normalized.endswith("WHERE id>=? ORDER BY id")
    assert params == [2]
    assert validate_keyset_query(normalized, ["id"]) == ["ASC"]


def test_keyset_detects_dollar_after_token_start_bom():
    sql = "SELECT id FROM ids WHERE id=\ufeff$x ORDER BY id"

    with pytest.raises(ValueError, match="命名占位符"):
        validate_keyset_query(sql, ["id"])


def test_keyset_ignores_dollar_inside_bom_identifier():
    sql = "SELECT id, a\ufeff$x FROM ids ORDER BY id"

    assert validate_keyset_query(sql, ["id"]) == ["ASC"]


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize(
    "payload", ("'x'", '"x"', "`x`", "[x]", "'--'", "/*x*/")
)
def test_parameter_suffix_protected_text_matches_sqlite_and_keyset_rejects(
    prefix, payload,
):
    name = f"a({payload})"
    expression = f"{prefix}{name}"

    normalized, params = normalize_one(f"SELECT {expression}", {name: 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        oracle = connection.execute(
            f"SELECT {expression}", {name: 7}
        ).fetchone()
        actual = connection.execute(normalized, params).fetchone()

    assert normalized == "SELECT ?"
    assert params == [7]
    assert actual == oracle == (7,)
    with pytest.raises(ValueError, match="命名占位符"):
        validate_keyset_query(
            f"SELECT id FROM ids WHERE id>={expression} ORDER BY id", ["id"]
        )


@pytest.mark.parametrize("prefix", tuple(":@$"))
@pytest.mark.parametrize("name", ("a(", "a(payload", "a::("))
def test_unclosed_parameter_suffix_is_not_partially_rewritten(prefix, name):
    sql = f"SELECT {prefix}{name}"

    normalized, params = normalize_one(sql, {"a": 1, name: 7})

    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(sqlite3.Error) as original:
            connection.execute(sql, {"a": 1, name: 7}).fetchone()
        with pytest.raises(type(original.value)) as after:
            connection.execute(normalized, params).fetchone()

    assert normalized == sql
    assert params == []
    assert str(after.value) == str(original.value)
