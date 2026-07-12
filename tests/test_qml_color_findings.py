# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Position-level color scanner regressions. 颜色扫描位置级回归。"""

from pathlib import Path

from scripts.qml_color_arrays import (
    color_array_literal_findings,
    color_array_literal_lines,
)
from scripts.qml_color_constructors import (
    numeric_color_constructor_findings,
    numeric_color_constructor_lines,
)
from scripts.qml_color_context_findings import color_literal_findings
from scripts.qml_color_contexts import color_literal_lines
from scripts.qml_lexer import sanitize_qml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "prismqml" / "PrismQML", ROOT / "examples")


def _views(source: str) -> tuple[list[str], list[str], str, str, str]:
    code = sanitize_qml(source, mask_strings=True)
    array_code = sanitize_qml(source, mask_strings=True, mark_values=True)
    quoted = sanitize_qml(source, mask_strings=False)
    return (
        code.splitlines(),
        quoted.splitlines(),
        code,
        array_code,
        quoted,
    )


def _normalized(source: str) -> str:
    return "\n".join(source.splitlines())


def _finding_values(source: str, findings) -> list[str]:
    normalized = _normalized(source)
    return [normalized[item.start:item.end] for item in findings]


def test_color_context_findings_preserve_each_literal_position():
    source = """Item {
    color: active ? "red" : "blue"
    property color blockColor: { if (active) return "white"; return "black" }
    function paint(ctx) { ctx.fillStyle = "cyan"; gradient.addColorStop(0, "gold") }
}
"""
    code_lines, source_lines, _, _, _ = _views(source)

    findings = color_literal_findings(code_lines, source_lines)

    assert [item.line for item in findings] == [2, 2, 3, 3, 4, 4]
    assert _finding_values(source, findings) == [
        '"red"', '"blue"', '"white"', '"black"', '"cyan"', '"gold"'
    ]
    assert color_literal_lines(code_lines, source_lines) == {2, 3, 4}


def test_array_findings_preserve_multiple_literals_on_one_line():
    source = """Item {
    property var fallbackColors: ["red", active ? "blue" : "gold"]
}
"""
    _, _, _, array_code, quoted = _views(source)

    findings = color_array_literal_findings(array_code, quoted)

    assert [item.line for item in findings] == [2, 2, 2]
    assert _finding_values(source, findings) == ['"red"', '"blue"', '"gold"']
    assert color_array_literal_lines(array_code, quoted) == {2}


def test_numeric_findings_cover_each_constructor_call_span():
    source = """Item {
    color: Qt.rgba(1, 0, 0, 1); border.color: (Qt).hsla(0, 1, 0.5, 1)
}
"""
    _, _, code, _, quoted = _views(source)

    findings = numeric_color_constructor_findings(code, quoted)

    assert [item.line for item in findings] == [2, 2]
    assert _finding_values(source, findings) == [
        "Qt.rgba(1, 0, 0, 1)",
        "(Qt).hsla(0, 1, 0.5, 1)",
    ]
    assert numeric_color_constructor_lines(code, quoted) == {2}


def test_numeric_finding_spans_use_normalized_line_separators():
    call = "Qt.rgba(1, 0, 0, 1)"
    for separator in ("\n", "\r\n", "\r", "\u2028", "\u2029"):
        source = separator.join(("Item {", f"    color: {call}", "}", ""))
        _, _, code, _, quoted = _views(source)
        findings = numeric_color_constructor_findings(code, quoted)

        assert [item.line for item in findings] == [2], repr(separator)
        assert _finding_values(source, findings) == [call], repr(separator)


def test_grouped_receiver_span_can_start_before_legacy_report_line():
    source = """Item {
    color: (
        Qt
    ).rgba(1, 0, 0, 1)
}
"""
    _, _, code, _, quoted = _views(source)

    findings = numeric_color_constructor_findings(code, quoted)

    assert [item.line for item in findings] == [3]
    assert _finding_values(source, findings) == ["(\n        Qt\n    ).rgba(1, 0, 0, 1)"]


def test_mismatched_views_do_not_enable_static_bracket_receivers():
    code = "Qt[      ](1,0,0,1)\n"
    quoted = "Qt['rgba'](1,0,0,1)\r\n"

    assert numeric_color_constructor_findings(code, quoted) == ()
    assert numeric_color_constructor_lines(code, quoted) == set()


def test_repository_line_wrappers_match_position_findings():
    for root in SOURCE_ROOTS:
        for path in sorted(item for item in root.rglob("*") if item.suffix in {".qml", ".js"}):
            source = path.read_text(encoding="utf-8")
            code_lines, source_lines, code, array_code, quoted = _views(source)
            assert color_literal_lines(code_lines, source_lines) == {
                item.line for item in color_literal_findings(code_lines, source_lines)
            }, path
            assert color_array_literal_lines(array_code, quoted) == {
                item.line for item in color_array_literal_findings(array_code, quoted)
            }, path
            assert numeric_color_constructor_lines(code, quoted) == {
                item.line for item in numeric_color_constructor_findings(code, quoted)
            }, path
