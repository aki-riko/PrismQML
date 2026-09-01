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


def test_graph_labels_do_not_depend_on_sibling_visible_binding():
    """图标签绑定不得以兄弟 `visible` 的缓存值作守卫。

    `visible` 与 `labels` 是独立绑定, QML 不保证同批重算。行被回收且 cardData
    变为 undefined 时, 残留的 `visible === true` 会让 labels 解引用 undefined,
    产生 `TypeError: Value is undefined and could not be converted to an object`
    (真实日志: TimelineVirtualRow.qml:279, 同一毫秒六条)。
    """
    virtual_source = VIRTUAL_ROW.read_text(encoding="utf-8")

    # The self-guarding accessor must exist and both bindings must read it.
    # 自守访问器必须存在, 且两个绑定都必须读它。
    assert "readonly property var _rowLabels:" in virtual_source
    assert "labels: _rowLabels" in virtual_source
    assert "visible: control._graphMode && _rowLabels.length > 0" in virtual_source
    # The regressed form must not come back.
    # 回归形态不得复现。
    assert "labels: visible ?" not in virtual_source


def test_timeline_connectors_are_centered_on_status_nodes():
    standard_source = STANDARD_CONTENT.read_text(encoding="utf-8")
    virtual_source = VIRTUAL_ROW.read_text(encoding="utf-8")
    expected_binding = "x: (Enums.controlSize.timelineIcon - width) / 2"

    assert expected_binding in standard_source
    assert expected_binding in virtual_source
    assert "x: 7" not in standard_source
    assert "x: 7" not in virtual_source
