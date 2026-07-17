# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Screen eyedropper start transaction contracts. 屏幕取色启动事务合同。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from prismqml.python.providers import screen_eyedropper as eyedropper


_START_PICKING = eyedropper.ScreenEyedropperWindow.start_picking
_CONSTANTS = eyedropper.ScreenEyedropperConstants


class _FakeTimer:
    def __init__(self, events, errors):
        self.events = events
        self.errors = errors

    def start(self, interval):
        self.events.append(("timer.start", interval))
        error = self.errors.get("timer.start")
        if error is not None:
            raise error

    def stop(self):
        self.events.append(("timer.stop",))


class _FakeWindow:
    def __init__(self, *, refresh_rate=120.0, update_result=True, errors=None):
        self.events = []
        self.errors = errors or {}
        self._constants = _CONSTANTS
        self._timer = _FakeTimer(self.events, self.errors)
        self._is_dark = False
        self.refresh_rate = refresh_rate
        self.update_result = update_result

    def _event(self, name, *args):
        self.events.append((name, *args))
        error = self.errors.get(name)
        if error is not None:
            raise error

    def show(self):
        self._event("window.show")

    def raise_(self):
        self._event("window.raise")

    def activateWindow(self):
        self._event("window.activate")

    def grabMouse(self):
        self._event("window.grab_mouse")

    def grabKeyboard(self):
        self._event("window.grab_keyboard")

    def releaseMouse(self):
        self._event("window.release_mouse")

    def releaseKeyboard(self):
        self._event("window.release_keyboard")

    def hide(self):
        self._event("window.hide")

    def screen(self):
        self._event("window.screen")
        return SimpleNamespace(refreshRate=lambda: self.refresh_rate)

    def _update_position_and_color(self):
        self._event("window.update")
        return self.update_result


def _event_names(window):
    return [event[0] for event in window.events]


def test_start_picking_commits_after_initial_capture():
    window = _FakeWindow(refresh_rate=120.0)

    result = _START_PICKING(window, True)

    assert result is True
    assert window._is_dark is True
    assert window.events == [
        ("window.show",),
        ("window.raise",),
        ("window.activate",),
        ("window.grab_mouse",),
        ("window.grab_keyboard",),
        ("window.screen",),
        ("timer.start", 8),
        ("window.update",),
    ]


@pytest.mark.parametrize(
    ("stage", "expected_releases"),
    [
        ("window.show", []),
        ("window.grab_mouse", []),
        ("window.grab_keyboard", ["window.release_mouse"]),
        (
            "timer.start",
            ["window.release_keyboard", "window.release_mouse"],
        ),
        (
            "window.update",
            ["window.release_keyboard", "window.release_mouse"],
        ),
    ],
)
def test_start_picking_rolls_back_ordinary_failures(stage, expected_releases):
    window = _FakeWindow(errors={stage: RuntimeError(stage)})

    result = _START_PICKING(window)

    assert result is False
    names = _event_names(window)
    assert names[-1] == "window.hide"
    assert "timer.stop" in names
    assert [name for name in names if name.startswith("window.release")] == expected_releases


def test_start_picking_rolls_back_when_initial_capture_has_no_screen():
    window = _FakeWindow(update_result=False)

    result = _START_PICKING(window)

    assert result is False
    assert _event_names(window)[-4:] == [
        "timer.stop",
        "window.release_keyboard",
        "window.release_mouse",
        "window.hide",
    ]


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(7)])
def test_start_picking_rolls_back_and_propagates_control_failures(error):
    window = _FakeWindow(errors={"window.update": error})

    with pytest.raises(type(error)) as caught:
        _START_PICKING(window)

    assert caught.value is error
    assert _event_names(window)[-4:] == [
        "timer.stop",
        "window.release_keyboard",
        "window.release_mouse",
        "window.hide",
    ]


@pytest.mark.parametrize("started", [False, True])
def test_manager_emits_started_only_after_window_commit(qapp, started):
    del qapp
    manager = eyedropper.ScreenEyedropperManager()
    original_window = manager._picker_window
    original_dark = manager._is_dark
    signals = []

    def slot():
        signals.append("started")

    manager.pickingStarted.connect(slot)
    manager._picker_window = SimpleNamespace(start_picking=lambda _dark: started)
    try:
        manager.startPicking(True)
        assert signals == (["started"] if started else [])
    finally:
        manager.pickingStarted.disconnect(slot)
        manager._picker_window = original_window
        manager._is_dark = original_dark
