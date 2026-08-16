# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window attachment geometry contracts. 窗口附着几何合同。"""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QRect

from prismqml.python.core import window_helper
from prismqml.python.core import _window_follower as follower


def _rect(left: int, top: int, right: int, bottom: int):
    return SimpleNamespace(left=left, top=top, right=right, bottom=bottom)


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        (follower._ATTACHMENT_POS_TOP_LEFT, (-28, 200, 92, 260)),
        (follower._ATTACHMENT_POS_TOP, (440, 132, 560, 192)),
        (follower._ATTACHMENT_POS_TOP_RIGHT, (908, 200, 1028, 260)),
        (follower._ATTACHMENT_POS_LEFT, (-28, 470, 92, 530)),
        (follower._ATTACHMENT_POS_RIGHT, (908, 470, 1028, 530)),
        (follower._ATTACHMENT_POS_BOTTOM_LEFT, (-28, 740, 92, 800)),
        (follower._ATTACHMENT_POS_BOTTOM, (440, 808, 560, 868)),
        (follower._ATTACHMENT_POS_BOTTOM_RIGHT, (908, 740, 1028, 800)),
    ],
)
def test_attachment_geometry_maps_each_edge_position(position, expected):
    """Eight outside positions map to their host edge and stack axis."""
    assert window_helper._attached_window_rect(
        _rect(100, 200, 900, 800),
        follower_width=120,
        follower_height=60,
        position=position,
        reserved_extent=0,
        gap=8,
        stack_offset=0,
    ) == expected


def test_attachment_respects_drawer_reservation_and_syncs_on_host_move():
    """Drawer reservation shifts an attachment without changing its size."""
    native_rects = {11: _rect(100, 200, 900, 800)}
    moves = []
    event_filter = window_helper._WindowFollowerFilter(
        read_rect=lambda hwnd: native_rects.get(hwnd),
        set_geometry=lambda hwnd, geometry, after: moves.append(
            (hwnd, geometry, after)
        ) or True,
    )

    assert event_filter.register(11, 22, window_helper.WINDOW_EDGE_LEFT, 200)
    moves.clear()
    assert event_filter.register_attachment(
        11, 33, follower._ATTACHMENT_POS_TOP_LEFT,
        width=120, height=60, gap=8, stack_offset=0,
    )
    assert moves == [(33, (-228, 200, -108, 260), 11)]

    moves.clear()
    event_filter.sync_host_rect(11, _rect(300, 400, 1100, 1000))
    assert moves == [
        (22, (100, 400, 300, 1000), 11),
        (33, (-28, 400, 92, 460), 11),
    ]

    assert event_filter.unregister_attachment(33)
    assert not event_filter.unregister_attachment(33)
    assert event_filter.binding_count == 1


class _FakeWindow:
    def __init__(self, hwnd: int, geometry):
        self._hwnd = hwnd
        self._geometry = geometry
        self.geometry_calls = []

    def winId(self) -> int:
        return self._hwnd

    def devicePixelRatio(self) -> float:
        return 1.0

    def frameGeometry(self):
        return self._geometry

    def setGeometry(self, geometry):
        self.geometry_calls.append(geometry)


def test_qt_fallback_uses_drawer_reservation_for_attachment(qapp, monkeypatch):
    """Non-Windows fallback keeps Drawer reservation semantics."""
    monkeypatch.setattr(window_helper.sys, "platform", "linux")
    monkeypatch.setattr(window_helper.WindowHelper, "_instance", None)
    helper = window_helper.WindowHelper()
    host = _FakeWindow(11, QRect(100, 200, 800, 600))
    drawer = _FakeWindow(22, QRect(0, 0, 1, 1))
    attached = _FakeWindow(33, QRect(0, 0, 1, 1))

    assert helper.registerWindowFollower(
        host, drawer, window_helper.WINDOW_EDGE_LEFT, 200
    )
    geometry = helper.windowAttachmentGeometry(
        host,
        follower._ATTACHMENT_POS_TOP_LEFT,
        120,
        60,
        8,
        0,
    )
    assert geometry == {"x": -228, "y": 200, "width": 120, "height": 60}
    assert helper.registerWindowAttachment(
        host, attached, follower._ATTACHMENT_POS_TOP_LEFT,
        120, 60, 8, 0,
    )
    assert attached.geometry_calls[-1].getRect() == (-228, 200, 120, 60)
    assert helper.unregisterWindowAttachment(attached) is False
    assert helper.unregisterWindowFollower(drawer)
