# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DWM shadow WinAPI contracts. DWM 阴影 WinAPI 合同。"""

import ctypes
import sys
from ctypes import wintypes
from types import SimpleNamespace

import pytest

import prismqml.python.core.shadow as shadow


pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="DWM contracts require Windows"
)


class _WideHwnd(int):
    """Pointer-width HWND sentinel. 指针宽度 HWND 哨兵。"""


def _hwnd_value(value):
    return 0 if value is None else int(value)


def _raw_win_function(callback):
    class RawWinFunction(ctypes._CFuncPtr):
        _flags_ = ctypes._FUNCFLAG_STDCALL
        _restype_ = ctypes.c_long

    address = ctypes.cast(callback, ctypes.c_void_p).value
    return RawWinFunction(address)


def _make_set_callback(events, result):
    callback_type = ctypes.WINFUNCTYPE(
        ctypes.HRESULT,
        wintypes.HWND,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
    )

    @callback_type
    def set_attribute(hwnd, attribute, value_pointer, value_size):
        policy = ctypes.cast(value_pointer, ctypes.POINTER(ctypes.c_int)).contents
        events.append(("set", _hwnd_value(hwnd), attribute, policy.value, value_size))
        return result

    return set_attribute


def _make_extend_callback(events, result):
    callback_type = ctypes.WINFUNCTYPE(
        ctypes.HRESULT,
        wintypes.HWND,
        ctypes.POINTER(shadow.MARGINS),
    )

    @callback_type
    def extend_frame(hwnd, margins_pointer):
        margins = margins_pointer.contents
        values = (
            margins.cxLeftWidth,
            margins.cxRightWidth,
            margins.cyTopHeight,
            margins.cyBottomHeight,
        )
        events.append(("extend", _hwnd_value(hwnd), values))
        return result

    return extend_frame


def _make_position_callback(events, result):
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    )

    @callback_type
    def set_window_pos(hwnd, insert_after, x, y, width, height, flags):
        events.append(
            (
                "position",
                _hwnd_value(hwnd),
                _hwnd_value(insert_after),
                x,
                y,
                width,
                height,
                flags,
            )
        )
        return result

    return set_window_pos


def _install_native_callbacks(
    monkeypatch, set_result=0, frame_result=0, position_result=1
):
    events = []
    set_callback = _make_set_callback(events, set_result)
    extend_callback = _make_extend_callback(events, frame_result)
    position_callback = _make_position_callback(events, position_result)
    set_attribute = _raw_win_function(set_callback)
    extend_frame = _raw_win_function(extend_callback)
    set_window_pos = _raw_win_function(position_callback)

    for function in (set_attribute, extend_frame, set_window_pos):
        assert function.argtypes is None
        assert function.restype is ctypes.c_long

    dwmapi = SimpleNamespace(
        DwmSetWindowAttribute=set_attribute,
        DwmExtendFrameIntoClientArea=extend_frame,
        _callbacks=(set_callback, extend_callback),
    )
    user32 = SimpleNamespace(
        SetWindowPos=set_window_pos,
        _callbacks=(position_callback,),
    )
    monkeypatch.setattr(
        shadow.ctypes,
        "windll",
        SimpleNamespace(dwmapi=dwmapi, user32=user32),
    )
    return events, dwmapi, user32


def _inject_native_error(dwmapi, user32, stage, error):
    functions = {
        "set": dwmapi.DwmSetWindowAttribute,
        "extend": dwmapi.DwmExtendFrameIntoClientArea,
        "position": user32.SetWindowPos,
    }

    def raise_error(_result, _function, _arguments):
        raise error

    functions[stage].errcheck = raise_error


def _assert_configured_signatures(dwmapi, user32, includes_position):
    assert dwmapi.DwmExtendFrameIntoClientArea.argtypes == [
        wintypes.HWND,
        ctypes.POINTER(shadow.MARGINS),
    ]
    assert dwmapi.DwmExtendFrameIntoClientArea.restype is ctypes.HRESULT
    if not includes_position:
        return
    assert user32.SetWindowPos.argtypes == [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    assert user32.SetWindowPos.restype is wintypes.BOOL


@pytest.mark.parametrize(
    ("method_name", "policy", "margin", "event_names"),
    (
        ("_enableDwmShadow", 2, 1, ["set", "extend", "position"]),
        ("_disableDwmShadow", 0, 0, ["set", "extend"]),
    ),
)
def test_dwm_shadow_configures_pointer_width_attribute_call(
    monkeypatch, method_name, policy, margin, event_names
):
    events, dwmapi, user32 = _install_native_callbacks(monkeypatch)
    manager = shadow.ShadowManager()
    hwnd = _WideHwnd(0x1_0000_0001)

    assert getattr(manager, method_name)(hwnd) is True

    assert [event[0] for event in events] == event_names
    assert events[0][1] == hwnd
    assert events[0][2:] == (2, policy, ctypes.sizeof(ctypes.c_int()))
    assert events[1][1] == hwnd
    assert events[1][2] == (margin, margin, margin, margin)
    if method_name == "_enableDwmShadow":
        assert events[2] == ("position", hwnd, 0, 0, 0, 0, 0, 0x27)
    _assert_configured_signatures(
        dwmapi, user32, includes_position=method_name == "_enableDwmShadow"
    )


@pytest.mark.parametrize(
    ("method_name", "set_result", "frame_result", "expected", "event_names"),
    (
        ("_enableDwmShadow", -1, 0, False, ["set"]),
        ("_enableDwmShadow", 0, -1, False, ["set", "extend"]),
        ("_enableDwmShadow", 1, 1, True, ["set", "extend", "position"]),
        ("_enableDwmShadow", 0, 0, True, ["set", "extend", "position"]),
        ("_disableDwmShadow", -1, 0, False, ["set"]),
        ("_disableDwmShadow", 0, -1, False, ["set", "extend"]),
        ("_disableDwmShadow", 1, 1, True, ["set", "extend"]),
        ("_disableDwmShadow", 0, 0, True, ["set", "extend"]),
    ),
)
def test_dwm_shadow_uses_hresult_success_contract(
    monkeypatch, method_name, set_result, frame_result, expected, event_names
):
    events, _dwmapi, _user32 = _install_native_callbacks(
        monkeypatch, set_result=set_result, frame_result=frame_result
    )
    manager = shadow.ShadowManager()

    assert getattr(manager, method_name)(0x1234) is expected
    assert [event[0] for event in events] == event_names


@pytest.mark.parametrize(
    ("method_name", "stage", "event_names"),
    (
        ("enableShadow", "set", ["set"]),
        ("enableShadow", "extend", ["set", "extend"]),
        ("enableShadow", "position", ["set", "extend", "position"]),
        ("disableShadow", "set", ["set"]),
        ("disableShadow", "extend", ["set", "extend"]),
    ),
)
def test_dwm_public_methods_return_false_on_native_exception(
    monkeypatch, method_name, stage, event_names
):
    events, dwmapi, user32 = _install_native_callbacks(monkeypatch)
    _inject_native_error(dwmapi, user32, stage, RuntimeError(f"{stage} failed"))
    manager = shadow.ShadowManager()

    assert getattr(manager, method_name)(0x1234) is False
    assert [event[0] for event in events] == event_names


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize(
    ("method_name", "stage", "event_names"),
    (
        ("enableShadow", "set", ["set"]),
        ("enableShadow", "extend", ["set", "extend"]),
        ("enableShadow", "position", ["set", "extend", "position"]),
        ("disableShadow", "set", ["set"]),
        ("disableShadow", "extend", ["set", "extend"]),
    ),
)
def test_dwm_public_methods_preserve_process_control_exception(
    monkeypatch, method_name, stage, event_names, error_type
):
    events, dwmapi, user32 = _install_native_callbacks(monkeypatch)
    injected = error_type(f"{stage} interrupted")
    _inject_native_error(dwmapi, user32, stage, injected)
    manager = shadow.ShadowManager()

    with pytest.raises(error_type) as caught:
        getattr(manager, method_name)(0x1234)

    assert caught.value is injected
    assert [event[0] for event in events] == event_names


def test_dwm_shadow_rejects_null_native_handle():
    manager = shadow.ShadowManager()

    assert manager._enableDwmShadow(0) is False
    assert manager._disableDwmShadow(0) is False
