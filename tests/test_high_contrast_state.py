# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""High-contrast detection and override. 高对比度探测与覆盖。

Qt exposes no contrast signal, so the platform is asked through
SystemParametersInfoW on Windows and the documented environment override wins
when set. 这些用例锁定该契约。
"""

import os
import sys

import pytest

from prismqml.python.core.theme import (
    HIGH_CONTRAST_ENV,
    ThemeManager,
    detect_high_contrast,
    read_high_contrast_env,
)


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", " yes ", "On"])
def test_truthy_overrides_enable_high_contrast(raw: str) -> None:
    assert read_high_contrast_env(raw) is True


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", " no ", "OFF"])
def test_falsy_overrides_disable_high_contrast(raw: str) -> None:
    assert read_high_contrast_env(raw) is False


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_missing_or_blank_override_defers_to_the_platform(raw) -> None:
    assert read_high_contrast_env(raw) is None


def test_invalid_override_is_ignored_instead_of_raising(caplog) -> None:
    """An unusable value warns and defers, never raises. 非法值告警并回退，不抛异常。"""
    with caplog.at_level("WARNING"):
        assert read_high_contrast_env("maybe") is None
    assert any(HIGH_CONTRAST_ENV in record.getMessage() for record in caplog.records)


def test_detection_returns_a_bool_on_every_platform() -> None:
    """The probe never guesses: non-Windows reports False. 非 Windows 返回 False。"""
    result = detect_high_contrast()
    assert isinstance(result, bool)
    if sys.platform != "win32":
        assert result is False


def test_detection_uses_the_real_windows_api() -> None:
    """On Windows the value must match the actual system setting. Windows 上与真实设置一致。"""
    if sys.platform != "win32":
        pytest.skip("Windows-only platform probe 仅 Windows 平台可用")
    import ctypes
    from ctypes import wintypes

    class _HighContrast(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("dwFlags", wintypes.DWORD),
            ("lpszDefaultScheme", wintypes.LPWSTR),
        ]

    info = _HighContrast()
    info.cbSize = ctypes.sizeof(_HighContrast)
    ctypes.windll.user32.SystemParametersInfoW(
        0x0042, info.cbSize, ctypes.byref(info), 0
    )
    assert detect_high_contrast() is bool(info.dwFlags & 0x00000001)


def test_manager_property_reacts_to_the_override(monkeypatch) -> None:
    """The manager property follows the override and notifies on change."""
    manager = ThemeManager()
    monkeypatch.setenv(HIGH_CONTRAST_ENV, "on")
    assert manager.refresh_high_contrast() is True
    assert manager.highContrast is True

    notifications: list[bool] = []
    manager.highContrastChanged.connect(notifications.append)
    # Re-reading the same value must not spam listeners.
    # 重读相同值不得重复通知监听者。
    assert manager.refresh_high_contrast() is True
    assert notifications == []

    monkeypatch.setenv(HIGH_CONTRAST_ENV, "off")
    assert manager.refresh_high_contrast() is False
    assert manager.highContrast is False
    assert notifications == [False]


def test_override_beats_the_platform_reading(monkeypatch) -> None:
    """An explicit override must win over the detected platform value."""
    manager = ThemeManager()
    monkeypatch.setattr(
        "prismqml.python.core.theme.detect_high_contrast", lambda: True
    )
    monkeypatch.setenv(HIGH_CONTRAST_ENV, "off")
    assert manager.refresh_high_contrast() is False
    monkeypatch.delenv(HIGH_CONTRAST_ENV, raising=False)
    assert manager.refresh_high_contrast() is True


def test_manager_exposes_the_property_to_qml() -> None:
    """The QML-facing property is registered on the meta object."""
    manager = ThemeManager()
    meta = manager.metaObject()
    index = meta.indexOfProperty("highContrast")
    assert index >= 0
    assert os.environ.get(HIGH_CONTRAST_ENV) is None or isinstance(
        manager.highContrast, bool
    )
