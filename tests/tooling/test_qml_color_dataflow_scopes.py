# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Scope and write tests for primitive color flow. 基础颜色流作用域与写入测试。"""

from pathlib import PurePosixPath

import pytest

from scripts._qml_lint.qml_color_dataflow import propagated_color_findings
from scripts.qml_conventions import scan_source_text


def _pairs(source: str, *, is_qml: bool) -> list[tuple[int, int]]:
    return [
        (finding.report_line, finding.use_line)
        for finding in propagated_color_findings(source, is_qml=is_qml)
    ]


def test_unrelated_shadows_and_member_writes_do_not_kill_outer_binding():
    source = """const alpha = 0.25;
function withParameter(alpha) {
    consume();
    Qt.rgba(alpha, 0, 0, 1);
}
function withHoistedVar() {
    if (enabled) { var alpha = dynamic; }
    consume();
    Qt.rgba(alpha, 0, 0, 1);
}
holder.alpha = dynamic;
Qt.rgba(alpha, 0, 0, 1);
"""

    assert _pairs(source, is_qml=False) == [(12, 12)]


def test_nested_const_bindings_resolve_to_their_own_uses():
    source = """const seed = "red";
ctx.fillStyle = seed;
{
    const seed = "blue";
    ctx.strokeStyle = seed;
}
"""

    assert _pairs(source, is_qml=False) == [(1, 2), (4, 5)]


def test_multiple_const_declarators_feed_one_constructor():
    source = """const red = 1, green = 0, blue = 0;
Qt.rgba(red, green, blue, 1);
"""

    assert _pairs(source, is_qml=False) == [(2, 2)]


def test_qml_child_property_does_not_hide_explicit_parent_id():
    source = """Item {
    id: root
    readonly property real alpha: 0.25
    Rectangle { property real alpha: dynamic }
    color: Qt.rgba(root.alpha, 0, 0, 1)
}
"""

    assert _pairs(source, is_qml=True) == [(5, 5)]


def test_local_qt_only_suppresses_its_own_function_scope():
    source = """const red = 1, green = 0, blue = 0;
function local(Qt = helper()) {
    consume();
    Qt.rgba(red, green, blue, 1);
}
Qt.rgba(red, green, blue, 1);
"""

    assert _pairs(source, is_qml=False) == [(6, 6)]


@pytest.mark.parametrize(
    "source",
    [
        """const red = 1, green = 0, blue = 0;
function local(Qt = helper()) { consume(); Qt.rgba(red, green, blue, 1); }
""",
        """const red = 1, green = 0, blue = 0;
function local() { Qt.rgba(red, green, blue, 1); const Qt = helper; }
""",
        """const red = 1, green = 0, blue = 0;
try { consume(); } catch (Qt) { consume(); Qt.rgba(red, green, blue, 1); }
""",
        """const red = 1, green = 0, blue = 0;
function local() { const {Qt} = helper; Qt.rgba(red, green, blue, 1); }
""",
        """const red = 1, green = 0, blue = 0;
function local() { const [Qt] = helper; Qt.rgba(red, green, blue, 1); }
""",
        """const red = 1, green = 0, blue = 0;
const local = Qt => (consume(), Qt.rgba(red, green, blue, 1));
""",
        """import Qt from "helper";
const red = 1, green = 0, blue = 0;
Qt.rgba(red, green, blue, 1);
""",
        """const red = 1, green = 0, blue = 0;
class Qt {}
Qt.rgba(red, green, blue, 1);
""",
    ],
)
def test_javascript_qt_shadows_suppress_propagated_constructor(source):
    assert propagated_color_findings(source, is_qml=False) == ()


@pytest.mark.parametrize(
    "declaration",
    [
        "const ignored = make(), Qt = helper();",
        "const ignored = make(), {Qt} = helper;",
    ],
)
def test_later_declarator_qt_shadows_builtin(declaration):
    source = f"""const alpha = 0.25;
{declaration}
Qt.rgba(alpha, 0, 0, 1);
"""

    assert propagated_color_findings(source, is_qml=False) == ()


@pytest.mark.parametrize(
    "declaration",
    [
        "const {alpha: localAlpha} = values;",
        "const {value: localAlpha = alpha} = values;",
        "const [localAlpha = alpha] = values;",
    ],
)
def test_destructuring_keys_and_defaults_do_not_shadow_outer_reads(declaration):
    source = f"""const alpha = 0.25;
function local() {{
    {declaration}
    Qt.rgba(alpha, 0, 0, 1);
}}
"""

    assert _pairs(source, is_qml=False) == [(4, 4)]


@pytest.mark.parametrize(
    "source",
    [
        """Item {
    readonly property real red: 1
    readonly property real green: 0
    readonly property real blue: 0
    property var Qt: helper
    color: Qt.rgba(red, green, blue, 1)
}
""",
        """Item {
    id: Qt
    readonly property real red: 1
    readonly property real green: 0
    readonly property real blue: 0
    color: Qt.rgba(red, green, blue, 1)
}
""",
    ],
)
def test_qml_qt_shadows_suppress_propagated_constructor(source):
    assert propagated_color_findings(source, is_qml=True) == ()


@pytest.mark.parametrize(
    "write",
    [
        "root.alpha = dynamic",
        "root.alpha += 1",
        "root.alpha &&= dynamic",
        "root.alpha ||= dynamic",
        "root.alpha ??= dynamic",
        "root.alpha >>>= 1",
        "root.alpha++",
        "++root.alpha",
    ],
)
def test_exact_qml_id_writes_invalidate_only_that_binding(write):
    source = f"""Item {{
    id: root
    readonly property real alpha: 0.25
    function mutate() {{ {write}; }}
    color: Qt.rgba(root.alpha, 0, 0, 1)
}}
"""

    assert propagated_color_findings(source, is_qml=True) == ()


@pytest.mark.parametrize(
    "target",
    ["root['alpha']", 'root["alpha"]', "root[`alpha`]", "root[key]"],
)
def test_qml_id_bracket_writes_fail_closed(target):
    source = f"""Item {{
    id: root
    readonly property real alpha: 0.25
    function mutate() {{ {target} = dynamic; }}
    color: Qt.rgba(root.alpha, 0, 0, 1)
}}
"""

    assert propagated_color_findings(source, is_qml=True) == ()


@pytest.mark.parametrize(
    "write",
    ["root[key]++", "++root[key]", "root[key]--", "--root[key]"],
)
def test_dynamic_qml_id_bracket_updates_fail_closed(write):
    source = f"""Item {{
    id: root
    readonly property real alpha: 0.25
    function mutate() {{ {write}; }}
    color: Qt.rgba(root.alpha, 0, 0, 1)
}}
"""

    assert propagated_color_findings(source, is_qml=True) == ()


@pytest.mark.parametrize(
    "write",
    [
        "alpha &&= dynamic",
        "alpha ||= dynamic",
        "alpha ??= dynamic",
        "alpha >>>= 1",
        "[alpha] = values",
        "({value: alpha} = object)",
        "for (alpha of values) { consume(alpha); }",
    ],
)
def test_exact_bare_writes_invalidate_candidate(write):
    source = f"""const alpha = 0.25;
{write};
Qt.rgba(alpha, 0, 0, 1);
"""

    assert propagated_color_findings(source, is_qml=False) == ()


def test_concise_arrow_parameter_does_not_pollute_outer_scope():
    source = """const alpha = 0.25;
const local = alpha => (consume(), Qt.rgba(alpha, 0, 0, 1));
Qt.rgba(alpha, 0, 0, 1);
"""

    assert _pairs(source, is_qml=False) == [(3, 3)]


def test_multiline_function_parameter_blocks_outer_qt():
    source = """const red = 1, green = 0, blue = 0;
function local(
    Qt
) {
    consume();
    Qt.rgba(red, green, blue, 1);
}
"""

    assert propagated_color_findings(source, is_qml=False) == ()


@pytest.mark.parametrize("parameter", ["{Qt}", "Qt = {rgba: helper}"])
def test_object_shaped_parameters_block_builtin_qt(parameter):
    source = f"""const red = 1, green = 0, blue = 0;
function local({parameter}) {{
    consume();
    Qt.rgba(red, green, blue, 1);
}}
"""

    assert propagated_color_findings(source, is_qml=False) == ()


@pytest.mark.parametrize(
    "parameter", ["{Qt: LocalQt}", "{value = alpha}", "[value = alpha]"]
)
def test_parameter_keys_and_defaults_do_not_shadow_outer_reads(parameter):
    source = f"""const alpha = 0.25;
function local({parameter}) {{
    consume();
    Qt.rgba(alpha, 0, 0, 1);
}}
"""

    assert _pairs(source, is_qml=False) == [(4, 4)]


@pytest.mark.parametrize(
    ("import_line", "expected"),
    [
        ('import {Qt as LocalQt} from "helper";', [(3, 3)]),
        ('import {Helper as Qt} from "helper";', []),
        ('import * as Qt from "helper";', []),
        ('import * as Helper from "helper";', [(3, 3)]),
    ],
)
def test_imports_only_bind_their_local_names(import_line, expected):
    source = f"""{import_line}
const alpha = 0.25;
Qt.rgba(alpha, 0, 0, 1);
"""

    assert _pairs(source, is_qml=False) == expected


def test_for_header_const_is_not_a_file_scope_candidate():
    source = """for (const alpha = 0.25; enabled; step()) { consume(alpha); }
Qt.rgba(alpha, 0, 0, 1);
"""

    assert propagated_color_findings(source, is_qml=False) == ()


def test_local_owner_shadow_does_not_resolve_as_qml_id():
    source = """Item {
    id: root
    readonly property string seed: "#123456"
    function iconColor(root) { consume(); return root.seed; }
    color: root.seed
}
"""

    assert _pairs(source, is_qml=True) == [(3, 5)]


@pytest.mark.parametrize(
    ("source", "path"),
    [
        (
            "const Qt = helper;\nQt.rgba(1, 0, 0, 1);\n",
            PurePosixPath("prismqml/PrismQML/Test.js"),
        ),
        (
            "const ignored = make(), Qt = helper();\nQt.rgba(1, 0, 0, 1);\n",
            PurePosixPath("prismqml/PrismQML/Test.js"),
        ),
        (
            "function local(Qt) { consume(); Qt.rgba(1, 0, 0, 1); }\n",
            PurePosixPath("prismqml/PrismQML/Test.js"),
        ),
        (
            "try {} catch (Qt) { Qt.rgba(1, 0, 0, 1); }\n",
            PurePosixPath("prismqml/PrismQML/Test.js"),
        ),
        (
            "const {Qt} = helper;\nQt.rgba(1, 0, 0, 1);\n",
            PurePosixPath("prismqml/PrismQML/Test.js"),
        ),
        (
            'import Qt from "helper";\nQt.rgba(1, 0, 0, 1);\n',
            PurePosixPath("prismqml/PrismQML/Test.js"),
        ),
        (
            "Item {\n    property var Qt: helper\n"
            "    color: Qt.rgba(1, 0, 0, 1)\n}\n",
            PurePosixPath("prismqml/PrismQML/Test.qml"),
        ),
    ],
)
def test_direct_numeric_scanner_respects_local_qt_shadow(source, path):
    assert "QML010" not in {item.rule for item in scan_source_text(source, path)}


def test_direct_numeric_scanner_keeps_unshadowed_global_qt():
    path = PurePosixPath("prismqml/PrismQML/Test.js")
    violations = scan_source_text("Qt.rgba(1, 0, 0, 1);\n", path)
    assert [item.rule for item in violations] == ["QML010"]
