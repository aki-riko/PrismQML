# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel.__init__ characterization. SQL 模型构造现状合同。"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject

from prismqml.python.models import _sqlite_connection, sql_list_model


_BASE_FIELDS = ("_router", "_db_path", "_page_size", "_lru_capacity")
_QUERY_FIELDS = (
    "_sql",
    "_count_sql",
    "_params",
    "_count_params",
    "_formatters",
    "_cursor_columns",
    "_cursor_nullable_index",
    "_cursor_col_indices",
    "_cursor_directions",
    "_row_count",
    "_columns",
    "_role_to_col",
    "_role_names",
    "_cache",
)
_TRACKED_FIELDS = frozenset((*_BASE_FIELDS, *_QUERY_FIELDS))
_MUTABLE_FIELDS = (
    "_params",
    "_count_params",
    "_formatters",
    "_cursor_columns",
    "_cursor_col_indices",
    "_cursor_directions",
    "_columns",
    "_role_to_col",
    "_role_names",
    "_cache",
)
_ERROR_TYPES = (ValueError, OSError, RuntimeError, KeyboardInterrupt, SystemExit)


class _GuardRouter(sql_list_model.DbRouter):
    def __init__(self):
        self.calls = 0

    def route(self, params):
        self.calls += 1
        raise AssertionError("constructor queried router")


class _IntProbe:
    def __init__(self, events, label, value=1, error=None):
        self._events = events
        self._label = label
        self._value = value
        self._error = error

    def __int__(self):
        self._events.append(self._label)
        if self._error is not None:
            raise self._error
        return self._value


class _NoRustAccess:
    def __getattr__(self, name):
        raise AssertionError(f"constructor accessed Rust backend: {name}")


class _RecordingSqlListModel(sql_list_model.SqlListModel):
    captured_instance = None
    assignment_events = None
    expected_parent = None
    failure_field = None
    failure_error = None

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        cls.captured_instance = instance
        return instance

    def __setattr__(self, name, value):
        events = type(self).assignment_events
        if events is not None and name in _TRACKED_FIELDS:
            try:
                parent_ready = self.parent() is type(self).expected_parent
            except RuntimeError:
                parent_ready = False
            events.append((name, parent_ready))
            if name == type(self).failure_field:
                raise type(self).failure_error
        super().__setattr__(name, value)


@pytest.fixture(autouse=True)
def _reset_recording_state():
    _clear_recording_state()
    yield
    _clear_recording_state()


def _clear_recording_state():
    _RecordingSqlListModel.captured_instance = None
    _RecordingSqlListModel.assignment_events = None
    _RecordingSqlListModel.expected_parent = None
    _RecordingSqlListModel.failure_field = None
    _RecordingSqlListModel.failure_error = None


def _dispose(qapp, *objects):
    for obj in objects:
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()
    for obj in objects:
        if obj is not None:
            assert not shiboken6.isValid(obj)


def _assert_same_error(error_type, expected_error, action):
    with pytest.raises(error_type) as exc_info:
        action()
    assert exc_info.value is expected_error


def _assert_public_signature():
    signature = inspect.signature(sql_list_model.SqlListModel.__init__)
    assert tuple(signature.parameters) == (
        "self",
        "db_path_or_router",
        "parent",
        "page_size",
        "lru_capacity",
    )
    parameters = signature.parameters
    assert all(
        parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for parameter in parameters.values()
    )
    assert parameters["db_path_or_router"].annotation == "Union[str, Path, DbRouter]"
    assert parameters["parent"].default is None
    assert parameters["page_size"].annotation == "int"
    assert parameters["page_size"].default == sql_list_model.PAGE_SIZE_DEFAULT
    assert parameters["lru_capacity"].annotation == "int"
    assert parameters["lru_capacity"].default == sql_list_model.LRU_CAPACITY_DEFAULT
    assert signature.return_annotation == "None"


def _assert_empty_query_state(model):
    assert model._sql == model._count_sql == ""
    assert model._cursor_nullable_index is None
    assert model._row_count == 0
    list_fields = (
        "_params",
        "_count_params",
        "_cursor_columns",
        "_cursor_col_indices",
        "_cursor_directions",
        "_columns",
    )
    dict_fields = ("_formatters", "_role_to_col", "_role_names")
    assert all(type(getattr(model, name)) is list for name in list_fields)
    assert all(not getattr(model, name) for name in list_fields)
    assert all(type(getattr(model, name)) is dict for name in dict_fields)
    assert all(not getattr(model, name) for name in dict_fields)
    assert model._cache._capacity == model._lru_capacity
    assert not model._cache._pages


def _prepare_recording(parent, *, field=None, error=None):
    events = []
    _RecordingSqlListModel.assignment_events = events
    _RecordingSqlListModel.expected_parent = parent
    _RecordingSqlListModel.failure_field = field
    _RecordingSqlListModel.failure_error = error
    return events


def _assert_capacity_failure_state(
    instance, events, conversion_events, stage, parent
):
    expected_conversions = ["page_size"]
    expected_names = ["_router", "_db_path"]
    if stage == "lru_capacity":
        expected_conversions.append("lru_capacity")
        expected_names.append("_page_size")
    assert conversion_events == expected_conversions
    assert [name for name, _ready in events] == expected_names
    assert all(ready for _name, ready in events)
    assert instance.parent() is parent
    assert all(hasattr(instance, name) for name in expected_names)
    missing = _TRACKED_FIELDS.difference(expected_names)
    assert all(not hasattr(instance, name) for name in missing)


def test_default_state_and_public_signature_are_preserved(qapp):
    model = None
    try:
        model = sql_list_model.SqlListModel("unused.sqlite")
        _assert_public_signature()
        assert type(model._router) is sql_list_model._SingleDbRouter
        assert model._router.route([]) == ["unused.sqlite"]
        assert model._db_path == "unused.sqlite"
        assert model._page_size == sql_list_model.PAGE_SIZE_DEFAULT
        assert model._lru_capacity == sql_list_model.LRU_CAPACITY_DEFAULT
        assert model.rowCount() == 0
        assert model.roleNames() == {}
        _assert_empty_query_state(model)
    finally:
        _dispose(qapp, model)


def test_path_source_does_not_open_or_create_database(qapp, monkeypatch, tmp_path):
    path = tmp_path / "missing.sqlite"

    def fail_connect(*_args, **_kwargs):
        raise AssertionError("constructor opened sqlite database")

    monkeypatch.setattr(_sqlite_connection.sqlite3, "connect", fail_connect)
    monkeypatch.setattr(sql_list_model, "_rs", _NoRustAccess())
    model = None
    try:
        model = sql_list_model.SqlListModel(path)
        assert model._db_path == str(path)
        assert model._router.route([]) == [str(path)]
        assert not path.exists()
        _assert_empty_query_state(model)
    finally:
        _dispose(qapp, model)


def test_router_source_keeps_identity_without_routing(qapp):
    router = _GuardRouter()
    model = None
    try:
        model = sql_list_model.SqlListModel(router)
        assert model._router is router
        assert model._db_path == ""
        assert router.calls == 0
        _assert_empty_query_state(model)
    finally:
        _dispose(qapp, model)


@pytest.mark.parametrize(
    ("page_size", "lru_capacity", "expected"),
    ((0, -7, (1, 1)), (-3, 8, (1, 8)), (5, 9, (5, 9))),
)
def test_capacity_values_preserve_clamping(qapp, page_size, lru_capacity, expected):
    model = None
    try:
        model = sql_list_model.SqlListModel(
            "unused.sqlite",
            page_size=page_size,
            lru_capacity=lru_capacity,
        )
        assert (model._page_size, model._lru_capacity) == expected
        assert model._cache._capacity == expected[1]
    finally:
        _dispose(qapp, model)


def test_capacity_conversion_order_and_values_are_preserved(qapp):
    events = []
    page_size = _IntProbe(events, "page_size", 7)
    lru_capacity = _IntProbe(events, "lru_capacity", 11)
    model = None
    try:
        model = sql_list_model.SqlListModel(
            "unused.sqlite",
            page_size=page_size,
            lru_capacity=lru_capacity,
        )
        assert events == ["page_size", "lru_capacity"]
        assert (model._page_size, model._lru_capacity) == (7, 11)
    finally:
        _dispose(qapp, model)


def test_qobject_parent_owns_unqueried_model(qapp):
    parent = QObject()
    model = sql_list_model.SqlListModel("unused.sqlite", parent=parent)
    assert model.parent() is parent
    assert model in parent.children()
    parent.deleteLater()
    QCoreApplication.sendPostedEvents(parent, QEvent.DeferredDelete)
    qapp.processEvents()
    assert not shiboken6.isValid(parent)
    assert not shiboken6.isValid(model)


def test_mutable_query_state_is_fresh_across_instances(qapp):
    left = right = None
    try:
        left = sql_list_model.SqlListModel("left.sqlite")
        right = sql_list_model.SqlListModel("right.sqlite")
        values = [
            getattr(model, name)
            for model in (left, right)
            for name in _MUTABLE_FIELDS
        ]
        values.extend((left._cache._pages, right._cache._pages))
        assert len({id(value) for value in values}) == len(values)
        left._params.append(1)
        left._formatters["value"] = str
        left._columns.append("value")
        left._role_names[257] = b"value"
        left._cache.put(0, [[1]], [1])
        assert not right._params
        assert not right._formatters
        assert not right._columns
        assert not right._role_names
        assert not right._cache._pages
    finally:
        _dispose(qapp, left, right)


def test_assignment_order_starts_after_qobject_parent(qapp):
    parent = QObject()
    events = _prepare_recording(parent)
    model = None
    try:
        model = _RecordingSqlListModel("unused.sqlite", parent=parent)
        assert sql_list_model._QUERY_STATE_FIELDS == _QUERY_FIELDS
        assert events == [(name, True) for name in (*_BASE_FIELDS, *_QUERY_FIELDS)]
        assert model.parent() is parent
        _assert_empty_query_state(model)
    finally:
        _dispose(qapp, model, parent)


def test_invalid_parent_fails_before_python_state(qapp):
    events = _prepare_recording(None)
    with pytest.raises(TypeError):
        _RecordingSqlListModel("unused.sqlite", parent=object())
    instance = _RecordingSqlListModel.captured_instance
    assert events == []
    assert not hasattr(instance, "_router")
    assert not shiboken6.isValid(instance)
    _dispose(qapp, instance)


def test_invalid_source_preserves_type_error_and_empty_state(qapp):
    parent = QObject()
    source = object()
    events = _prepare_recording(parent)
    try:
        with pytest.raises(TypeError) as exc_info:
            _RecordingSqlListModel(source, parent=parent)
        instance = _RecordingSqlListModel.captured_instance
        assert str(exc_info.value) == (
            f"db_path_or_router 必须是 str/Path/DbRouter,got {type(source)}"
        )
        assert events == []
        assert instance.parent() is parent
        assert shiboken6.isValid(instance)
        assert all(not hasattr(instance, name) for name in _BASE_FIELDS)
    finally:
        instance = _RecordingSqlListModel.captured_instance
        _dispose(qapp, parent)
        assert instance is None or not shiboken6.isValid(instance)


@pytest.mark.parametrize("stage", ("page_size", "lru_capacity"))
@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_capacity_errors_propagate_with_exact_partial_state(
    qapp, stage, error_type
):
    parent = QObject()
    events = _prepare_recording(parent)
    conversion_events = []
    expected_error = error_type(f"{stage} failed")
    page_error = expected_error if stage == "page_size" else None
    lru_error = expected_error if stage == "lru_capacity" else None
    page_size = _IntProbe(conversion_events, "page_size", 7, page_error)
    lru_capacity = _IntProbe(conversion_events, "lru_capacity", 11, lru_error)
    try:
        _assert_same_error(
            error_type,
            expected_error,
            lambda: _RecordingSqlListModel(
                "unused.sqlite",
                parent=parent,
                page_size=page_size,
                lru_capacity=lru_capacity,
            ),
        )
        instance = _RecordingSqlListModel.captured_instance
        _assert_capacity_failure_state(
            instance, events, conversion_events, stage, parent
        )
    finally:
        instance = _RecordingSqlListModel.captured_instance
        _dispose(qapp, parent)
        assert instance is None or not shiboken6.isValid(instance)


@pytest.mark.parametrize("field", _QUERY_FIELDS)
@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_query_field_errors_propagate_without_rollback(qapp, field, error_type):
    parent = QObject()
    expected_error = error_type(f"{field} failed")
    events = _prepare_recording(parent, field=field, error=expected_error)
    try:
        _assert_same_error(
            error_type,
            expected_error,
            lambda: _RecordingSqlListModel("unused.sqlite", parent=parent),
        )
        instance = _RecordingSqlListModel.captured_instance
        target_index = _QUERY_FIELDS.index(field)
        assigned_fields = (*_BASE_FIELDS, *_QUERY_FIELDS[:target_index])
        expected_events = (*assigned_fields, field)
        assert [name for name, _ready in events] == list(expected_events)
        assert all(ready for _name, ready in events)
        assert instance.parent() is parent
        assert all(hasattr(instance, name) for name in assigned_fields)
        assert all(
            not hasattr(instance, name)
            for name in _QUERY_FIELDS[target_index:]
        )
    finally:
        instance = _RecordingSqlListModel.captured_instance
        _dispose(qapp, parent)
        assert instance is None or not shiboken6.isValid(instance)


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_page_cache_errors_preserve_prior_query_state(
    qapp, monkeypatch, error_type
):
    parent = QObject()
    expected_error = error_type("PageCache failed")
    events = _prepare_recording(parent)
    capacities = []

    def fail_cache(capacity):
        capacities.append(capacity)
        raise expected_error

    monkeypatch.setattr(sql_list_model, "PageCache", fail_cache)
    try:
        _assert_same_error(
            error_type,
            expected_error,
            lambda: _RecordingSqlListModel("unused.sqlite", parent=parent),
        )
        instance = _RecordingSqlListModel.captured_instance
        expected_fields = (*_BASE_FIELDS, *_QUERY_FIELDS[:-1])
        assert capacities == [sql_list_model.LRU_CAPACITY_DEFAULT]
        assert [name for name, _ready in events] == list(expected_fields)
        assert all(ready for _name, ready in events)
        assert all(hasattr(instance, name) for name in expected_fields)
        assert not hasattr(instance, "_cache")
    finally:
        instance = _RecordingSqlListModel.captured_instance
        _dispose(qapp, parent)
        assert instance is None or not shiboken6.isValid(instance)
