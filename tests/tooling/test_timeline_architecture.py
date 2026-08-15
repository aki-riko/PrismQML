# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline architecture gates. Timeline 架构门禁。"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TIMELINE_CORE = (
    REPO_ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "TimelineCore.qml"
)
VIRTUAL_ROW = TIMELINE_CORE.parent / "_internal" / "TimelineVirtualRow.qml"
STANDARD_CONTENT = TIMELINE_CORE.parent / "_internal" / "TimelineStandardContent.qml"


def test_virtual_timeline_row_is_an_internal_delegate():
    core_source = TIMELINE_CORE.read_text(encoding="utf-8")
    row_source = VIRTUAL_ROW.read_text(encoding="utf-8")

    assert 'import "_internal" as TimelineInternal' in core_source
    assert "delegate: TimelineInternal.TimelineVirtualRow {}" in core_source
    assert "TimelineInternal.TimelineStandardContent" in core_source
    assert "timeline: control" in core_source
    assert "property var timelineControl: control" in core_source
    assert "TimelineGraphLayer" not in core_source
    assert "TimelineGraphLabels" not in core_source
    assert "ListView.view.timelineControl" in row_source
    assert "required property var model" in row_source
    assert "required property var timeline" in STANDARD_CONTENT.read_text(
        encoding="utf-8"
    )


def test_timeline_modules_stay_within_architecture_limit():
    assert len(TIMELINE_CORE.read_text(encoding="utf-8").splitlines()) < 500
    assert len(VIRTUAL_ROW.read_text(encoding="utf-8").splitlines()) < 500
    assert len(STANDARD_CONTENT.read_text(encoding="utf-8").splitlines()) < 500
