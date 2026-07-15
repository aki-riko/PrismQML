# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowCore.__init__ characterization. 窗口状态初始化现状合同。"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Optional

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject

from prismqml.python import config
from prismqml.python.window import window_core
from prismqml.python.window.fluent_window import Window


_MUTABLE_FIELDS = (
    "_pending_props",
    "_pending_calls",
    "_nav_items",
    "_bottom_nav_items",
    "_pages",
)
_PRE_CONFIG_FIELDS = (
    "_window_type",
    "_engine",
    "_window",
    "_content_area",
    "_pending_props",
    "_pending_calls",
    "_title",
    "_width",
    "_height",
    "_icon",
    "_icon_colored",
    "_nav_items",
    "_bottom_nav_items",
    "_current_index",
    "_pages",
)
_SPLASH_FIELDS = (
    "_splash_enabled",
    "_splash_icon",
    "_splash_title",
    "_splash_subtitle",
    "_splash_instance",
)
_TRACKED_FIELDS = frozenset(
    (*_PRE_CONFIG_FIELDS, "_lazy_loading", *_SPLASH_FIELDS)
)
_ASSIGNMENT_ORDER = (*_PRE_CONFIG_FIELDS, "_lazy_loading", *_SPLASH_FIELDS)
_ERROR_TYPES = (RuntimeError, ValueError, KeyboardInterrupt, SystemExit)


class _ConfigProbe:
    def __init__(self, events, value, error=None):
        self._events = events
        self._value = value
        self._error = error

    @property
    def lazyLoading(self):
        self._events.append(("config", "property"))
        if self._error is not None:
            raise self._error
        return self._value


class _RecordingWindowCore(window_core.WindowCore):
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
            events.append(("set", name, parent_ready))
            if name == type(self).failure_field:
                raise type(self).failure_error
        super().__setattr__(name, value)


def _install_config_value(monkeypatch, value):
    manager = SimpleNamespace(lazyLoading=value)
    monkeypatch.setattr(config, "getConfigManager", lambda: manager)


def _install_config_probe(
    monkeypatch,
    events,
    parent,
    value,
    *,
    factory_error=None,
    property_error=None,
):
    probe = _ConfigProbe(events, value, property_error)

    def get_config_manager():
        instance = _RecordingWindowCore.captured_instance
        events.append(("config", "factory", instance.parent() is parent))
        if factory_error is not None:
            raise factory_error
        return probe

    monkeypatch.setattr(config, "getConfigManager", get_config_manager)


def _dispose(*objects):
    for obj in objects:
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def _reset_recording_state():
    _RecordingWindowCore.assignment_events = None
    _RecordingWindowCore.captured_instance = None
    _RecordingWindowCore.expected_parent = None
    _RecordingWindowCore.failure_field = None
    _RecordingWindowCore.failure_error = None


def _expected_success_events():
    events = [("set", name, True) for name in _PRE_CONFIG_FIELDS]
    events.extend(
        [
            ("config", "factory", True),
            ("config", "property"),
            ("set", "_lazy_loading", True),
        ]
    )
    events.extend(("set", name, True) for name in _SPLASH_FIELDS)
    return events


def _assert_same_error(error_type, expected_error, action):
    with pytest.raises(error_type) as exc_info:
        action()
    assert exc_info.value is expected_error


def _assert_partial_state(instance, window_type, parent):
    assert instance.parent() is parent
    assert instance._window_type is window_type
    for name in _PRE_CONFIG_FIELDS:
        assert hasattr(instance, name)
    assert not hasattr(instance, "_lazy_loading")
    for name in _SPLASH_FIELDS:
        assert not hasattr(instance, name)


def _prepare_config_failure(monkeypatch, stage, error_type):
    events = []
    parent = QObject()
    token = object()
    expected_error = error_type(f"{stage} failed")
    _RecordingWindowCore.assignment_events = events
    _RecordingWindowCore.captured_instance = None
    _RecordingWindowCore.expected_parent = parent
    _RecordingWindowCore.failure_field = None
    _RecordingWindowCore.failure_error = None
    _install_config_probe(
        monkeypatch,
        events,
        parent,
        object(),
        factory_error=expected_error if stage == "factory" else None,
        property_error=expected_error if stage == "property" else None,
    )
    return events, parent, token, expected_error


def _expected_failure_events(stage):
    events = [("set", name, True) for name in _PRE_CONFIG_FIELDS]
    events.append(("config", "factory", True))
    if stage == "property":
        events.append(("config", "property"))
    return events


def _prepare_assignment_failure(monkeypatch, field, error_type):
    events = []
    parent = QObject()
    token = object()
    expected_error = error_type(f"{field} failed")
    _RecordingWindowCore.assignment_events = events
    _RecordingWindowCore.captured_instance = None
    _RecordingWindowCore.expected_parent = parent
    _RecordingWindowCore.failure_field = field
    _RecordingWindowCore.failure_error = expected_error
    _install_config_probe(monkeypatch, events, parent, object())
    return events, parent, token, expected_error


def _expected_assignment_failure_events(field):
    events = []
    for name in _ASSIGNMENT_ORDER:
        if name == "_lazy_loading":
            events.extend(
                [("config", "factory", True), ("config", "property")]
            )
        events.append(("set", name, True))
        if name == field:
            return events
    raise AssertionError(f"Unknown tracked field: {field}")


def _assert_assignment_prefix(instance, field, window_type, parent):
    target_index = _ASSIGNMENT_ORDER.index(field)
    assert instance.parent() is parent
    for name in _ASSIGNMENT_ORDER[:target_index]:
        assert hasattr(instance, name)
    for name in _ASSIGNMENT_ORDER[target_index:]:
        assert not hasattr(instance, name)
    if field != "_window_type":
        assert instance._window_type is window_type


def _assert_public_signature():
    signature = inspect.signature(window_core.WindowCore.__init__)
    assert tuple(signature.parameters) == ("self", "window_type", "parent")
    self_parameter = signature.parameters["self"]
    type_parameter = signature.parameters["window_type"]
    parent_parameter = signature.parameters["parent"]
    assert all(
        parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for parameter in (self_parameter, type_parameter, parent_parameter)
    )
    assert type_parameter.annotation is int
    assert type_parameter.default is window_core.WindowType.BAR
    assert parent_parameter.annotation == Optional[QObject]
    assert parent_parameter.default is None
    assert signature.return_annotation is inspect.Signature.empty
    assert inspect.isfunction(window_core.WindowCore.__init__)


def _assert_default_state(instance, lazy_value):
    assert instance.parent() is None
    assert instance._window_type is window_core.WindowType.BAR
    assert instance._engine is instance._window is instance._content_area is None
    assert instance._title == "PrismQML App"
    assert (instance._width, instance._height) == (1200, 800)
    assert (instance._icon, instance._icon_colored) == ("", True)
    assert instance._current_index == 0
    assert instance._lazy_loading is lazy_value
    assert all(not getattr(instance, name) for name in _MUTABLE_FIELDS)
    assert type(instance._pending_props) is type(instance._pages) is dict
    assert all(
        type(getattr(instance, name)) is list
        for name in ("_pending_calls", "_nav_items", "_bottom_nav_items")
    )
    assert instance._splash_enabled is True
    assert (instance._splash_icon, instance._splash_title) == ("", "")
    assert instance._splash_subtitle == ""
    assert instance._splash_instance is None
    assert not hasattr(instance, "_splash_component")


def test_default_state_and_public_signature_are_preserved(monkeypatch):
    lazy_value = object()
    _install_config_value(monkeypatch, lazy_value)

    instance = window_core.WindowCore()
    try:
        _assert_public_signature()
        _assert_default_state(instance, lazy_value)
    finally:
        _dispose(instance)


def test_public_window_forwards_parent_and_raw_window_type(monkeypatch):
    _install_config_value(monkeypatch, False)
    parent = QObject()
    token = object()
    previous = window_core.WindowCore._current_window_instance
    current_marker = object()
    window_core.WindowCore._current_window_instance = current_marker
    instance = Window(window_type=token, parent=parent)
    try:
        assert instance.parent() is parent
        assert instance._window_type is token
        assert window_core.WindowCore._current_window_instance is current_marker
    finally:
        window_core.WindowCore._current_window_instance = previous
        _dispose(parent)


def test_mutable_state_is_fresh_within_and_across_instances(monkeypatch):
    _install_config_value(monkeypatch, True)
    left = window_core.WindowCore()
    right = window_core.WindowCore()
    try:
        values = [
            getattr(item, name)
            for item in (left, right)
            for name in _MUTABLE_FIELDS
        ]
        assert len({id(value) for value in values}) == len(values)
        left._pending_props["key"] = "value"
        left._pending_calls.append(("method", 1))
        left._nav_items.append(object())
        left._bottom_nav_items.append(object())
        left._pages[0] = object()
        assert all(not getattr(right, name) for name in _MUTABLE_FIELDS)
    finally:
        _dispose(left, right)


def test_assignment_and_config_read_order_are_preserved(monkeypatch):
    events = []
    parent = QObject()
    token = object()
    lazy_value = object()
    _RecordingWindowCore.assignment_events = events
    _RecordingWindowCore.expected_parent = parent
    _install_config_probe(monkeypatch, events, parent, lazy_value)
    instance = _RecordingWindowCore(window_type=token, parent=parent)
    try:
        assert events == _expected_success_events()
        assert instance._window_type is token
        assert instance._lazy_loading is lazy_value
    finally:
        _reset_recording_state()
        _dispose(parent)


def test_qobject_parent_owns_unopened_window_core(monkeypatch, qapp):
    _install_config_value(monkeypatch, True)
    parent = QObject()
    instance = window_core.WindowCore(parent=parent)

    assert instance.parent() is parent
    assert instance in parent.children()
    parent.deleteLater()
    QCoreApplication.sendPostedEvents(parent, QEvent.DeferredDelete)
    qapp.processEvents()

    assert not shiboken6.isValid(parent)
    assert not shiboken6.isValid(instance)


def test_invalid_parent_fails_before_any_tracked_assignment(monkeypatch):
    _install_config_value(monkeypatch, True)
    events = []
    previous = window_core.WindowCore._current_window_instance
    marker = object()
    window_core.WindowCore._current_window_instance = marker
    _RecordingWindowCore.assignment_events = events
    _RecordingWindowCore.expected_parent = None
    try:
        with pytest.raises(TypeError):
            _RecordingWindowCore(parent=object())
        instance = _RecordingWindowCore.captured_instance
        assert events == []
        assert not hasattr(instance, "_window_type")
        assert window_core.WindowCore._current_window_instance is marker
    finally:
        window_core.WindowCore._current_window_instance = previous
        _reset_recording_state()


@pytest.mark.parametrize("stage", ("factory", "property"))
@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_config_failures_propagate_with_exact_partial_state(
    monkeypatch, stage, error_type
):
    events, parent, token, expected_error = _prepare_config_failure(
        monkeypatch, stage, error_type
    )
    previous = window_core.WindowCore._current_window_instance
    marker = object()
    window_core.WindowCore._current_window_instance = marker

    try:
        _assert_same_error(
            error_type,
            expected_error,
            lambda: _RecordingWindowCore(window_type=token, parent=parent),
        )
        instance = _RecordingWindowCore.captured_instance
        _assert_partial_state(instance, token, parent)
        assert events == _expected_failure_events(stage)
        assert window_core.WindowCore._current_window_instance is marker
    finally:
        instance = _RecordingWindowCore.captured_instance
        window_core.WindowCore._current_window_instance = previous
        _reset_recording_state()
        _dispose(parent)
        assert instance is None or not shiboken6.isValid(instance)


@pytest.mark.parametrize("field", _ASSIGNMENT_ORDER)
@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_field_assignment_failures_propagate_without_rollback(
    monkeypatch, field, error_type
):
    events, parent, token, expected_error = _prepare_assignment_failure(
        monkeypatch, field, error_type
    )
    previous = window_core.WindowCore._current_window_instance
    marker = object()
    window_core.WindowCore._current_window_instance = marker
    try:
        _assert_same_error(
            error_type,
            expected_error,
            lambda: _RecordingWindowCore(window_type=token, parent=parent),
        )
        instance = _RecordingWindowCore.captured_instance
        _assert_assignment_prefix(instance, field, token, parent)
        assert events == _expected_assignment_failure_events(field)
        assert window_core.WindowCore._current_window_instance is marker
    finally:
        instance = _RecordingWindowCore.captured_instance
        window_core.WindowCore._current_window_instance = previous
        _reset_recording_state()
        _dispose(parent)
        assert instance is None or not shiboken6.isValid(instance)
