# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""System backdrop type contracts. 系统背板类型合同。

覆盖 DWM 背板类型映射（none/mica/acrylic/mica_alt）、新增 setBackdropType
入口，以及既有 micaEnabled 开关（setMicaEffect）行为零回归；QML 侧同时锁定
PrismEnums/Backdrop.qml 的新旧令牌取值。
"""

from __future__ import annotations

import ctypes
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.window import mica_window

ROOT = Path(__file__).resolve().parents[1]

BACKDROP_SCENE = """
import QtQuick
import PrismQML

Item {
    property int none: Enums.backdrop.none
    property int mica: Enums.backdrop.mica
    property int acrylic: Enums.backdrop.acrylic
    property int micaAlt: Enums.backdrop.mica_alt
    property int legacyNone: Enums.backdrop._dwm_none
    property int legacyMica: Enums.backdrop._dwm_mica
}
"""


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


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose(engine, component, instance) -> None:
    if instance is not None:
        instance.deleteLater()
    if component is not None:
        component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_backdrop_type_map_matches_dwm_enumeration():
    assert mica_window.BACKDROP_TYPE_VALUES == {
        "none": 1,
        "mica": 2,
        "acrylic": 3,
        "mica_alt": 4,
    }
    assert mica_window.DWM_BACKDROP_NONE == 1
    assert mica_window.DWM_BACKDROP_MICA == 2
    assert mica_window.DWM_BACKDROP_ACRYLIC == 3
    assert mica_window.DWM_BACKDROP_MICA_ALT == 4


@pytest.mark.parametrize(
    ("token", "expected"),
    [("none", 1), ("mica", 2), ("acrylic", 3), ("mica_alt", 4), (" MICA_ALT ", 4)],
)
def test_set_backdrop_type_applies_the_expected_dwm_value(qapp, token, expected):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)
    window = _FakeWindow()
    signals = []
    manager.micaEnabledChanged.connect(signals.append)

    assert manager.setBackdropType(window, token, True) is True

    assert [call[1:3] for call in dwm.calls] == [
        (mica_window.DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
        (mica_window.DWMWA_WINDOW_CORNER_PREFERENCE, mica_window.DWMWCP_ROUND),
        (
            mica_window.DWMWA_BORDER_COLOR,
            ctypes.c_int(mica_window.DWMWA_COLOR_NONE).value,
        ),
        (mica_window.DWMWA_SYSTEMBACKDROP_TYPE, expected),
    ]
    assert manager._current_window is window
    assert manager._current_hwnd == window.handle
    assert manager.micaEnabled is (expected != 1)
    # "none" matches the initial disabled state, so no logical transition is emitted.
    # "none" 与初始禁用状态一致，因此不产生逻辑变化通知。
    assert signals == ([True] if expected != 1 else [])


def test_set_backdrop_type_rejects_unknown_token_without_dwm_calls(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)

    assert manager.setBackdropType(_FakeWindow(), "blur", True) is False
    assert dwm.calls == []
    assert manager._current_window is None
    assert manager._current_hwnd is None
    assert manager.micaEnabled is False


def test_set_backdrop_type_rejects_unsupported_build(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm, build=mica_window.WIN11_BACKDROP_BUILD_THRESHOLD - 1)

    assert manager.setBackdropType(_FakeWindow(), "acrylic", False) is False
    assert dwm.calls == []


def test_set_backdrop_type_rejects_empty_hwnd(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)

    assert manager.setBackdropType(_FakeWindow(handle=0), "mica", False) is False
    assert dwm.calls == []


def test_existing_mica_toggle_behavior_is_unchanged(qapp):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)
    window = _FakeWindow()
    signals = []
    manager.micaEnabledChanged.connect(signals.append)

    assert manager.setMicaEffect(window, True, True) is True
    assert [call[1:3] for call in dwm.calls] == [
        (mica_window.DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
        (mica_window.DWMWA_WINDOW_CORNER_PREFERENCE, mica_window.DWMWCP_ROUND),
        (
            mica_window.DWMWA_BORDER_COLOR,
            ctypes.c_int(mica_window.DWMWA_COLOR_NONE).value,
        ),
        (mica_window.DWMWA_SYSTEMBACKDROP_TYPE, mica_window.DWM_BACKDROP_MICA),
    ]
    assert manager.micaEnabled is True

    dwm.calls.clear()
    assert manager.setMicaEffect(window, False, False) is True
    assert [call[1:3] for call in dwm.calls] == [
        (mica_window.DWMWA_USE_IMMERSIVE_DARK_MODE, 0),
        (mica_window.DWMWA_WINDOW_CORNER_PREFERENCE, mica_window.DWMWCP_ROUND),
        (
            mica_window.DWMWA_BORDER_COLOR,
            ctypes.c_int(mica_window.DWMWA_COLOR_NONE).value,
        ),
        (mica_window.DWMWA_SYSTEMBACKDROP_TYPE, mica_window.DWM_BACKDROP_NONE),
    ]
    assert manager.micaEnabled is False
    assert signals == [True, False]


def test_existing_transition_logging_is_unchanged(qapp, monkeypatch):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)
    window = _FakeWindow()
    info_messages = []
    debug_messages = []
    monkeypatch.setattr(mica_window, "info", info_messages.append)
    monkeypatch.setattr(mica_window, "debug", debug_messages.append)

    manager.setMicaEffect(window, True, False)
    manager.setMicaEffect(window, True, False)

    assert info_messages == ["Mica effect enabled"]
    assert debug_messages == ["Mica effect enabled reapplied (hwnd=4660)"]


def test_backdrop_type_logging_names_the_token(qapp, monkeypatch):
    del qapp
    dwm = _FakeDwmSetAttribute()
    manager = _manager(dwm)
    info_messages = []
    monkeypatch.setattr(mica_window, "info", info_messages.append)

    assert manager.setBackdropType(_FakeWindow(), "acrylic", False) is True
    assert info_messages == ["System backdrop 'acrylic' enabled"]


def test_backdrop_tokens_are_exposed_to_qml(qapp):
    del qapp
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        component = QQmlComponent(engine)
        component.setData(
            BACKDROP_SCENE.encode("utf-8"), QUrl("inline:w5-backdrop-tokens.qml")
        )
        for _ in range(50):
            if component.status() != QQmlComponent.Status.Loading:
                break
            _pump(20)
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        instance = component.create(engine.rootContext())
        assert instance is not None, [error.toString() for error in component.errors()]

        assert instance.property("none") == 1
        assert instance.property("mica") == 2
        assert instance.property("acrylic") == 3
        assert instance.property("micaAlt") == 4
        assert instance.property("legacyNone") == 1
        assert instance.property("legacyMica") == 2
    finally:
        _dispose(engine, component, instance)
