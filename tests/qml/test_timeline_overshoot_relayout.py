# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline visual overshoot relayout contracts. 时间线视觉越界重布局合同。"""

import pytest
from PySide6.QtCore import QMetaObject

from timeline_conventions_shared import (
    timeline_scene,
    _pump,
    _send_wheel,
    _virtual_viewport_and_helper,
    _wait_for,
)


def test_visual_overshoot_keeps_native_position_clamped_after_viewport_resize(
    timeline_scene,
):
    window, _timeline, timeline, warnings, _windows_before = timeline_scene
    viewport, helper = _virtual_viewport_and_helper(timeline)
    assert helper.property("_visualOvershootEnabled")
    assert QMetaObject.invokeMethod(helper, "scrollToEnd")
    assert _wait_for(
        lambda: viewport.property("contentY")
        == pytest.approx(helper.property("maxScroll"), abs=0.5)
    )
    _send_wheel(window, viewport, -120)
    assert _wait_for(lambda: helper.property("_visualOvershootOffset") < -1)
    assert helper.property("_isOutwardBounceV")

    positions = []
    viewport.contentYChanged.connect(
        lambda: positions.append((
            float(viewport.property("contentY")),
            float(helper.property("minScroll")),
            float(helper.property("maxScroll")),
        ))
    )
    timeline.setHeight(timeline.height() + 80)
    _pump(300)

    assert positions
    assert all(
        minimum - 0.5 <= position <= maximum + 0.5
        for position, minimum, maximum in positions
    ), positions
    assert warnings == []
