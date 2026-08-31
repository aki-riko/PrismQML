# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window caption action host contract. 窗口标题栏通用动作宿主合同。"""

from types import SimpleNamespace

import pytest

from prismqml.python.window.window_core import WindowCore


def _owner():
    writes = []
    owner = SimpleNamespace(
        _caption_action_callback=None,
        _set_window_property=lambda key, value: writes.append((key, value)),
    )
    return owner, writes


def test_caption_action_configuration_stays_feature_neutral():
    owner, writes = _owner()

    WindowCore.set_caption_action(
        owner,
        "Bot",
        "Open assistant",
        enabled=False,
        visible=True,
    )

    assert owner._caption_action_icon == "Bot"
    assert owner._caption_action_tool_tip == "Open assistant"
    assert owner._caption_action_enabled is False
    assert owner._caption_action_visible is True
    assert writes == [
        ("captionActionVisible", True),
        ("captionActionIcon", "Bot"),
        ("captionActionToolTip", "Open assistant"),
        ("captionActionEnabled", False),
    ]


def test_caption_action_empty_icon_never_reserves_a_slot():
    owner, writes = _owner()

    WindowCore.set_caption_action(owner, "", "Unused", visible=True)

    assert owner._caption_action_visible is False
    assert writes[0] == ("captionActionVisible", False)


def test_caption_action_callback_is_owned_by_the_host():
    owner, _writes = _owner()
    events = []

    WindowCore.on_caption_action_triggered(owner, lambda: events.append("open"))
    WindowCore._on_caption_action_triggered(owner)

    assert events == ["open"]


@pytest.mark.parametrize(
    ("icon", "tool_tip"),
    ((object(), "valid"), ("Bot", object())),
)
def test_caption_action_rejects_non_string_display_data(icon, tool_tip):
    owner, _writes = _owner()

    with pytest.raises(TypeError):
        WindowCore.set_caption_action(owner, icon, tool_tip)


def test_caption_action_rejects_non_callable_callback():
    owner, _writes = _owner()

    with pytest.raises(TypeError, match="callable"):
        WindowCore.on_caption_action_triggered(owner, object())
