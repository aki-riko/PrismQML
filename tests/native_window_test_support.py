# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NativeWindow test doubles and invariants. NativeWindow 测试替身与不变量。"""

from dataclasses import dataclass
from typing import Optional

import prismqml.python.window.native_window as native_window


HWND = 101
OBSERVED_STYLE = 0x10
ACTUAL_PREVIOUS_STYLE = 0x20
ERROR_ACCESS_DENIED = 5
ERROR_INVALID_WINDOW_HANDLE = 1400


@dataclass(frozen=True)
class _Outcome:
    value: object
    error: Optional[int] = None


class _LastError:
    def __init__(self):
        self.value = ERROR_ACCESS_DENIED
        self.set_calls = []

    def set(self, value: int) -> None:
        self.set_calls.append(value)
        self.value = value

    def set_from_api(self, value: int) -> None:
        self.value = value

    def get(self) -> int:
        return self.value


class _FakeUser32:
    def __init__(self, last_error, *, gets=(), sets=(), positions=()):
        self._last_error = last_error
        self._gets = list(gets)
        self._sets = list(sets)
        self._positions = list(positions)
        self.calls = []

    def _next(self, outcomes, name):
        if not outcomes:
            raise AssertionError(f"unexpected {name} call")
        outcome = outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        if outcome.error is not None:
            self._last_error.set_from_api(outcome.error)
        return outcome.value

    def GetWindowLongPtrW(self, hwnd, index):
        self.calls.append(("get", hwnd, index))
        return self._next(self._gets, "GetWindowLongPtrW")

    def SetWindowLongPtrW(self, hwnd, index, style):
        self.calls.append(("set", hwnd, index, style))
        return self._next(self._sets, "SetWindowLongPtrW")

    def SetWindowPos(self, hwnd, insert_after, x, y, width, height, flags):
        self.calls.append(
            ("position", hwnd, insert_after, x, y, width, height, flags)
        )
        return self._next(self._positions, "SetWindowPos")


class _FakeDestroyedSignal:
    def __init__(self, connect_errors=()):
        self.callbacks = []
        self._connect_errors = list(connect_errors)

    def connect(self, callback):
        if self._connect_errors:
            error = self._connect_errors.pop(0)
            if error is not None:
                raise error
        self.callbacks.append(callback)

    def emit_one(self, index: int) -> None:
        self.callbacks[index]()


class _FakeWindow:
    def __init__(self, hwnd=HWND, *, destroyed=None):
        self._hwnd = hwnd
        self._win_id_error = None
        self.destroyed = destroyed or _FakeDestroyedSignal()

    def winId(self):
        if self._win_id_error is not None:
            raise self._win_id_error
        return self._hwnd

    def set_hwnd(self, hwnd: int) -> None:
        self._hwnd = hwnd

    def fail_win_id(self, error: BaseException) -> None:
        self._win_id_error = error


def _assert_state(
    hook, *, attached=(), framechanged=(), restore_pending=(), styles=None
):
    assert hook._hwnds == set(attached)
    assert hook._framechanged_hwnds == set(framechanged)
    assert hook._restore_pending_hwnds == set(restore_pending)
    assert hook._original_styles == (styles or {})
    assert set(hook._original_styles) == hook._hwnds
    assert hook._framechanged_hwnds <= hook._hwnds
    assert set(restore_pending) <= hook._hwnds
    assert hook._framechanged_hwnds.isdisjoint(set(restore_pending))
    assert len(hook._owner_hwnds) == len(hook._hwnd_owners)
    for token, hwnd in hook._owner_hwnds.items():
        assert hook._hwnd_owners.get(hwnd) is token
    for hwnd, token in hook._hwnd_owners.items():
        assert hook._owner_hwnds.get(token) == hwnd
    assert set(hook._owner_keys) == set(hook._owner_generations.values())
    for token, owner_key in hook._owner_keys.items():
        assert hook._owner_generations.get(owner_key) is token
    assert set(hook._retired_owner_hwnds).isdisjoint(hook._owner_hwnds)


def _assert_owner_counts(hook, *, active: int = 0, retired: int = 0) -> None:
    assert len(hook._owner_hwnds) == active
    assert len(hook._retired_owner_hwnds) == retired


def _assert_owner_state_empty(hook) -> None:
    assert hook._owner_generations == {}
    assert hook._owner_keys == {}
    assert hook._owner_hwnds == {}
    assert hook._hwnd_owners == {}
    assert hook._retired_owner_hwnds == {}
    assert hook._wrapper_owner_keys == {}
    assert hook._owner_wrapper_ids == {}


def _make_hook_env(monkeypatch):
    last_error = _LastError()
    messages = []
    monkeypatch.setattr(native_window.sys, "platform", "win32")
    monkeypatch.setattr(native_window, "_set_last_error", last_error.set)
    monkeypatch.setattr(native_window, "_get_last_error", last_error.get)
    monkeypatch.setattr(native_window, "exception", messages.append)
    hook = native_window.NativeWindowHook(_isolated=True, _install_filter=False)
    return hook, last_error, messages


def _install(monkeypatch, last_error, **outcomes):
    fake = _FakeUser32(last_error, **outcomes)
    monkeypatch.setattr(native_window, "user32", fake)
    return fake
