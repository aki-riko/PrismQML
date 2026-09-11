# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML architecture boundaries and size gates. QML 架构边界与大小门禁。"""

import re

from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text

ROOT = Path(__file__).resolve().parents[2]

QML_ROOT = ROOT / "prismqml" / "PrismQML"

OVERSIZED_QML_EXCEPTIONS = {
    "prismqml/PrismQML/PrismEnums/Metrics.qml",
}

def _source(relative_path: str) -> Path:
    return ROOT / relative_path

def _declaration_indent(source: str, declaration: str) -> int:
    """返回声明所在行的缩进宽度, 用于判断两个对象是否同级。

    Indentation width of the line declaring ``declaration``, so callers can tell
    a sibling from a nested child.
    """
    for line in source.splitlines():
        if line.strip() == declaration:
            return len(line) - len(line.lstrip())
    raise AssertionError(f"declaration not found: {declaration}")

def _assert_modularized(entry_path: str, helper_path: str, helper_type: str) -> None:
    entry = _source(entry_path)
    helper = _source(helper_path)

    assert entry.exists()
    assert helper.exists()
    assert len(entry.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert f"{helper_type} {{" in entry.read_text(encoding="utf-8")

_CHART_INTERNAL = QML_ROOT / "controls" / "data" / "Chart" / "_internal"

_CHART_MATH = _CHART_INTERNAL / "ChartMath.js"

_PICKER_INTERNAL = QML_ROOT / "controls" / "inputs" / "ColorPicker" / "_internal"

_PICKER_HSV = _PICKER_INTERNAL / "ColorPickerHsv.js"

_PICKER_DIALOG = _PICKER_INTERNAL / "ColorPickerDialog.qml"

_PICKER_DROPDOWN = _PICKER_INTERNAL / "ColorPickerDropdown.qml"
