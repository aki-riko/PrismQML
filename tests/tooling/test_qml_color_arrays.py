# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML color-array scanner regressions. QML 颜色数组扫描回归。"""

from pathlib import Path, PurePosixPath
from time import perf_counter

from scripts._qml_lint.qml_color_arrays import color_array_literal_lines
from scripts.qml_conventions import scan_source_text
from scripts._qml_lint.qml_lexer import sanitize_qml


ROOT = Path(__file__).resolve().parents[2]
LIBRARY_PATH = PurePosixPath("prismqml/PrismQML/Test.qml")
JAVASCRIPT_PATH = PurePosixPath("prismqml/PrismQML/Test.js")
EXEMPT_PATHS = (
    PurePosixPath("prismqml/PrismQML/PrismEnums/Constants.qml"),
    PurePosixPath("prismqml/PrismQML/effects/_internal/MatrixRainPresets.js"),
    PurePosixPath(
        "prismqml/PrismQML/controls/inputs/ColorPicker/_internal/ColorPickerDialog.qml"
    ),
    PurePosixPath("prismqml/PrismQML/controls/feedback/Confetti.qml"),
)
MIGRATED_EXAMPLE_ARRAY_PATHS = (
    PurePosixPath("examples/pages/CarouselPage.qml"),
    PurePosixPath("examples/pages/ChartPage.qml"),
)
GLOBAL_PALETTE_VALUE_LINES = {
    210, 212, 214, 216, 218, 220, 225, 226, 330, 331, 356, 357, 358, 359, 360, 361,
    379, 385, 386,
}


def _qml010_lines(source: str, path: PurePosixPath = LIBRARY_PATH) -> list[int]:
    return [
        item.line
        for item in scan_source_text(source, path)
        if item.rule == "QML010"
    ]


def _detector_lines(source: str) -> set[int]:
    return color_array_literal_lines(
        sanitize_qml(source, mask_strings=True, mark_values=True),
        sanitize_qml(source, mask_strings=False),
    )


def test_multiline_qml_color_collections_report_direct_literals():
    source = """Item {
    property var palette: [
        "#112233",
        "red",
        active ? "blue" : Enums.accentColor
    ]
    property list<color> stops:
    [
        "white"
    ]
    function fallbackColors() {
        return [
            "black"
        ]
    }
}
"""

    assert _qml010_lines(source) == [3, 4, 5, 9, 13]


def test_javascript_color_collections_and_function_returns_are_reported():
    source = """const swatches = [
    "red",
    "#fff",
]
function fallbackPalette() {
    return [
        "blue",
        enabled ? "white" : "black",
    ]
}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [2, 3, 7, 8]


def test_inline_color_collections_deduplicate_each_source_line():
    qml = 'Item { property var quickPalette: ["#fff", "red", "blue"] }\n'
    javascript = 'const colorStops = ["red", "blue"]\n'

    assert _qml010_lines(qml) == [1]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [1]


def test_non_color_arrays_and_nested_text_fields_do_not_report():
    source = """Item {
    property var model: ["red", "#fff"]
    property var themeNames: ["cyan", "red"]
    property var colors: [Enums.accentColor, Qt.lighter(Enums.accentColor, 1.2)]
    property var colorEntries: [{ label: "Red", value: 1 }]
    property var palettes: [
        { label: "Red", value: 1 },
        mapping["blue"],
        value === "red",
        { "red": 1 }
    ]
}
"""

    assert _qml010_lines(source) == []


def test_long_comparison_and_object_key_gaps_remain_non_values():
    padding = "/*" + "x" * 600 + "*/"
    source = f"""const colors = [
    value === {padding}"red",
    "blue"{padding} !== value,
    {{ "white"{padding}: 1 }}
]
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == []


def test_real_color_maps_use_tokens_but_literal_maps_remain_reported():
    path = PurePosixPath("examples/pages/InputPage.qml")
    source = (ROOT / path).read_text(encoding="utf-8")
    compressed = (
        'Item { property var tagColors: ({ first: Enums.accentColor, '
        'second: "#D13438" }) }\n'
    )

    assert (
        'colors[Fluent.Translator.tr("gallery_0efa477b24b1f3c7", '
        "Fluent.Translator._v)] = Enums.chartColors.palette[3]"
        in source
    )
    assert _qml010_lines(source, path) == []
    assert _qml010_lines(compressed) == [1]


def test_object_records_calls_and_grouping_are_distinguished():
    source = """Item {
    property var palettes: [
        { label: ["Red", "Blue"], value: 1 },
        { color: "#fff" },
        qsTr("Cyan"),
        ("blue"),
        mapping["red"]
    ]
}
"""

    assert _qml010_lines(source) == [4, 6]


def test_wrapped_and_conditional_color_arrays_are_reported():
    qml = """Item {
    property var palette: active ? (["red"]) : ["blue"]
    property list<color> swatches: enabled ? ["white"] : ["black"]
}
"""
    javascript = """function fallbackPalette() {
    return active ? (["red"]) : ["blue"]
}
"""

    assert _qml010_lines(qml) == [2, 3]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [2]


def test_multiline_wrappers_and_balanced_branches_preserve_owner():
    qml = """Item {
    property var palette: active ? [
        { label: "x" }
    ] : [
        "green"
    ]
}
"""
    javascript = """function fallbackPalette() {
    return (
        ["blue"]
    )
}
"""

    assert _qml010_lines(qml) == [5]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [3]


def test_named_owners_survive_balanced_object_branches_and_arguments():
    javascript = """const colors = active ? { label: 1 } : ["red"]
const palette = make({ label: 1 }, ["blue"])
"""
    qml = """Item {
    colors: active ? { label: 1 } : ["white"]
}
"""

    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [1, 2]
    assert _qml010_lines(qml) == [2]


def test_named_bindings_report_call_arguments_but_function_returns_do_not():
    qml = """Item {
    property var palette: make(["red"])
    property var swatches: lookup[["blue"]]
}
"""
    javascript = """colors = makeLabels(), ["black"]
function fallbackColors() { return make(["white"]) }
"""

    assert _qml010_lines(qml) == [2]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == []


def test_function_calls_inside_color_arrays_remain_non_direct_elements():
    source = """const colors = [make(["red"])]
const palette = [...make(["blue"])]
function fallbackColors() { return [make(["white"])] }
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == []


def test_spread_await_and_nested_function_boundaries_are_distinguished():
    source = """const colors = [...["red"]]
const palette = [...(["blue"])]
function fallbackColors() {
    const record = { return: ["black"] }
    const anonymous = function() { return ["white"] }
    const arrow = () => ["green"]
    return await ["cyan"]
}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [1, 2, 7]


def test_nested_default_parameters_and_arrow_asi_keep_function_owners():
    source = """function fallbackColors(value = make()) {
    return ["red"]
}
function outerColors() {
    function labels(value = make()) {
        return ["blue"]
    }
    return ["white"]
}
const makeLabel = () => value
const colors = ["black"]
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [2, 8, 11]


def test_method_and_getter_frames_keep_the_innermost_owner():
    source = """const provider = {
    fallbackColors() { return ["cyan"] }
}
function outerColors() {
    const helper = {
        labels() { return ["red"] },
        get shades() { return ["green"] }
    }
    return ["blue"]
}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [2, 9]


def test_arrow_asi_preserves_string_template_and_regex_values():
    source = """const label = () => "text"
const colors = ["red"]
const template = () => `text`
const palette = ["blue"]
const matcher = () => /x/
const swatches = ["white"]
const fallbackColors = () => func
(["cyan"])
const moreColors = () => value
+ ["magenta"]
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [2, 4, 6]


def test_non_array_unary_operators_do_not_propagate_collection_owners():
    source = """const colors = typeof ["red"]
const palette = void ["blue"]
const swatches = delete [["white"]]
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == []


def test_callable_parameter_defaults_and_binding_patterns_are_not_arrays():
    source = """const colors = (value = ["red"]) => value
const palette = ([label = "white"]) => label
const swatches = function(value = ["blue"]) { return value }
const themeColors = function([label = "black"]) { return label }
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == []


def test_named_function_expressions_and_arrows_report_direct_returns():
    source = """const fallbackColors = () => ["red"]
const fallbackPalette = function() { return ["blue"] }
const provider = { fallbackColors: () => ["white"] }
const labels = () => ["green"]
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [1, 2, 3]


def test_long_owner_contexts_expand_beyond_the_fast_prefix_window():
    padding = "/*" + "x" * 600 + "*/"
    source = f"""const colors = {padding}["red"]
function fallbackPalette() {{ return {padding}["blue"] }}
function outerColors() {{ const labels = () => {padding}["white"] }}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [1, 2]


def test_color_bindings_canvas_and_color_stops_accept_array_values():
    source = """Item {
    property color tint: ["label", "red"][1]
    color: ["red", "blue"][index]
    function paint(ctx) {
        ctx.fillStyle = ["white"]
        ctx.strokeStyle = enabled ? ["black"] : ["blue"]
        gradient.addColorStop(0, ["cyan"])
        gradient.addColorStop(clamp(x, 0, 1), ["magenta"])
        gradient.addColorStop(clamp(offset(a, b), 0, 1), "#abcdef")
    }
}
"""

    assert _qml010_lines(source) == [2, 3, 5, 6, 7, 8, 9]


def test_regex_and_string_receivers_are_not_array_literals():
    regex = 'const colors = /x/[["red"]]\n'
    string = 'const colors = "x"[["blue"]]\n'

    assert _qml010_lines(regex, JAVASCRIPT_PATH) == []
    assert _qml010_lines(string, JAVASCRIPT_PATH) == []


def test_regex_after_control_condition_does_not_corrupt_function_frames():
    source = """function fallbackColors() {
    if (ready) /{/.test(value)
    return ["red"]
}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [3]


def test_color_array_returns_use_the_innermost_function_and_respect_asi():
    source = """function fallbackPalette() {
    function labels() {
        return ["Red", "Blue"]
    }
    if (active)
        return (["red"])
    return
    ["blue"]
}
function wrapper() {
    function fallbackColors() {
        return [["white"]]
    }
}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [6, 12]


def test_only_high_confidence_collection_name_suffixes_are_scanned():
    source = """Item {
    property var colorNames: ["red"]
    property var paletteNames: ["blue"]
    property var swatchLabels: ["white"]
    property var colors: ["black"]
}
"""

    assert _qml010_lines(source) == [5]


def test_real_data_resources_and_dynamic_collections_stay_exempt():
    constants = EXEMPT_PATHS[0]
    source = (ROOT / constants).read_text(encoding="utf-8")
    assert _detector_lines(source) == GLOBAL_PALETTE_VALUE_LINES
    assert _qml010_lines(source, constants) == []

    for path in EXEMPT_PATHS[1:]:
        source = (ROOT / path).read_text(encoding="utf-8")
        assert _detector_lines(source) == set(), path
        assert _qml010_lines(source, path) == [], path


def test_color_array_lines_follow_all_supported_line_separators():
    for separator in ("\n", "\r\n", "\r", "\u2028", "\u2029"):
        qml = separator.join(
            ("Item {", "property var palette: [", "/* masked", "comment */", '"red"', "]", "}")
        )
        javascript = separator.join(
            ("const swatches = [", "// masked", '"blue"', "]")
        )
        wrapped_return = separator.join(
            ("function fallbackPalette() {", "return (", '["green"]', ")", "}")
        )
        conditional = separator.join(
            ("Item {", "property var palette: active ? [{ label: 1 }] : [", '"white"', "]", "}")
        )
        assert _qml010_lines(qml) == [5], repr(separator)
        assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [3], repr(separator)
        assert _qml010_lines(wrapped_return, JAVASCRIPT_PATH) == [3], repr(separator)
        assert _qml010_lines(conditional) == [3], repr(separator)


def test_unclosed_color_array_candidates_are_scanned_in_linear_time():
    source = "Item {\n" + "    property var palette: [\n" * 3000 + "}\n"
    started = perf_counter()

    assert _qml010_lines(source) == []
    assert perf_counter() - started < 0.75


def test_deeply_nested_color_arrays_are_scanned_in_linear_time():
    source = (
        "Item { property var palette: "
        + "[" * 3000
        + '"red"'
        + "]" * 3000
        + " }\n"
    )
    started = perf_counter()

    assert _qml010_lines(source) == [1]
    assert perf_counter() - started < 0.75


def test_large_closed_color_arrays_are_not_silently_skipped():
    dynamic_items = "Enums.accentColor," * 1500
    source = f'const colors = ["red", {dynamic_items} Enums.cardColor]\n'
    started = perf_counter()

    assert len(source) > 16384
    assert _qml010_lines(source, JAVASCRIPT_PATH) == [1]
    assert perf_counter() - started < 0.75


def test_real_example_object_arrays_use_global_color_tokens():
    for path in MIGRATED_EXAMPLE_ARRAY_PATHS:
        source = (ROOT / path).read_text(encoding="utf-8")
        assert _qml010_lines(source, path) == []
