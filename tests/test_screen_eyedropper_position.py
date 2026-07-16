# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Screen eyedropper position contracts. 屏幕取色器位置合同。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QPoint, QRect

from prismqml.python.providers import screen_eyedropper as eyedropper


_UPDATE_POSITION = eyedropper.ScreenEyedropperWindow._update_position_and_color
_CONSTANTS = eyedropper.ScreenEyedropperConstants


class _FakeScreen:
    def __init__(self, events, geometry, errors=None):
        self.events = events
        self.rect = geometry
        self.errors = errors or {}

    def geometry(self):
        self.events.append(("screen.geometry",))
        error = self.errors.get("geometry")
        if error is not None:
            raise error
        return self.rect


class _FakeImage:
    def __init__(self, events, *, is_null, pixel_value=0, errors=None):
        self.events = events
        self.is_null = is_null
        self.pixel_value = pixel_value
        self.errors = errors or {}

    def isNull(self):
        self.events.append(("image.is_null",))
        error = self.errors.get("is_null")
        if error is not None:
            raise error
        return self.is_null

    def pixel(self, x, y):
        self.events.append(("image.pixel", x, y))
        error = self.errors.get("pixel")
        if error is not None:
            raise error
        return self.pixel_value


class _FakeWindow:
    def __init__(self, events, *, width=20, height=10, capture_result=None, errors=None):
        self._constants = _CONSTANTS
        self._current_color = object()
        self._captured_image = object()
        self.events = events
        self.window_width = width
        self.window_height = height
        self.capture_result = capture_result
        self.errors = errors or {}
        self.last_move = None

    def _event(self, name, *args):
        self.events.append((name, *args))
        error = self.errors.get(name)
        if error is not None:
            raise error

    def width(self):
        self._event("window.width")
        return self.window_width

    def height(self):
        self._event("window.height")
        return self.window_height

    def move(self, x, y):
        self._event("window.move", x, y)
        self.last_move = (x, y)

    def _capture_screen(self, cursor_pos, screen):
        self._event("window.capture", cursor_pos, screen)
        self._captured_image = self.capture_result

    def update(self):
        self._event("window.update")


class _FakeQtApis:
    def __init__(self, events, cursor, screen_at, primary, errors=None):
        self.events = events
        self.cursor = cursor
        self.screen_at_result = screen_at
        self.primary_result = primary
        self.errors = errors or {}
        self.color_values = []

    def _event(self, name, *args):
        self.events.append((name, *args))
        error = self.errors.get(name)
        if error is not None:
            raise error

    def cursor_pos(self):
        self._event("cursor.pos")
        return self.cursor

    def screen_at(self, cursor):
        self._event("application.screen_at", cursor)
        return self.screen_at_result

    def primary_screen(self):
        self._event("application.primary_screen")
        return self.primary_result

    def color(self, value):
        self._event("color.create", value)
        converted = ("converted-color", value)
        self.color_values.append(converted)
        return converted

    def install(self, monkeypatch):
        monkeypatch.setattr(eyedropper, "QCursor", SimpleNamespace(pos=self.cursor_pos))
        monkeypatch.setattr(
            eyedropper,
            "QGuiApplication",
            SimpleNamespace(screenAt=self.screen_at, primaryScreen=self.primary_screen),
        )
        monkeypatch.setattr(eyedropper, "QColor", self.color)


def _make_case(
    monkeypatch,
    *,
    cursor=QPoint(50, 50),
    geometry=QRect(0, 0, 200, 200),
    use_primary=False,
    capture_result=None,
    window_errors=None,
    api_errors=None,
):
    events = []
    screen = _FakeScreen(events, geometry)
    screen_at = None if use_primary else screen
    api = _FakeQtApis(events, cursor, screen_at, screen, api_errors)
    window = _FakeWindow(events, capture_result=capture_result, errors=window_errors)
    api.install(monkeypatch)
    return SimpleNamespace(events=events, screen=screen, api=api, window=window)


def _event_names(events):
    return [event[0] for event in events]


@pytest.mark.parametrize("use_primary", [False, True])
def test_update_position_selects_cursor_screen_then_primary_fallback(
    monkeypatch, use_primary
):
    case = _make_case(monkeypatch, use_primary=use_primary)

    _UPDATE_POSITION(case.window)

    names = _event_names(case.events)
    assert names[:2] == ["cursor.pos", "application.screen_at"]
    assert names.count("application.primary_screen") == int(use_primary)
    assert names.index("screen.geometry") < names.index("window.move")
    assert case.events[names.index("window.capture")][1:] == (
        case.api.cursor,
        case.screen,
    )


@pytest.mark.parametrize(
    ("cursor", "expected", "dimension_calls"),
    [
        (QPoint(50, 50), (66, 66), ["window.width", "window.height"]),
        (QPoint(180, 50), (144, 66), ["window.width", "window.width", "window.height"]),
        (QPoint(50, 190), (66, 164), ["window.width", "window.height", "window.height"]),
        (
            QPoint(180, 190),
            (144, 164),
            ["window.width", "window.width", "window.height", "window.height"],
        ),
    ],
)
def test_update_position_keeps_window_near_cursor_in_all_overflow_quadrants(
    monkeypatch, cursor, expected, dimension_calls
):
    case = _make_case(monkeypatch, cursor=cursor)

    _UPDATE_POSITION(case.window)

    names = _event_names(case.events)
    assert case.window.last_move == expected
    assert [name for name in names if name in {"window.width", "window.height"}] == dimension_calls
    assert names.index("window.move") < names.index("window.capture")


def test_update_position_samples_new_capture_center_before_repaint(monkeypatch):
    events = []
    image = _FakeImage(events, is_null=False, pixel_value=0x11223344)
    case = _make_case(monkeypatch, capture_result=image)
    image.events = case.events
    old_color = case.window._current_color

    _UPDATE_POSITION(case.window)

    names = _event_names(case.events)
    center = _CONSTANTS.CAPTURE_SIZE // 2
    assert old_color is not case.window._current_color
    assert case.window._current_color == ("converted-color", 0x11223344)
    assert ("image.pixel", center, center) in case.events
    assert names.index("window.capture") < names.index("image.pixel")
    assert names.index("color.create") < names.index("window.update")


@pytest.mark.parametrize("captured_kind", ["none", "null"])
def test_update_position_preserves_color_for_missing_or_null_capture(
    monkeypatch, captured_kind
):
    events = []
    image = None if captured_kind == "none" else _FakeImage(events, is_null=True)
    case = _make_case(monkeypatch, capture_result=image)
    if image is not None:
        image.events = case.events
    old_color = case.window._current_color

    _UPDATE_POSITION(case.window)

    names = _event_names(case.events)
    assert case.window._current_color is old_color
    assert "image.pixel" not in names
    assert "color.create" not in names
    assert names[-1] == "window.update"


@pytest.mark.parametrize(
    ("stage", "error", "expected_prefix", "moved", "captured", "color_changed"),
    [
        (
            "application.screen_at",
            RuntimeError("screen"),
            ["cursor.pos", "application.screen_at"],
            False,
            False,
            False,
        ),
        (
            "window.capture",
            OSError("capture"),
            ["window.move", "window.capture"],
            True,
            False,
            False,
        ),
        ("image.pixel", ValueError("pixel"), ["image.is_null", "image.pixel"], True, True, False),
        ("window.move", KeyboardInterrupt(), ["window.height", "window.move"], False, False, False),
        ("window.update", SystemExit(9), ["color.create", "window.update"], True, True, True),
    ],
)
def test_update_position_propagates_failures_with_ordered_partial_state(
    monkeypatch, stage, error, expected_prefix, moved, captured, color_changed
):
    events = []
    image_errors = {"pixel": error} if stage == "image.pixel" else None
    image = _FakeImage(events, is_null=False, pixel_value=7, errors=image_errors)
    window_errors = {stage: error} if stage.startswith("window.") else None
    api_errors = {stage: error} if stage.startswith("application.") else None
    case = _make_case(
        monkeypatch,
        capture_result=image,
        window_errors=window_errors,
        api_errors=api_errors,
    )
    image.events = case.events
    old_color = case.window._current_color

    with pytest.raises(type(error)) as caught:
        _UPDATE_POSITION(case.window)

    names = _event_names(case.events)
    assert caught.value is error
    assert names[-2:] == expected_prefix
    assert (case.window.last_move is not None) is moved
    assert (case.window._captured_image is image) is captured
    assert (case.window._current_color is not old_color) is color_changed
    assert "window.update" not in names[:-1]
