# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Notification banner guard contracts. 通知横幅避让守卫合同。

覆盖纯函数钳制、跨平台降级、守卫单例与引用计数生命周期。
不依赖真实系统通知，避免在通知横幅出现时产生不稳定断言。
"""

from __future__ import annotations

from prismqml.python.core import _notification_banner as banner
from prismqml.python.core import notification_banner_guard as guard_module
from prismqml.python.core.notification_banner_guard import (
    NotificationBannerGuard,
    get_notification_banner_guard,
)


def test_banner_band_constant_is_immersive_notification():
    assert banner.ZBID_IMMERSIVE_NOTIFICATION == 4


def test_clamp_reservation_rejects_non_positive_inputs():
    assert banner.clamp_reservation(0, 1000) == 0
    assert banner.clamp_reservation(-10, 1000) == 0
    assert banner.clamp_reservation(200, 0) == 0
    assert banner.clamp_reservation(200, -5) == 0


def test_clamp_reservation_keeps_reservation_below_the_ratio():
    # Measured single banner height against the work area height on a 4K display.
    # 4K 显示器上实测的单条横幅高度与工作区高度。
    assert banner.clamp_reservation(228, 2088) == 228


def test_clamp_reservation_caps_reservation_above_the_ratio():
    assert banner.clamp_reservation(900, 1000) == int(1000 * banner.MAX_RESERVATION_RATIO)
    assert banner.clamp_reservation(1000, 1000) < 1000


def test_banner_probe_degrades_without_win32_api(monkeypatch):
    monkeypatch.setattr(banner, "_api", lambda: None)
    assert banner.notification_banner_reservation() == 0
    assert banner.notification_banner_handles() == []


def test_guard_is_a_process_singleton(qapp):
    assert get_notification_banner_guard() is get_notification_banner_guard()
    assert NotificationBannerGuard() is get_notification_banner_guard()


def test_guard_reference_counting_is_balanced(qapp):
    guard = get_notification_banner_guard()
    baseline = guard.watcherCount
    try:
        guard.acquire()
        assert guard.watcherCount == baseline + 1
        guard.acquire()
        assert guard.watcherCount == baseline + 2
    finally:
        guard.release()
        guard.release()
    assert guard.watcherCount == baseline


def test_release_without_acquire_never_goes_negative(qapp):
    guard = get_notification_banner_guard()
    baseline = guard.watcherCount
    guard.release()
    guard.release()
    assert guard.watcherCount == max(0, baseline - 2)
    assert guard.watcherCount >= 0


def test_last_release_clears_reserved_height(qapp):
    guard = get_notification_banner_guard()
    baseline = guard.watcherCount
    guard.acquire()
    guard.release()
    assert guard.watcherCount == baseline
    if baseline == 0:
        assert guard.reservedHeight == 0


def test_guard_survives_a_failing_probe(qapp, monkeypatch):
    guard = get_notification_banner_guard()

    def _explode():
        raise OSError("simulated probe failure")

    monkeypatch.setattr(guard_module, "notification_banner_reservation", _explode)
    guard.acquire()
    assert guard.watcherCount >= 1
    guard.release()
    assert guard.reservedHeight >= 0


def test_guard_publishes_probe_result(qapp, monkeypatch):
    guard = get_notification_banner_guard()
    monkeypatch.setattr(guard_module, "notification_banner_reservation", lambda: 228)
    guard.acquire()
    try:
        assert guard.reservedHeight == 228
    finally:
        guard.release()
