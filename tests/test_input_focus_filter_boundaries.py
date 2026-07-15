# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Input focus filter branch contracts. 输入焦点过滤器分支合同。"""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QEvent

import prismqml.python.core.input_focus_filter as focus_module


def _resolve(outcome):
    if isinstance(outcome, BaseException):
        raise outcome
    return outcome


class _PrimaryPosition:
    def __init__(self, outcome, events):
        self._outcome = outcome
        self._events = events

    def toPoint(self):
        self._events.append("toPoint")
        return _resolve(self._outcome)


class _MouseEvent:
    def __init__(self, primary, fallback, events, event_type=QEvent.Type.MouseButtonPress):
        self._primary = primary
        self._fallback = fallback
        self._events = events
        self._event_type = event_type

    def type(self):
        self._events.append("type")
        return self._event_type

    def globalPosition(self):
        self._events.append("globalPosition")
        return _PrimaryPosition(self._primary, self._events)

    def globalPos(self):
        self._events.append("globalPos")
        return _resolve(self._fallback)


class _PrimaryCallEvent(_MouseEvent):
    def globalPosition(self):
        self._events.append("globalPosition")
        return _resolve(self._primary)


class _FocusObject:
    def __init__(self, events, set_focus_error=None):
        self._events = events
        self._set_focus_error = set_focus_error

    def setFocus(self, focused):
        self._events.append(("setFocus", focused))
        if self._set_focus_error is not None:
            raise self._set_focus_error


def _install_focus_context(monkeypatch, events, focus, *, is_input=True, inside=False):
    class App:
        def focusObject(self):
            events.append("focusObject")
            return focus

    monkeypatch.setattr(
        focus_module,
        "QGuiApplication",
        SimpleNamespace(instance=lambda: App()),
    )
    monkeypatch.setattr(
        focus_module,
        "_is_input_item",
        lambda item: events.append(("isInput", item)) or is_input,
    )
    monkeypatch.setattr(
        focus_module,
        "_is_inside",
        lambda item, point: events.append(("isInside", item, point)) or inside,
    )


@pytest.fixture
def focus_filter(qapp):
    return focus_module._InputFocusFilter()


def test_non_mouse_event_stops_before_application_lookup(
    focus_filter, monkeypatch
):
    events = []
    event = _MouseEvent(None, None, events, QEvent.Type.KeyPress)
    monkeypatch.setattr(
        focus_module,
        "QGuiApplication",
        SimpleNamespace(instance=lambda: pytest.fail("application queried")),
    )

    assert focus_filter.eventFilter(object(), event) is False
    assert events == ["type"]


def test_mouse_event_without_application_stops_before_focus_lookup(
    focus_filter, monkeypatch
):
    events = []
    event = _MouseEvent(None, None, events)

    def no_application():
        events.append("instance")
        return None

    monkeypatch.setattr(
        focus_module,
        "QGuiApplication",
        SimpleNamespace(instance=no_application),
    )
    monkeypatch.setattr(focus_module, "_is_input_item", pytest.fail)
    monkeypatch.setattr(focus_module, "_is_inside", pytest.fail)

    assert focus_filter.eventFilter(object(), event) is False
    assert events == ["type", "instance"]


def test_non_input_focus_stops_before_coordinate_lookup(focus_filter, monkeypatch):
    events = []
    focus = _FocusObject(events)
    event = _MouseEvent(None, None, events)
    _install_focus_context(monkeypatch, events, focus, is_input=False)

    assert focus_filter.eventFilter(object(), event) is False
    assert events == ["type", "focusObject", ("isInput", focus)]


def test_primary_position_inside_focus_never_uses_fallback(focus_filter, monkeypatch):
    events = []
    focus = _FocusObject(events)
    point = object()
    event = _MouseEvent(point, pytest.fail, events)
    _install_focus_context(monkeypatch, events, focus, inside=True)

    assert focus_filter.eventFilter(object(), event) is False
    assert events == [
        "type",
        "focusObject",
        ("isInput", focus),
        "globalPosition",
        "toPoint",
        ("isInside", focus, point),
    ]


def test_primary_position_outside_focus_clears_without_fallback(
    focus_filter, monkeypatch
):
    events = []
    focus = _FocusObject(events)
    point = object()
    event = _MouseEvent(point, pytest.fail, events)
    _install_focus_context(monkeypatch, events, focus)

    assert focus_filter.eventFilter(object(), event) is False
    assert events == [
        "type",
        "focusObject",
        ("isInput", focus),
        "globalPosition",
        "toPoint",
        ("isInside", focus, point),
        ("setFocus", False),
    ]


def test_primary_none_position_still_runs_hit_test_without_fallback(
    focus_filter, monkeypatch
):
    events = []
    focus = _FocusObject(events)
    event = _MouseEvent(None, pytest.fail, events)
    _install_focus_context(monkeypatch, events, focus, inside=True)

    assert focus_filter.eventFilter(object(), event) is False
    assert ("isInside", focus, None) in events
    assert ("setFocus", False) not in events
    assert "globalPos" not in events


@pytest.mark.parametrize("error_type", (AttributeError, RuntimeError))
def test_primary_position_failure_uses_fallback_and_clears_focus(
    focus_filter, monkeypatch, error_type
):
    events = []
    messages = []
    focus = _FocusObject(events)
    point = object()
    event = _MouseEvent(error_type("primary failed"), point, events)
    _install_focus_context(monkeypatch, events, focus)
    monkeypatch.setattr(focus_module, "debug", messages.append)

    assert focus_filter.eventFilter(object(), event) is False
    assert events[-3:] == ["globalPos", ("isInside", focus, point), ("setFocus", False)]
    assert messages == [
        "[InputFocusFilter] globalPosition 不可用,尝试 globalPos: primary failed"
    ]


@pytest.mark.parametrize("error_type", (AttributeError, RuntimeError))
def test_global_position_call_failure_uses_fallback(
    focus_filter, monkeypatch, error_type
):
    events = []
    focus = _FocusObject(events)
    point = object()
    event = _PrimaryCallEvent(error_type("primary call failed"), point, events)
    _install_focus_context(monkeypatch, events, focus)

    assert focus_filter.eventFilter(object(), event) is False
    assert "toPoint" not in events
    assert events[-3:] == ["globalPos", ("isInside", focus, point), ("setFocus", False)]


def test_fallback_none_position_still_runs_hit_test_as_resolved(
    focus_filter, monkeypatch
):
    events = []
    focus = _FocusObject(events)
    event = _MouseEvent(AttributeError("primary"), None, events)
    _install_focus_context(monkeypatch, events, focus, inside=True)

    assert focus_filter.eventFilter(object(), event) is False
    assert ("isInside", focus, None) in events
    assert ("setFocus", False) not in events


@pytest.mark.parametrize("fallback_error", (AttributeError("missing"), RuntimeError("bad")))
def test_both_position_paths_unavailable_leave_focus_unchanged(
    focus_filter, monkeypatch, fallback_error
):
    events = []
    messages = []
    focus = _FocusObject(events)
    event = _MouseEvent(AttributeError("primary"), fallback_error, events)
    _install_focus_context(monkeypatch, events, focus)
    monkeypatch.setattr(focus_module, "debug", messages.append)

    assert focus_filter.eventFilter(object(), event) is False
    assert not any(isinstance(item, tuple) and item[0] == "setFocus" for item in events)
    assert not any(isinstance(item, tuple) and item[0] == "isInside" for item in events)
    assert messages == [
        "[InputFocusFilter] globalPosition 不可用,尝试 globalPos: primary",
        f"[InputFocusFilter] 获取鼠标全局坐标失败: {fallback_error}",
    ]


@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_primary_fallback_debug_error_preserves_identity(
    focus_filter, monkeypatch, error_type
):
    events = []
    focus = _FocusObject(events)
    failure = error_type("debug failed")
    event = _MouseEvent(AttributeError("primary"), pytest.fail, events)
    _install_focus_context(monkeypatch, events, focus)

    def fail_debug(_message):
        raise failure

    monkeypatch.setattr(focus_module, "debug", fail_debug)
    with pytest.raises(error_type) as caught:
        focus_filter.eventFilter(object(), event)

    assert caught.value is failure
    assert "globalPos" not in events


@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_final_position_debug_error_preserves_identity(
    focus_filter, monkeypatch, error_type
):
    events = []
    messages = []
    focus = _FocusObject(events)
    failure = error_type("debug failed")
    event = _MouseEvent(AttributeError("primary"), AttributeError("fallback"), events)
    _install_focus_context(monkeypatch, events, focus)

    def fail_second_debug(message):
        messages.append(message)
        if len(messages) == 2:
            raise failure

    monkeypatch.setattr(focus_module, "debug", fail_second_debug)
    with pytest.raises(error_type) as caught:
        focus_filter.eventFilter(object(), event)

    assert caught.value is failure
    assert len(messages) == 2
    assert not any(isinstance(item, tuple) and item[0] == "isInside" for item in events)


@pytest.mark.parametrize("error_type", (TypeError, KeyboardInterrupt, SystemExit))
def test_primary_unhandled_error_preserves_identity(
    focus_filter, monkeypatch, error_type
):
    events = []
    focus = _FocusObject(events)
    failure = error_type("stop")
    event = _MouseEvent(failure, pytest.fail, events)
    _install_focus_context(monkeypatch, events, focus)

    with pytest.raises(error_type) as caught:
        focus_filter.eventFilter(object(), event)

    assert caught.value is failure
    assert "globalPos" not in events


@pytest.mark.parametrize("error_type", (TypeError, KeyboardInterrupt, SystemExit))
def test_global_position_call_unhandled_error_preserves_identity(
    focus_filter, monkeypatch, error_type
):
    events = []
    focus = _FocusObject(events)
    failure = error_type("stop")
    event = _PrimaryCallEvent(failure, pytest.fail, events)
    _install_focus_context(monkeypatch, events, focus)

    with pytest.raises(error_type) as caught:
        focus_filter.eventFilter(object(), event)

    assert caught.value is failure
    assert "toPoint" not in events
    assert "globalPos" not in events


@pytest.mark.parametrize("error_type", (TypeError, KeyboardInterrupt, SystemExit))
def test_fallback_unhandled_error_preserves_identity(
    focus_filter, monkeypatch, error_type
):
    events = []
    focus = _FocusObject(events)
    failure = error_type("stop")
    event = _MouseEvent(AttributeError("primary"), failure, events)
    _install_focus_context(monkeypatch, events, focus)

    with pytest.raises(error_type) as caught:
        focus_filter.eventFilter(object(), event)

    assert caught.value is failure
    assert not any(isinstance(item, tuple) and item[0] == "setFocus" for item in events)


@pytest.mark.parametrize("error_type", (AttributeError, RuntimeError, TypeError))
def test_focus_clear_ordinary_error_is_logged_and_not_consumed(
    focus_filter, monkeypatch, error_type
):
    events = []
    messages = []
    focus = _FocusObject(events, error_type("clear failed"))
    event = _MouseEvent(object(), None, events)
    _install_focus_context(monkeypatch, events, focus)
    monkeypatch.setattr(focus_module, "debug", messages.append)

    assert focus_filter.eventFilter(object(), event) is False
    assert messages == ["[InputFocusFilter] 清除输入焦点失败: clear failed"]


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_focus_clear_process_control_error_preserves_identity(
    focus_filter, monkeypatch, error_type
):
    events = []
    failure = error_type("stop")
    focus = _FocusObject(events, failure)
    event = _MouseEvent(object(), None, events)
    _install_focus_context(monkeypatch, events, focus)

    with pytest.raises(error_type) as caught:
        focus_filter.eventFilter(object(), event)

    assert caught.value is failure
