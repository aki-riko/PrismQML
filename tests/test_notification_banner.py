# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Notification banner guard contracts. 通知横幅避让守卫合同。

覆盖边缘判定、纯函数钳制、跨平台降级、守卫单例与引用计数生命周期。
不依赖真实系统通知，避免在通知横幅出现时产生不稳定断言。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from prismqml.python.core import _notification_banner as banner
from prismqml.python.core import notification_banner_guard as guard_module
from prismqml.python.core.notification_banner_guard import (
    NotificationBannerGuard,
    get_notification_banner_guard,
)

ROOT = Path(__file__).resolve().parents[1]

# Work area of the 4K reference display the measurements below come from.
# 下方测量数据所在 4K 参考显示器的工作区。
WORK = (0, 0, 3840, 2088)

# Measured banner geometry: window rect bottom-right anchored on WORK.
# 实测横幅几何：贴靠 WORK 右下角的窗口矩形。
BOTTOM_RIGHT_RECT = (3246, 1860, 3840, 2088)


def test_banner_band_constant_is_immersive_notification():
    assert banner.ZBID_IMMERSIVE_NOTIFICATION == 4


def test_edge_constants_are_distinct():
    assert banner.EDGE_TOP != banner.EDGE_BOTTOM


def test_bottom_right_banner_is_classified_as_bottom():
    edge, height = banner.banner_edge_and_height(BOTTOM_RIGHT_RECT, WORK)
    assert edge == banner.EDGE_BOTTOM
    assert height == 228


def test_bottom_left_banner_is_classified_as_bottom():
    edge, height = banner.banner_edge_and_height((0, 1860, 594, 2088), WORK)
    assert edge == banner.EDGE_BOTTOM
    assert height == 228


def test_top_right_banner_is_classified_as_top():
    edge, height = banner.banner_edge_and_height((3246, 0, 3840, 228), WORK)
    assert edge == banner.EDGE_TOP
    assert height == 228


def test_top_left_banner_is_classified_as_top():
    edge, height = banner.banner_edge_and_height((0, 0, 594, 228), WORK)
    assert edge == banner.EDGE_TOP
    assert height == 228


def test_edge_ties_resolve_to_bottom():
    edge, height = banner.banner_edge_and_height((0, 0, 100, 100), (0, 0, 100, 100))
    assert edge == banner.EDGE_BOTTOM
    assert height == 100


def test_clamp_reservation_rejects_non_positive_inputs():
    assert banner.clamp_reservation(0, 1000) == 0
    assert banner.clamp_reservation(-10, 1000) == 0
    assert banner.clamp_reservation(200, 0) == 0
    assert banner.clamp_reservation(200, -5) == 0


def test_clamp_reservation_keeps_reservation_below_the_ratio():
    assert banner.clamp_reservation(228, 2088) == 228


def test_clamp_reservation_caps_reservation_above_the_ratio():
    assert banner.clamp_reservation(900, 1000) == int(1000 * banner.MAX_RESERVATION_RATIO)
    assert banner.clamp_reservation(1000, 1000) < 1000


def test_banner_probe_degrades_without_win32_api(monkeypatch):
    monkeypatch.setattr(banner, "_api", lambda: None)
    assert banner.notification_banner_reservations() == (0, 0)
    assert banner.notification_banner_handles() == []


def test_module_imports_without_ctypes_winfunctype():
    """Import must not require ctypes.WINFUNCTYPE, which exists only on Windows.

    ctypes.WINFUNCTYPE 仅存在于 Windows；在 Linux 上导入本模块不得依赖它，
    否则 runtime 导入链会在非 Windows 平台直接失败。
    """
    script = (
        "import ctypes, sys\n"
        "del ctypes.WINFUNCTYPE\n"
        "sys.platform = 'linux'\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "import prismqml.python.core._notification_banner as module\n"
        "assert module._MONITOR_ENUMPROC is None\n"
        "assert module.notification_banner_reservations() == (0, 0)\n"
        "assert module.notification_banner_handles() == []\n"
        "assert module.clamp_reservation(228, 2088) == 228\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr[-2000:]


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


def test_last_release_clears_reservations(qapp):
    guard = get_notification_banner_guard()
    baseline = guard.watcherCount
    guard.acquire()
    guard.release()
    assert guard.watcherCount == baseline
    if baseline == 0:
        assert guard.topReservedHeight == 0
        assert guard.bottomReservedHeight == 0


def test_guard_survives_a_failing_probe(qapp, monkeypatch):
    guard = get_notification_banner_guard()

    def _explode():
        raise OSError("simulated probe failure")

    monkeypatch.setattr(guard_module, "notification_banner_reservations", _explode)
    guard.acquire()
    assert guard.watcherCount >= 1
    guard.release()
    assert guard.topReservedHeight >= 0
    assert guard.bottomReservedHeight >= 0


def test_guard_publishes_both_reservations(qapp, monkeypatch):
    guard = get_notification_banner_guard()
    monkeypatch.setattr(
        guard_module, "notification_banner_reservations", lambda: (120, 228)
    )
    guard.acquire()
    try:
        assert guard.topReservedHeight == 120
        assert guard.bottomReservedHeight == 228
    finally:
        guard.release()
