# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Native window follower contracts. 原生附属窗口跟随合同。"""

from types import SimpleNamespace

import pytest

from prismqml.python.core import window_helper


def _rect(left: int, top: int, right: int, bottom: int):
    return SimpleNamespace(left=left, top=top, right=right, bottom=bottom)


@pytest.mark.parametrize(
    ("edge", "expected"),
    [
        (window_helper.WINDOW_EDGE_LEFT, (-80, 120, 100, 520)),
        (window_helper.WINDOW_EDGE_RIGHT, (700, 120, 880, 520)),
        (window_helper.WINDOW_EDGE_TOP, (100, 0, 700, 120)),
        (window_helper.WINDOW_EDGE_BOTTOM, (100, 520, 700, 640)),
    ],
)
def test_follower_rect_uses_proposed_native_host_rect(edge, expected):
    actual = window_helper._follower_rect(
        _rect(100, 120, 700, 520),
        follower_width=180,
        follower_height=120,
        edge=edge,
    )

    assert actual == expected


@pytest.mark.parametrize(
    ("edge", "expected"),
    [
        (window_helper.WINDOW_EDGE_LEFT, (40, 120, 100, 520)),
        (window_helper.WINDOW_EDGE_RIGHT, (700, 120, 760, 520)),
        (window_helper.WINDOW_EDGE_TOP, (100, 60, 700, 120)),
        (window_helper.WINDOW_EDGE_BOTTOM, (100, 520, 700, 580)),
    ],
)
def test_follower_rect_for_extent_updates_one_complete_rect(edge, expected):
    actual = window_helper._follower_rect_for_extent(
        _rect(100, 120, 700, 520),
        extent=60,
        edge=edge,
    )

    assert actual == expected


def test_animation_frame_reads_host_once_and_submits_one_complete_rect():
    reads = []
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: reads.append(hwnd)
        or _rect(100, 120, 700, 520),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )

    assert event_filter.update_geometry(
        11,
        21,
        window_helper.WINDOW_EDGE_TOP,
        extent=60,
    )

    assert reads == [11]
    assert moves == [(21, (100, 60, 700, 120), 11)]
    assert event_filter.binding_count == 0


def test_filter_syncs_all_followers_for_the_moving_host():
    native_rects = {
        11: _rect(100, 120, 700, 520),
        21: _rect(-80, 120, 100, 520),
        22: _rect(700, 120, 880, 520),
        88: _rect(0, 0, 600, 400),
        99: _rect(0, 0, 50, 50),
    }
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )
    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_LEFT, 180)
    assert event_filter.register(11, 22, window_helper.WINDOW_EDGE_RIGHT, 180)
    assert event_filter.register(88, 99, window_helper.WINDOW_EDGE_BOTTOM, 120)
    moves.clear()

    event_filter.sync_host_rect(11, _rect(240, 260, 880, 680))

    assert moves == [
        (21, (60, 260, 240, 680), 11),
        (22, (880, 260, 1060, 680), 11),
    ]


def test_registration_immediately_aligns_to_native_host_rect():
    native_rects = {
        11: _rect(680, 296, 1880, 1096),
        21: _rect(1873, 266, 2153, 1103),
    }
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )

    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_RIGHT, 280)

    assert moves == [(21, (1880, 296, 2160, 1096), 11)]


def test_registration_resubmits_aligned_rect_to_refresh_z_order():
    native_rects = {
        11: _rect(680, 296, 1880, 1096),
        21: _rect(1880, 296, 2160, 1096),
    }
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )

    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_RIGHT, 280)

    assert moves == [(21, (1880, 296, 2160, 1096), 11)]
    assert event_filter.binding_count == 1


def test_reregister_updates_edge_and_unregister_cleans_binding():
    native_rects = {
        11: _rect(100, 120, 700, 520),
        21: _rect(700, 120, 880, 520),
    }
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )
    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_RIGHT, 180)
    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_BOTTOM, 120)
    moves.clear()

    event_filter.sync_host_rect(11, _rect(200, 300, 800, 700))
    assert moves == [(21, (200, 700, 800, 820), 11)]

    assert event_filter.unregister(21)
    event_filter.sync_host_rect(11, _rect(300, 400, 900, 800))
    assert moves == [(21, (200, 700, 800, 820), 11)]
    assert event_filter.unregister(21) is False


def test_registration_rejects_invalid_edge_and_missing_native_rect():
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda _hwnd: None,
        set_geometry=lambda _hwnd, _geometry, _after: True,
    )

    assert event_filter.register(11, 21, 99, 180) is False
    assert (
        event_filter.register(
            11, 21, window_helper.WINDOW_EDGE_LEFT, 180
        ) is False
    )


def test_set_window_pos_failure_does_not_drop_registration():
    native_rects = {
        11: _rect(100, 120, 700, 520),
        21: _rect(710, 120, 890, 520),
    }
    results = iter((True, False))
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda _hwnd, _geometry, _after: next(results),
    )
    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_RIGHT, 180)

    event_filter.sync_host_rect(11, _rect(240, 260, 840, 660))

    assert event_filter.binding_count == 1


def test_follower_raise_promotes_host_then_stays_behind_it():
    promotions = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda _hwnd: _rect(100, 120, 700, 520),
        set_geometry=lambda _hwnd, _geometry, _after: True,
        promote_window=lambda hwnd, after: promotions.append((hwnd, after)) or True,
    )
    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_RIGHT, 180)
    window_pos = SimpleNamespace(
        hwndInsertAfter=0,
        flags=0,
    )

    event_filter.enforce_follower_z_order(21, window_pos)

    assert promotions == [(11, 0)]
    assert window_pos.hwndInsertAfter == 11
    assert window_pos.flags & window_helper._SWP_NOZORDER == 0
    assert window_pos.flags & window_helper._SWP_NOOWNERZORDER


def test_internal_follower_placement_does_not_promote_host():
    promotions = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda _hwnd: _rect(100, 120, 700, 520),
        set_geometry=lambda _hwnd, _geometry, _after: True,
        promote_window=lambda hwnd, after: promotions.append((hwnd, after)) or True,
    )
    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_RIGHT, 180)
    window_pos = SimpleNamespace(hwndInsertAfter=11, flags=0)

    event_filter.enforce_follower_z_order(21, window_pos)

    assert promotions == []


class _FakeWindow:
    def __init__(self, hwnd: int) -> None:
        self._hwnd = hwnd

    def winId(self) -> int:
        return self._hwnd

    def devicePixelRatio(self) -> float:
        return 1.5


def test_window_helper_installs_one_filter_and_delegates_lifecycle(monkeypatch):
    calls = []

    class _FakeFilter:
        def update_geometry(self, host_hwnd, follower_hwnd, edge, extent):
            calls.append(("update", host_hwnd, follower_hwnd, edge, extent))
            return True

        def register(self, host_hwnd, follower_hwnd, edge, extent):
            calls.append(("register", host_hwnd, follower_hwnd, edge, extent))
            return True

        def unregister(self, follower_hwnd):
            calls.append(("unregister", follower_hwnd))
            return True

    class _FakeApplication:
        def installNativeEventFilter(self, event_filter):
            calls.append(("install", event_filter))

    fake_filter = _FakeFilter()
    monkeypatch.setattr(window_helper.sys, "platform", "win32")
    monkeypatch.setattr(
        window_helper.QGuiApplication,
        "instance",
        lambda: _FakeApplication(),
    )
    monkeypatch.setattr(
        window_helper,
        "_WindowFollowerFilter",
        lambda: fake_filter,
    )
    monkeypatch.setattr(window_helper.WindowHelper, "_instance", None)
    helper = window_helper.WindowHelper()

    assert helper.registerWindowFollower(
        _FakeWindow(11), _FakeWindow(21),
        window_helper.WINDOW_EDGE_RIGHT, 180,
    )
    assert helper.registerWindowFollower(
        _FakeWindow(11), _FakeWindow(22),
        window_helper.WINDOW_EDGE_LEFT, 180,
    )
    assert helper.updateWindowFollowerGeometry(
        _FakeWindow(11),
        _FakeWindow(22),
        window_helper.WINDOW_EDGE_TOP,
        60,
    )
    assert helper.unregisterWindowFollower(_FakeWindow(21))

    assert calls == [
        ("install", fake_filter),
        ("register", 11, 21, window_helper.WINDOW_EDGE_RIGHT, 270),
        ("register", 11, 22, window_helper.WINDOW_EDGE_LEFT, 270),
        ("update", 11, 22, window_helper.WINDOW_EDGE_TOP, 90),
        ("unregister", 21),
    ]
