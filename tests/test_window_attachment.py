# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window attachment geometry contracts. 窗口附着几何合同。"""

from types import SimpleNamespace

import pytest

from prismqml.python.core import window_helper
from prismqml.python.core import _window_follower as follower


def _rect(left: int, top: int, right: int, bottom: int):
    return SimpleNamespace(left=left, top=top, right=right, bottom=bottom)


@pytest.mark.parametrize(
    ("position", "reserved", "expected"),
    [
        (
            follower._ATTACHMENT_POS_RIGHT,
            140,
            (845, 290, 945, 370),
        ),
        (
            follower._ATTACHMENT_POS_TOP,
            0,
            (350, 25, 450, 105),
        ),
        (
            follower._ATTACHMENT_POS_BOTTOM_LEFT,
            60,
            (-65, 430, 35, 510),
        ),
    ],
)
def test_attached_window_rect_respects_edge_reservation_and_anchor(
    position, reserved, expected
):
    assert window_helper._attached_window_rect(
        _rect(100, 120, 700, 520),
        follower_width=100,
        follower_height=80,
        position=position,
        reserved_extent=reserved,
        gap=5,
        stack_offset=10,
    ) == expected


def test_attachment_reservation_is_scoped_to_drawer_edge_and_follows_host():
    native_rects = {11: _rect(100, 120, 700, 520)}
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )

    assert event_filter.register(11, 21, window_helper.WINDOW_EDGE_LEFT, 140)
    assert event_filter.register_attachment(
        11,
        31,
        follower._ATTACHMENT_POS_LEFT,
        100,
        80,
        5,
        10,
    )
    assert event_filter.register_attachment(
        11,
        32,
        follower._ATTACHMENT_POS_RIGHT,
        100,
        80,
        5,
        10,
    )
    assert event_filter.binding_count == 3
    assert moves[-2:] == [
        (31, (-145, 290, -45, 370), 11),
        (32, (705, 290, 805, 370), 11),
    ]

    moves.clear()
    event_filter.sync_host_rect(11, _rect(240, 260, 840, 660))
    assert moves == [
        (21, (100, 260, 240, 660), 11),
        (31, (-5, 430, 95, 510), 11),
        (32, (845, 430, 945, 510), 11),
    ]
    assert event_filter.unregister_attachment(31)
    assert event_filter.binding_count == 2
    assert not event_filter.unregister_attachment(31)


class _FallbackWindow:
    def __init__(self, hwnd: int, geometry) -> None:
        self._hwnd = hwnd
        self._geometry = geometry
        self.set_geometries = []

    def winId(self) -> int:
        return self._hwnd

    def frameGeometry(self):
        return self._geometry

    def devicePixelRatio(self) -> float:
        return 1.0

    def setGeometry(self, geometry) -> None:
        self.set_geometries.append(
            (geometry.x(), geometry.y(), geometry.width(), geometry.height())
        )


class _QtGeometry:
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
        self._left = left
        self._top = top
        self._right = right
        self._bottom = bottom

    def left(self) -> int:
        return self._left

    def top(self) -> int:
        return self._top

    def right(self) -> int:
        return self._right

    def bottom(self) -> int:
        return self._bottom


def test_window_helper_fallback_applies_exact_attachment_geometry(monkeypatch):
    monkeypatch.setattr(window_helper.sys, "platform", "linux")
    monkeypatch.setattr(window_helper.WindowHelper, "_instance", None)
    helper = window_helper.WindowHelper()
    host = _FallbackWindow(11, _QtGeometry(100, 120, 700, 520))
    attached = _FallbackWindow(31, _QtGeometry(0, 0, 1, 1))

    assert helper.registerWindowAttachment(
        host,
        attached,
        follower._ATTACHMENT_POS_RIGHT,
        100,
        80,
        5,
        10,
    )
    assert attached.set_geometries == [(706, 290, 100, 80)]
    assert helper.windowAttachmentGeometry(
        host,
        follower._ATTACHMENT_POS_RIGHT,
        100,
        80,
        5,
        10,
    ) == {"x": 706, "y": 290, "width": 100, "height": 80}
