# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NativeWindow owner and wrapper lifecycle regressions. owner 与包装器生命周期回归。"""

import gc
import weakref

import pytest
import shiboken6
from PySide6.QtQml import QQmlApplicationEngine

from native_window_test_support import (
    ACTUAL_PREVIOUS_STYLE,
    HWND,
    OBSERVED_STYLE,
    _FakeDestroyedSignal,
    _FakeWindow,
    _Outcome,
    _assert_owner_counts,
    _assert_owner_state_empty,
    _assert_state,
    _install,
    _make_hook_env,
)


@pytest.fixture
def hook_env(monkeypatch, qapp):
    return _make_hook_env(monkeypatch)


def _assert_replacement_state(hook, previous_style: int) -> None:
    _assert_state(
        hook,
        attached=[HWND],
        framechanged=[HWND],
        styles={HWND: previous_style},
    )


def _assert_handle_state(hook, hwnd: int, previous_style: int) -> None:
    _assert_state(
        hook,
        attached=[hwnd],
        framechanged=[hwnd],
        styles={hwnd: previous_style},
    )


def _assert_unbound_owner_generation(hook, window, owner_key, token) -> None:
    assert hook._owner_generations == {owner_key: token}
    assert hook._owner_keys == {token: owner_key}
    assert hook._owner_hwnds == {}
    assert hook._hwnd_owners == {}
    assert hook._retired_owner_hwnds == {}
    assert hook._wrapper_owner_keys == {id(window): owner_key}
    assert hook._owner_wrapper_ids == {owner_key: {id(window)}}


def test_detach_uses_owner_bound_hwnd_without_calling_win_id(
    monkeypatch, hook_env
):
    hook, last_error, _messages = hook_env
    window = _FakeWindow(HWND)
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE), _Outcome(OBSERVED_STYLE)],
        positions=[_Outcome(1), _Outcome(1)],
    )
    assert hook.attach(window) is True
    window.fail_win_id(RuntimeError("detach must use tracked hwnd"))

    assert hook.detach(window) is True

    _assert_state(hook)
    assert {call[1] for call in fake.calls} == {HWND}


def test_never_attached_detach_is_noop_without_calling_win_id(hook_env):
    hook, _last_error, _messages = hook_env
    window = _FakeWindow(HWND)
    window.fail_win_id(RuntimeError("unattached detach must not call winId"))

    assert hook.detach(window) is True
    _assert_state(hook)
    _assert_owner_state_empty(hook)


def _prepare_handle_change(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    window = _FakeWindow(HWND)
    replacement_hwnd = 202
    replacement_previous_style = 0x30
    _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE), _Outcome(ACTUAL_PREVIOUS_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE), _Outcome(replacement_previous_style)],
        positions=[_Outcome(1), _Outcome(1)],
    )
    assert hook.attach(window) is True
    window.set_hwnd(replacement_hwnd)
    assert hook.attach(window) is True
    return hook, window, replacement_hwnd, replacement_previous_style


def test_same_owner_handle_change_ignores_stale_destroy_generation(
    monkeypatch, hook_env
):
    hook, window, hwnd, previous_style = _prepare_handle_change(
        monkeypatch, hook_env
    )
    _assert_handle_state(hook, hwnd, previous_style)
    assert len(window.destroyed.callbacks) == 2

    window.destroyed.emit_one(0)
    _assert_handle_state(hook, hwnd, previous_style)
    window.destroyed.emit_one(1)
    _assert_state(hook)
    _assert_owner_state_empty(hook)


def _prepare_connect_failure_handle_change(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    destroyed = _FakeDestroyedSignal([None, RuntimeError("connect failed")])
    window = _FakeWindow(HWND, destroyed=destroyed)
    replacement_hwnd = 202
    replacement_previous_style = 0x30
    _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE), _Outcome(ACTUAL_PREVIOUS_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE), _Outcome(replacement_previous_style)],
        positions=[_Outcome(1), _Outcome(1)],
    )
    assert hook.attach(window) is True
    window.set_hwnd(replacement_hwnd)
    owner_key = hook._owner_identity(window)
    original_token = hook._owner_generations[owner_key]
    return (
        hook, destroyed, window, replacement_hwnd,
        replacement_previous_style, owner_key, original_token,
    )


def test_handle_change_connect_failure_preserves_old_generation_for_retry(
    monkeypatch, hook_env
):
    prepared = _prepare_connect_failure_handle_change(monkeypatch, hook_env)
    hook, destroyed, window, hwnd, previous_style, owner_key, token = prepared

    assert hook.attach(window) is False
    _assert_state(hook)
    _assert_owner_counts(hook)
    _assert_unbound_owner_generation(hook, window, owner_key, token)
    assert len(destroyed.callbacks) == 1
    assert hook.attach(window) is True
    _assert_handle_state(hook, hwnd, previous_style)
    assert len(destroyed.callbacks) == 1
    destroyed.emit_one(0)
    _assert_state(hook)
    _assert_owner_state_empty(hook)


def _prepare_reused_owner(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    first = _FakeWindow(HWND)
    replacement = _FakeWindow(HWND)
    replacement_previous_style = 0x30
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE), _Outcome(ACTUAL_PREVIOUS_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE), _Outcome(replacement_previous_style)],
        positions=[_Outcome(1), _Outcome(1)],
    )
    assert hook.attach(first) is True
    assert hook.attach(replacement) is True
    _assert_replacement_state(hook, replacement_previous_style)
    _assert_owner_counts(hook, active=1, retired=1)
    return hook, first, replacement, replacement_previous_style, fake


def test_new_owner_reusing_hwnd_rejects_stale_owner_operations(
    monkeypatch, hook_env
):
    hook, first, replacement, previous_style, fake = _prepare_reused_owner(
        monkeypatch, hook_env
    )
    calls_after_replacement = list(fake.calls)
    assert hook.finalizeAttach(first) is False
    assert hook.attach(first) is False
    assert hook.detach(first) is True
    assert fake.calls == calls_after_replacement
    _assert_replacement_state(hook, previous_style)

    first.destroyed.emit_one(0)
    _assert_owner_counts(hook, active=1)
    _assert_replacement_state(hook, previous_style)
    replacement.destroyed.emit_one(0)
    _assert_state(hook)
    _assert_owner_state_empty(hook)


def _exercise_qml_wrapper_recreation(monkeypatch, hook_env, engine):
    hook, last_error, _messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE)],
        positions=[_Outcome(1)],
    )
    window = engine.rootObjects()[0]
    hwnd = int(window.winId())
    owner_pointer = shiboken6.getCppPointer(window)[0]
    assert hook.attach(window) is True
    wrapper_ref = weakref.ref(window)
    del window
    gc.collect()
    assert wrapper_ref() is None
    _assert_replacement_state_for_hwnd(hook, hwnd)

    replacement = engine.rootObjects()[0]
    assert shiboken6.getCppPointer(replacement)[0] == owner_pointer
    assert hook.finalizeAttach(replacement) is True
    assert [call[0] for call in fake.calls] == ["get", "set", "position"]
    return hook


def _assert_replacement_state_for_hwnd(hook, hwnd: int) -> None:
    _assert_state(
        hook,
        attached=[hwnd],
        framechanged=[hwnd],
        styles={hwnd: ACTUAL_PREVIOUS_STYLE},
    )
    _assert_owner_counts(hook, active=1)


def test_qml_wrapper_gc_does_not_release_live_native_owner(
    monkeypatch, hook_env, qapp
):
    engine = QQmlApplicationEngine()
    try:
        engine.loadData(b"import QtQuick.Window\nWindow { visible: false }")
        assert len(engine.rootObjects()) == 1
        hook = _exercise_qml_wrapper_recreation(monkeypatch, hook_env, engine)
        shiboken6.delete(engine)
        qapp.processEvents()
        engine = None
        _assert_state(hook)
        _assert_owner_state_empty(hook)
    finally:
        if engine is not None and shiboken6.isValid(engine):
            shiboken6.delete(engine)
            qapp.processEvents()


def test_destroyed_connect_failure_rolls_back_and_retry_cleans_state(
    monkeypatch, hook_env
):
    hook, last_error, _messages = hook_env
    destroyed = _FakeDestroyedSignal([RuntimeError("connect failed")])
    window = _FakeWindow(HWND, destroyed=destroyed)
    _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE)],
        positions=[_Outcome(1)],
    )

    assert hook.attach(window) is False
    _assert_owner_state_empty(hook)
    assert hook.attach(window) is True
    assert len(destroyed.callbacks) == 1
    destroyed.emit_one(0)
    _assert_state(hook)
    _assert_owner_state_empty(hook)
