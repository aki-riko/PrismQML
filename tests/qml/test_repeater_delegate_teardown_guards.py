# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Repeater delegate parent-teardown contracts. Repeater 委托父项销毁契约。"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_WIDGET = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "DataWidgetCore.qml"
)
DATE_TIME_PICKER = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Picker"
    / "DateTimePicker.qml"
)


def _section(path: Path, start: str, end: str) -> str:
    source = path.read_text(encoding="utf-8")
    return source.split(start, 1)[1].split(end, 1)[0]


def test_data_widget_skeleton_delegate_guards_parent_teardown():
    """A destroyed Column may clear a live Repeater delegate parent. 销毁列时委托父项可先置空。"""
    section = _section(DATA_WIDGET, "// Loading skeleton", "// Footer")

    assert "model: root.loading ? Math.min(" in section
    assert "width: parent ? parent.width : 0" in section
    assert "width: parent.width" not in section


def test_date_time_picker_display_delegate_guards_parent_teardown():
    """A destroyed Row may clear a live display delegate parent. 销毁行时显示委托父项可先置空。"""
    section = _section(
        DATE_TIME_PICKER,
        "// Display content",
        "// Interaction and initialization",
    )

    assert "width: parent ? parent.width / _totalColCount : 0" in section
    assert "height: parent ? parent.height : 0" in section
    assert "width: parent.width / _totalColCount" not in section
    assert "height: parent.height" not in section
