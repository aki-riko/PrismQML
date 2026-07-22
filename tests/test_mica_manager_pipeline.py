# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Python MicaManager DWM transaction contracts. Python Mica DWM 事务合同。"""

from __future__ import annotations

import ctypes

import pytest

from prismqml.python.window import mica_window


class _FakeWindow:
    def __init__(self, handle=0x1234, error=None):
        self.handle = handle
        self.error = error

    def winId(self):
        if self.error is not None:
            raise self.error
        return self.handle


class _FakeDwmSetAttribute:
    def __init__(self, results=None, errors=None):
        self.results = results or {}
        self.errors = errors or {}
        self.calls = []

    def __call__(self, hwnd, attribute, value_pointer, value_size):
        value = ctypes.cast(value_pointer, ctypes.POINTER(ctypes.c_int)).contents.value
        self.calls.append((hwnd, attribute, value, value_size))
        error = self.errors.get(attribute)
        if error is not None:
            raise error
        return self.results.get(attribute, 0)


def _manager(dwm, *, build=mica_window.WIN11_BACKDROP_BUILD_THRESHOLD):
    manager = mica_window.MicaManager()
    manager._is_win11 = True
    manager._is_mica_supported = build >= mica_window.WIN11_BACKDROP_BUILD_THRESHOLD
    manager._windows_build = build
    manager._dwm_set_attr = dwm
    manager._current_hwnd = None
    manager._current_window = None
    manager._mica_enabled = False
    return manager


@pytest.mark.parametrize("backdrop_result", [0, 1])
def test_positive_hresult_commits_window_state_and_signal(qapp, backdrop_result):
    del qapp
    dwm = _FakeDwmSetAttribute(
        results={mica_window.DWMWA_SYSTEMBACKDROP_TYPE: backdrop_result}
    )
    manager = _manager(dwm)
    window = _FakeWindow()
    signals = []
    manager.micaEnabledChanged.connect(signals.append)

    assert manager.setMicaEffect(window, True, True) is True
    assert [call[1:3] for call in dwm.calls] == [
        (mica_window.DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
        (mica_window.DWMWA_WINDOW_CORNER_PREFERENCE, mica_window.DWMWCP_ROUND),
        (mica_window.DWMWA_SYSTEMBACKDROP_TYPE, mica_window.DWM_BACKDROP_MICA),
    ]
    assert manager._current_window is window
    assert manager._current_hwnd == window.handle
    assert manager.micaEnabled is True
    assert signals == [True]


def test_negative_hresult_keeps_previous_state(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute(
        results={mica_window.DWMWA_SYSTEMBACKDROP_TYPE: -1}
    )
    manager = _manager(dwm)
    previous_window = object()
    manager._current_window = previous_window
    manager._current_hwnd = 77
    signals = []
    manager.micaEnabledChanged.connect(signals.append)

    assert manager.setMicaEffect(_FakeWindow(), True, False) is False
    assert manager._current_window is previous_window
    assert manager._current_hwnd == 77
    assert manager.micaEnabled is False
    assert signals == []


def test_unsupported_build_has_no_dwm_side_effects(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm, build=mica_window.WIN11_BACKDROP_BUILD_THRESHOLD - 1)

    assert manager.setMicaEffect(_FakeWindow(), True, False) is False
    assert dwm.calls == []
    assert manager._current_window is None
    assert manager._current_hwnd is None


def test_zero_hwnd_has_no_dwm_side_effects(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)

    assert manager.setMicaEffect(_FakeWindow(handle=0), True, False) is False
    assert dwm.calls == []
    assert manager._current_window is None
    assert manager._current_hwnd is None


@pytest.mark.parametrize(
    ("rounded", "preference"),
    [
        (True, mica_window.DWMWCP_ROUND),
        (False, mica_window.DWMWCP_DONOTROUND),
    ],
)
def test_set_window_corner_is_stateless(qapp, rounded, preference):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm, build=mica_window.WIN11_BUILD_THRESHOLD)
    previous_window = object()
    manager._current_window = previous_window
    manager._current_hwnd = 77

    assert manager.setWindowCorner(_FakeWindow(), rounded) is True

    assert [call[1:3] for call in dwm.calls] == [
        (mica_window.DWMWA_WINDOW_CORNER_PREFERENCE, preference),
    ]
    assert manager._current_window is previous_window
    assert manager._current_hwnd == 77
    assert manager.micaEnabled is False


def test_set_window_corner_rejects_failed_dwm_call_without_state_change(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute(
        results={mica_window.DWMWA_WINDOW_CORNER_PREFERENCE: -1}
    )
    manager = _manager(dwm, build=mica_window.WIN11_BUILD_THRESHOLD)

    assert manager.setWindowCorner(_FakeWindow(), True) is False
    assert manager._current_window is None
    assert manager._current_hwnd is None
    assert manager.micaEnabled is False


@pytest.mark.parametrize("error", [OSError("dwm"), KeyboardInterrupt(), SystemExit(9)])
def test_dark_mode_failure_preserves_state_and_control_flow(qapp, error):
    del qapp
    dwm = _FakeDwmSetAttribute(
        errors={mica_window.DWMWA_USE_IMMERSIVE_DARK_MODE: error}
    )
    manager = _manager(dwm)
    previous_window = object()
    manager._current_window = previous_window
    manager._current_hwnd = 88

    if isinstance(error, Exception):
        assert manager.setMicaEffect(_FakeWindow(), True, True) is False
    else:
        with pytest.raises(type(error)) as caught:
            manager.setMicaEffect(_FakeWindow(), True, True)
        assert caught.value is error
    assert manager._current_window is previous_window
    assert manager._current_hwnd == 88
    assert manager.micaEnabled is False
