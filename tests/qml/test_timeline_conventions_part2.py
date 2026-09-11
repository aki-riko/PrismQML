# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 2/2 of the former test_timeline_conventions.py."""
import pytest  # noqa: F401
from timeline_conventions_shared import *
from timeline_conventions_shared import (
    _pump,
    _wait_for,
    _new_visible_windows,
    _visual_descendants,
    _named_visible_descendants,
    _send_wheel,
    _create_scene,
    _dispose_scene,
    _virtual_viewport_and_helper,
)

def test_timeline_selection_uses_render_thread_animators(timeline_scene):
    """Selection motion must survive GUI-thread result processing. 选中动效须独立于 GUI 线程。"""
    window, _timeline, _virtual_timeline, warnings, windows_before = timeline_scene
    graph_timeline = window.findChild(QQuickItem, "graphTimeline")
    assert graph_timeline is not None
    assert _wait_for(
        lambda: len(
            [
                item
                for item in _visual_descendants(graph_timeline)
                if item.objectName() == "timelineCardSelectionIndicator"
            ]
        )
        == 2
    )

    graph_timeline.setProperty("selectedKey", "feature")
    _pump(250)
    descendants = _visual_descendants(graph_timeline)
    card_indicators = [
        item
        for item in descendants
        if item.objectName() == "timelineCardSelectionIndicator"
    ]
    graph_rings = [
        item
        for item in descendants
        if item.objectName() == "timelineGraphSelectionRing"
    ]
    card_outlines = [
        item
        for item in descendants
        if item.objectName() == "timelineCardSelectionOutline"
    ]

    assert sorted(round(item.opacity(), 3) for item in card_indicators) == [0.0, 1.0]
    graph_ring_opacities = [round(item.opacity(), 3) for item in graph_rings]
    assert graph_ring_opacities.count(1.0) == 1
    assert all(opacity in (0.0, 1.0) for opacity in graph_ring_opacities)
    assert sorted(round(item.opacity(), 3) for item in card_outlines) == [0.0, 1.0]
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_timeline_selection_animation_does_not_change_geometry_on_gui_thread():
    timeline_source = SOURCE_PATH.read_text(encoding="utf-8")
    graph_source = GRAPH_SOURCE_PATH.read_text(encoding="utf-8")
    virtual_row_source = VIRTUAL_ROW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "Behavior on height" not in timeline_source
    assert "TimelineInternal.TimelineVirtualRow" in timeline_source
    assert "Status hairline" not in virtual_row_source
    assert "timelineGraphNodeHalo" not in graph_source
    assert "timelineGraphSelectionHalo" not in graph_source
    assert "paintColor: control.selected" in graph_source
    assert "SequentialAnimation on _pulsePhase" in timeline_source
    assert "NumberAnimation" in timeline_source
    assert "OpacityAnimator" in virtual_row_source
    assert "ScaleAnimator" in virtual_row_source
    assert "OpacityAnimator" in graph_source
    assert "ScaleAnimator" in graph_source

def test_timeline_core_source_follows_conventions():
    for source_path in (SOURCE_PATH, GRAPH_SOURCE_PATH, GRAPH_LABELS_SOURCE_PATH):
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source_path.read_text(encoding="utf-8"), path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
    ] == []

def test_timeline_time_and_date_fields_are_forwarded_without_formatting():
    timeline_source = SOURCE_PATH.read_text(encoding="utf-8")
    virtual_row_source = VIRTUAL_ROW_SOURCE_PATH.read_text(encoding="utf-8")

    assert '"dateKey": grp.dateKey || ""' in timeline_source
    assert '"time": cardObject ? card.time || "" : ""' in timeline_source
    assert '"timePeriod": cardObject ? card.timePeriod || "" : ""' in timeline_source
    assert "function _getTimeColor(period)" in timeline_source
    assert 'objectName: "timelineCardTimeBadge"' in virtual_row_source
    assert 'objectName: "timelineCardTimeLabel"' in virtual_row_source
