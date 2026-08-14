# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tests for conservative primitive color data flow. 保守基础颜色数据流测试。"""

from pathlib import PurePosixPath

import pytest

from scripts._qml_lint.qml_color_dataflow import propagated_color_findings
from scripts.qml_conventions import scan_source_text
from scripts._qml_lint.qml_scan_scope import new_violations


def _pairs(source: str, *, is_qml: bool) -> list[tuple[int, int]]:
    return [
        (finding.report_line, finding.use_line)
        for finding in propagated_color_findings(source, is_qml=is_qml)
    ]


@pytest.mark.parametrize(
    ("source", "is_qml", "expected"),
    [
        ('const seed = "red";\nctx.fillStyle = seed;\n', False, [(1, 2)]),
        (
            'Item {\n    readonly property string seed: "#123456"\n'
            '    color: seed\n}\n',
            True,
            [(2, 3)],
        ),
        (
            'Item {\n    readonly property string forwarded: seed\n'
            '    readonly property string seed: "#123456"\n'
            '    color: forwarded\n}\n',
            True,
            [(3, 4)],
        ),
        (
            'Item {\n    id: root\n'
            '    readonly property string seed: "#123456"\n'
            '    Rectangle { color: root.seed }\n}\n',
            True,
            [(3, 4)],
        ),
        (
            'const seed = "red";\nctx.fillStyle = seed;\n'
            'gradient.addColorStop(0, seed);\n'
            'function iconColor() { return seed; }\n',
            False,
            [(1, 2), (1, 3), (1, 4)],
        ),
        ('const seed = "red";\nconst palette = [seed];\n', False, [(1, 2)]),
        (
            'const red = 1;\nconst green = 0;\nconst blue = 0;\n'
            'const value = Qt.rgba(red, green, blue, 1);\n',
            False,
            [(4, 4)],
        ),
    ],
)
def test_high_confidence_color_flow(source, is_qml, expected):
    assert _pairs(source, is_qml=is_qml) == expected


@pytest.mark.parametrize(
    ("source", "is_qml"),
    [
        ('let seed = "red";\nctx.fillStyle = seed;\n', False),
        ('var seed = "red";\nctx.fillStyle = seed;\n', False),
        (
            'Item {\n    property string seed: "#123456"\n'
            '    color: seed\n}\n',
            True,
        ),
        (
            'const seed = "red";\n'
            'function paint(seed) { ctx.fillStyle = seed; }\n',
            False,
        ),
        ('const seed = "red";\nseed = other;\nctx.fillStyle = seed;\n', False),
        (
            'Item {\n    readonly property string seed: "#123456"\n'
            '    Rectangle { color: seed }\n}\n',
            True,
        ),
        ('const seed = "red";\nconst value = make(seed);\n', False),
        ('const seed = ["red"];\nconst palette = seed;\n', False),
        (
            'const first = second;\nconst second = first;\n'
            'ctx.fillStyle = first;\n',
            False,
        ),
        (
            'const Qt = helper;\nconst red = 1;\nconst green = 0;\n'
            'const blue = 0;\nQt.rgba(red, green, blue, 1);\n',
            False,
        ),
    ],
)
def test_uncertain_color_flow_fails_closed(source, is_qml):
    assert propagated_color_findings(source, is_qml=is_qml) == ()


def test_each_use_preserves_an_independent_changed_baseline_event():
    path = PurePosixPath("prismqml/PrismQML/Test.qml")
    baseline = 'const seed = "#123456";\nctx.fillStyle = seed;\n'
    current = baseline + "ctx.strokeStyle = seed;\n"
    baseline_violations = scan_source_text(baseline, path)
    current_violations = scan_source_text(current, path)
    assert len(baseline_violations) == 1
    assert len(current_violations) == 2
    assert len(new_violations(current_violations, baseline_violations)) == 1


@pytest.mark.parametrize(
    ("source", "path", "is_qml"),
    [
        (
            'Item {\n    readonly property color seed: "#123456"\n'
            '    color: seed\n}\n',
            PurePosixPath("prismqml/PrismQML/Test.qml"),
            True,
        ),
        (
            'const seed = "#123456";\nctx.fillStyle = seed;\n',
            PurePosixPath("prismqml/PrismQML/Test.js"),
            False,
        ),
    ],
)
def test_directly_reported_origins_are_not_counted_again(source, path, is_qml):
    assert propagated_color_findings(source, is_qml=is_qml) == ()
    assert [item.rule for item in scan_source_text(source, path)] == ["QML010"]


@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r", "\u2028", "\u2029"])
def test_color_flow_normalizes_all_supported_line_separators(separator):
    source = separator.join(['const seed = "red";', "ctx.fillStyle = seed;", ""])
    assert _pairs(source, is_qml=False) == [(1, 2)]


def test_conditional_and_short_circuit_origins_keep_each_branch():
    conditional = 'const seed = enabled ? "red" : "blue";\nctx.fillStyle = seed;\n'
    short_circuit = 'const seed = primary || "green";\nctx.fillStyle = seed;\n'
    assert _pairs(conditional, is_qml=False) == [(1, 2), (1, 2)]
    assert _pairs(short_circuit, is_qml=False) == [(1, 2)]


@pytest.mark.parametrize(
    "expression",
    ['make("red")', '["red"][0]', '({color: "red"}).color', '"red" === current'],
)
def test_non_direct_literal_sources_do_not_become_origins(expression):
    source = f"const seed = {expression};\nctx.fillStyle = seed;\n"
    assert propagated_color_findings(source, is_qml=False) == ()


@pytest.mark.parametrize(
    "sink",
    [
        "ctx.fillStyle = make(seed);",
        "const value = seed === current;",
        "const value = palette[seed];",
        "const value = object.seed;",
    ],
)
def test_non_direct_uses_do_not_become_color_sinks(sink):
    source = f'const seed = "red";\n{sink}\n'
    assert propagated_color_findings(source, is_qml=False) == ()


@pytest.mark.parametrize(
    "source",
    [
        'const seed = "red;\nctx.fillStyle = seed;\n',
        "const seed = (((((((((((((((((((((((((((((((((((((((((1;",
        'const seed = "red";\nconst alias = (seed;\nctx.fillStyle = alias;\n',
        "const first = second;\nconst second = first;\nctx.fillStyle = first;\n",
    ],
)
def test_malformed_and_cyclic_inputs_fail_closed(source):
    assert propagated_color_findings(source, is_qml=False) == ()


def test_valid_prefix_remains_visible_before_malformed_tail():
    source = 'const seed = "red";\nctx.fillStyle = seed;\n{{{{'
    assert _pairs(source, is_qml=False) == [(1, 2)]


def test_alias_chain_over_budget_fails_closed():
    source = "Item {\n"
    source += "\n".join(
        f"    readonly property string alias{index}: "
        f"{'seed' if index == 139 else f'alias{index + 1}'}"
        for index in range(140)
    )
    source += '\n    readonly property string seed: "#123456"'
    source += "\n    color: alias0\n}\n"
    assert propagated_color_findings(source, is_qml=True) == ()
