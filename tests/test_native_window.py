# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NativeWindow WinAPI transaction regressions. NativeWindow WinAPI 事务回归。"""

import pytest

import prismqml.python.window.native_window as native_window
from native_window_test_support import (
    ACTUAL_PREVIOUS_STYLE,
    ERROR_ACCESS_DENIED,
    ERROR_INVALID_WINDOW_HANDLE,
    HWND,
    OBSERVED_STYLE,
    _FakeWindow,
    _Outcome,
    _assert_owner_counts,
    _assert_owner_state_empty,
    _assert_state,
    _install,
    _make_hook_env,
)

REATTACH_CALLS = (
    "get",
    "set",
    "position",
    "set",
    "position",
    "get",
    "set",
    "position",
)


@pytest.fixture
def hook_env(monkeypatch, qapp):
    return _make_hook_env(monkeypatch)


def _install_frame_retry(monkeypatch, last_error):
    return _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE)],
        positions=[_Outcome(0, ERROR_ACCESS_DENIED), _Outcome(1)],
    )


def _install_detach_frame_retry(monkeypatch, last_error):
    return _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE), _Outcome(OBSERVED_STYLE)],
        positions=[_Outcome(1), _Outcome(0, ERROR_ACCESS_DENIED), _Outcome(1)],
    )


def _install_reattach_after_restore_failure(monkeypatch, last_error, replacement):
    return _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE), _Outcome(ACTUAL_PREVIOUS_STYLE)],
        sets=[
            _Outcome(ACTUAL_PREVIOUS_STYLE),
            _Outcome(OBSERVED_STYLE),
            _Outcome(replacement),
        ],
        positions=[_Outcome(1), _Outcome(0, ERROR_ACCESS_DENIED), _Outcome(1)],
    )


def test_zero_style_and_zero_last_error_are_valid(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(0)],
        sets=[_Outcome(0)],
        positions=[_Outcome(1)],
    )

    window = _FakeWindow()
    assert hook.attach(window) is True

    _assert_state(
        hook,
        attached=[HWND],
        framechanged=[HWND],
        styles={HWND: 0},
    )
    assert [call[0] for call in fake.calls] == ["get", "set", "position"]
    assert last_error.set_calls == [0, 0, 0]


def test_get_style_failure_does_not_commit(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(0, ERROR_INVALID_WINDOW_HANDLE)],
    )

    window = _FakeWindow()
    assert hook.attach(window) is False

    _assert_state(hook)
    _assert_owner_counts(hook, active=1)
    assert [call[0] for call in fake.calls] == ["get"]
    window.destroyed.emit_one(0)
    _assert_owner_state_empty(hook)


def test_set_style_failure_does_not_commit(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(0, ERROR_ACCESS_DENIED)],
    )

    window = _FakeWindow()
    assert hook.attach(window) is False

    _assert_state(hook)
    _assert_owner_counts(hook, active=1)
    assert [call[0] for call in fake.calls] == ["get", "set"]
    window.destroyed.emit_one(0)
    _assert_owner_state_empty(hook)


def test_framechanged_failure_retains_partial_state_and_retries(
    monkeypatch, hook_env
):
    hook, last_error, _messages = hook_env
    fake = _install_frame_retry(monkeypatch, last_error)

    window = _FakeWindow()
    assert hook.attach(window) is False
    _assert_state(
        hook,
        attached=[HWND],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )

    assert hook.finalizeAttach(window) is True
    _assert_state(
        hook,
        attached=[HWND],
        framechanged=[HWND],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )
    assert [call[0] for call in fake.calls] == ["get", "set", "position", "position"]


def test_set_window_pos_zero_without_last_error_fails_closed(
    monkeypatch, hook_env
):
    hook, last_error, messages = hook_env
    _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE)],
        positions=[_Outcome(0)],
    )

    window = _FakeWindow()
    assert hook.attach(window) is False

    _assert_state(
        hook,
        attached=[HWND],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )
    assert messages == [
        "NativeWindowHook.attach failed: OSError: "
        "SetWindowPos failed without a LastError code"
    ]


def test_native_system_commands_post_maximize_and_restore(monkeypatch, hook_env):
    hook, last_error, messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        messages=[_Outcome(1), _Outcome(1)],
    )
    window = _FakeWindow()

    assert hook.requestMaximize(window) is True
    assert hook.requestRestore(window) is True

    assert fake.calls == [
        (
            "message",
            HWND,
            native_window.WM_SYSCOMMAND,
            native_window.SC_MAXIMIZE,
            0,
        ),
        (
            "message",
            HWND,
            native_window.WM_SYSCOMMAND,
            native_window.SC_RESTORE,
            0,
        ),
    ]
    assert last_error.set_calls == [0, 0]
    assert messages == []


def test_native_system_command_failure_falls_back_cleanly(
    monkeypatch, hook_env
):
    hook, last_error, messages = hook_env
    _install(
        monkeypatch,
        last_error,
        messages=[_Outcome(0, ERROR_ACCESS_DENIED)],
    )

    assert hook.requestMaximize(_FakeWindow()) is False
    assert messages == [
        "NativeWindowHook.requestMaximize failed: "
        "OSError: [Errno 5] PostMessageW failed"
    ]


def test_detach_restore_failure_preserves_state(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[
            _Outcome(ACTUAL_PREVIOUS_STYLE),
            _Outcome(0, ERROR_ACCESS_DENIED),
        ],
        positions=[_Outcome(1)],
    )
    window = _FakeWindow()
    assert hook.attach(window) is True

    assert hook.detach(window) is False

    _assert_state(
        hook,
        attached=[HWND],
        framechanged=[HWND],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )
    assert [call[0] for call in fake.calls] == ["get", "set", "position", "set"]


def test_detach_destroyed_hwnd_clears_state_without_error(monkeypatch, hook_env):
    hook, last_error, messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[
            _Outcome(ACTUAL_PREVIOUS_STYLE),
            _Outcome(0, ERROR_INVALID_WINDOW_HANDLE),
        ],
        positions=[_Outcome(1)],
    )
    window = _FakeWindow()
    assert hook.attach(window) is True

    assert hook.detach(window) is True

    _assert_state(hook)
    _assert_owner_counts(hook)
    assert messages == []
    assert [call[0] for call in fake.calls] == ["get", "set", "position", "set"]
    window.destroyed.emit_one(0)
    _assert_owner_state_empty(hook)


def test_detach_frame_failure_retries_before_clearing_state(
    monkeypatch, hook_env
):
    hook, last_error, _messages = hook_env
    fake = _install_detach_frame_retry(monkeypatch, last_error)
    window = _FakeWindow()
    assert hook.attach(window) is True

    assert hook.detach(window) is False
    _assert_state(
        hook,
        attached=[HWND],
        restore_pending=[HWND],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )
    assert hook.detach(window) is True
    _assert_state(hook)
    assert [call[0] for call in fake.calls] == [
        "get",
        "set",
        "position",
        "set",
        "position",
        "position",
    ]


def test_attach_repairs_detach_frame_failure_and_reused_hwnd(
    monkeypatch, hook_env
):
    hook, last_error, _messages = hook_env
    replacement_previous_style = 0x30
    fake = _install_reattach_after_restore_failure(
        monkeypatch, last_error, replacement_previous_style
    )
    window = _FakeWindow()
    assert hook.attach(window) is True
    assert hook.detach(window) is False
    _assert_state(
        hook,
        attached=[HWND],
        restore_pending=[HWND],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )

    assert hook.attach(window) is True

    _assert_state(
        hook,
        attached=[HWND],
        framechanged=[HWND],
        styles={HWND: replacement_previous_style},
    )
    _assert_owner_counts(hook, active=1)
    assert tuple(call[0] for call in fake.calls) == REATTACH_CALLS


def test_finalize_attach_and_duplicate_operations_are_idempotent(
    monkeypatch, hook_env
):
    hook, last_error, _messages = hook_env
    fake = _install(
        monkeypatch,
        last_error,
        gets=[_Outcome(OBSERVED_STYLE)],
        sets=[
            _Outcome(ACTUAL_PREVIOUS_STYLE),
            _Outcome(OBSERVED_STYLE),
        ],
        positions=[_Outcome(1), _Outcome(1)],
    )

    window = _FakeWindow()
    assert hook.finalizeAttach(window) is True
    calls_after_attach = list(fake.calls)
    assert hook.attach(window) is True
    assert hook.finalizeAttach(window) is True
    assert fake.calls == calls_after_attach
    assert hook.detach(window) is True
    calls_after_detach = list(fake.calls)
    window.fail_win_id(RuntimeError("duplicate detach must not call winId"))
    assert hook.detach(window) is True
    assert fake.calls == calls_after_detach


def test_one_window_failure_does_not_pollute_another(monkeypatch, hook_env):
    hook, last_error, _messages = hook_env
    second_hwnd = 202
    _install(
        monkeypatch,
        last_error,
        gets=[
            _Outcome(0, ERROR_INVALID_WINDOW_HANDLE),
            _Outcome(OBSERVED_STYLE),
        ],
        sets=[_Outcome(ACTUAL_PREVIOUS_STYLE)],
        positions=[_Outcome(1)],
    )

    failed_window = _FakeWindow(HWND)
    successful_window = _FakeWindow(second_hwnd)
    assert hook.attach(failed_window) is False
    assert hook.attach(successful_window) is True

    _assert_state(
        hook,
        attached=[second_hwnd],
        framechanged=[second_hwnd],
        styles={second_hwnd: ACTUAL_PREVIOUS_STYLE},
    )


def test_runtime_error_logs_traceback_boundary(monkeypatch, hook_env):
    hook, last_error, messages = hook_env
    _install(
        monkeypatch,
        last_error,
        gets=[RuntimeError("native read exploded")],
    )

    assert hook.attach(_FakeWindow()) is False

    _assert_state(hook)
    assert messages == [
        "NativeWindowHook.attach failed: RuntimeError: native read exploded"
    ]


@pytest.mark.parametrize("method", ("finalizeAttach", "detach"))
@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_process_control_from_tracked_state_propagates(
    monkeypatch, hook_env, method, error_type
):
    hook, last_error, _messages = hook_env
    window = _FakeWindow()
    assert hook._prepare_owner(window, HWND) is True
    hook._hwnds.add(HWND)
    hook._original_styles[HWND] = ACTUAL_PREVIOUS_STYLE
    if method == "detach":
        hook._framechanged_hwnds.add(HWND)
        _install(monkeypatch, last_error, sets=[error_type("stop")])
    else:
        _install(monkeypatch, last_error, positions=[error_type("stop")])

    with pytest.raises(error_type, match="stop"):
        getattr(hook, method)(window)

    _assert_state(
        hook,
        attached=[HWND],
        framechanged=[HWND] if method == "detach" else [],
        styles={HWND: ACTUAL_PREVIOUS_STYLE},
    )


def test_message_filter_logs_runtime_error_with_traceback(monkeypatch, hook_env):
    _hook, _last_error, messages = hook_env
    event_filter = native_window._MsgFilter(set())

    def fail_cast(*_args):
        raise RuntimeError("invalid MSG")

    monkeypatch.setattr(native_window.ctypes, "cast", fail_cast)

    assert event_filter.nativeEventFilter(b"windows_generic_MSG", 1) == (False, 0)
    assert messages == [
        "NativeWindow message filter failed: RuntimeError: invalid MSG"
    ]


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_message_filter_does_not_swallow_process_control(
    monkeypatch, hook_env, error_type
):
    event_filter = native_window._MsgFilter(set())

    def fail_cast(*_args):
        raise error_type("stop")

    monkeypatch.setattr(native_window.ctypes, "cast", fail_cast)

    with pytest.raises(error_type, match="stop"):
        event_filter.nativeEventFilter(b"windows_generic_MSG", 1)


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_process_control_errors_propagate(monkeypatch, hook_env, error_type):
    hook, last_error, _messages = hook_env
    _install(monkeypatch, last_error, gets=[error_type("stop")])

    with pytest.raises(error_type, match="stop"):
        hook.attach(_FakeWindow())

    _assert_state(hook)
