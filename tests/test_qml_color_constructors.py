# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML numeric color-constructor scanner regressions. QML 数值构色扫描回归。"""

from pathlib import Path, PurePosixPath
from time import perf_counter

from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = PurePosixPath("prismqml/PrismQML/Test.qml")
JAVASCRIPT_PATH = PurePosixPath("prismqml/PrismQML/Test.js")
DATA_PATHS = (
    PurePosixPath("prismqml/PrismQML/Enums.qml"),
    PurePosixPath("prismqml/PrismQML/PrismEnums/Test.qml"),
    PurePosixPath("prismqml/PrismQML/PrismEnums/Test.js"),
)
REAL_TARGETS = {
    PurePosixPath("prismqml/PrismQML/controls/navigation/TabWidget.qml"): {
        444,
        445,
        452,
        453,
        459,
        460,
    },
    PurePosixPath("prismqml/PrismQML/controls/data/DataWidgetCore.qml"): {153},
    PurePosixPath("prismqml/PrismQML/controls/data/Label/Label.qml"): {24},
}


def _qml010_lines(source: str, path: PurePosixPath = LIBRARY_PATH) -> list[int]:
    return [
        item.line
        for item in scan_source_text(source, path)
        if item.rule == "QML010"
    ]


def _qml010_locations(source: str, path: PurePosixPath) -> list[tuple[int, str]]:
    return [
        (item.line, item.source.strip())
        for item in scan_source_text(source, path)
        if item.rule == "QML010"
    ]


def test_fixed_numeric_constructors_report_all_qml_contexts():
    source = """Item {
    color: Qt.rgba(1, 1, 1, 0.7)
    border.color: active ? Qt.rgba(0, 0, 0, 0.2) : Qt.rgba(1, 1, 1, 0.1)
    readonly property color accent: {
        if (active) return Qt.hsla(0.5, 1, 0.5, 1)
        return Qt.hsva(0.25, 1, 1, 1)
    }
    function paint(ctx) {
        ctx.fillStyle = Qt.rgba(0.1, 0.2, 0.3, 0.4)
        gradient.addColorStop(0, Qt.rgba(0, 0, 0, 0))
    }
    Component.onCompleted: background.color = Qt.rgba(0, 0, 0, 0.5)
}
"""

    assert _qml010_lines(source) == [2, 3, 5, 6, 9, 10, 12]


def test_fixed_visual_coefficients_report_but_dynamic_algorithms_do_not():
    source = """Item {
    property color base: Enums.accentColor
    readonly property color faded: Qt.rgba(base.r, base.g, base.b, 0.15)
    readonly property color themed: Qt.rgba(base.r, base.g, base.b, dark ? 0.20 : 0.14)
    readonly property color wrapped: Qt.rgba(base.r, base.g, base.b, dark ? (0.20) : (0.14))
    readonly property color dimmed: Qt.rgba(base.r * 0.25, base.g * 0.25, base.b * 0.25, 1)
    readonly property color inherited: Qt.rgba(base.r, base.g, base.b, base.a * 0.25)
    readonly property color scaledInherited: Qt.rgba(base.r * 0.25, 0.25 * base.g, base.b * (0.25), base.a * 0.5)
    readonly property color configured: Qt.rgba(base.r, base.g, base.b, opacity)
    function rainbowColor(hue) { return Qt.hsla(hue / 360, 1, 0.5, 1) }
    function editColor(c, value) { return Qt.hsva(c.h, c.s, value, c.a) }
    function pixelColor(r, g, b, a) { return Qt.rgba(r, g, b, a) }
}
"""

    assert _qml010_lines(source) == [3, 4, 5, 6, 7, 8]


def test_leading_decimal_and_optional_chain_ternaries_are_distinguished():
    source = """Item {
    property color leadingDecimal: Qt.rgba(base.r, base.g, base.b, active ? .2 : .1)
    property color nestedChoice: Qt.rgba(base.r, base.g, base.b, active ? hot ? .3 : .2 : .1)
    property color optionalChain: Qt.rgba(base.r, base.g, base.b, state?.active ? .2 : .1)
    property color nullishChoice: Qt.rgba(base.r, base.g, base.b, state ?? false ? .2 : .1)
}
"""

    assert _qml010_lines(source) == [2, 3, 4, 5]


def test_multiline_calls_and_nested_conversions_keep_balanced_arguments():
    source = """Item {
    property color overlay: Qt.rgba(
        0,
        0,
        0,
        0.4
    )
    property color hue: Qt.hsla(Qt.hsla(baseColor).h, 1, 0.5, 1)
}
"""

    assert _qml010_lines(source) == [2]


def test_spacing_constant_arithmetic_and_receiver_boundaries():
    source = """Item {
    property real opacity: 0.5
    property color arithmetic: Qt /* fixed red */ . rgba(255 / 255, 0 / 255, 0, 50 / 100)
    property color dynamicAlpha: Qt . hsla(0, 1, 0.5, opacity)
    property color fakeReceiver: helper.Qt.rgba(1, 1, 1, 1)
    property color spacedReceiver: helper . Qt.rgba(1, 1, 1, 1)
    property color commentReceiver: helper./* receiver */Qt.rgba(1, 1, 1, 1)
    property color multilineReceiver: helper.
        Qt.rgba(1, 1, 1, 1)
}
"""
    javascript = """const arithmetic = Qt /* fixed */ . rgba(1 / 2, 0, 0, 1)
const fakeReceiver = helper.Qt.rgba(1, 1, 1, 1)
const spacedReceiver = helper . Qt.rgba(1, 1, 1, 1)
const commentReceiver = helper./* receiver */Qt.rgba(1, 1, 1, 1)
const multilineReceiver = helper.
    Qt.rgba(1, 1, 1, 1)
"""

    assert _qml010_lines(source) == [3, 4]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [1]


def test_global_qt_receiver_variants_and_static_brackets_are_reported():
    source = """Item {
    property color optionalDot: Qt?.rgba(1, 0, 0, 1)
    property color parenthesized: (Qt).hsla(0, 1, 0.5, 1)
    property color nestedParentheses: ((Qt)).hsva(0, 1, 1, 1)
    property color singleBracket: Qt['rgba'](1, 0, 0, 1)
    property color doubleBracket: Qt["hsla"](0, 1, 0.5, 1)
    property string quoted: "Qt['rgba'](1, 0, 0, 1)"
    property color callReceiver: helper(Qt).rgba(1, 0, 0, 1)
    function makeColor() { return (Qt).rgba(1, 0, 0, 1) }
}
"""
    javascript = """const bracket = Qt["hsva"](0, 1, 1, 1)
const quoted = "Qt['rgba'](1, 0, 0, 1)"
"""

    assert _qml010_lines(source) == [2, 3, 4, 5, 6, 9]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [1]


def test_line_start_global_qt_is_not_attached_to_previous_statement():
    source = """Item {
    property color blockResult: {
        var marker = 1
        Qt.rgba(1, 0, 0, 1)
    }
    function inspect() {
        helper()
        Qt?.rgba(1, 0, 0, 1)
        helper.
            Qt.rgba(1, 0, 0, 1)
        helper()
        (Qt).rgba(1, 0, 0, 1)
    }
}
"""
    javascript = """let marker = 1
Qt['rgba'](1, 0, 0, 1)
helper()
(Qt).rgba(1, 0, 0, 1)
"""

    assert _qml010_lines(source) == [4, 8]
    assert _qml010_lines(javascript, JAVASCRIPT_PATH) == [2]


def test_javascript_line_separators_keep_constructor_source_lines():
    direct = "Qt.rgba(1, 0, 0, 1)"
    bracket = "Qt['rgba'](1, 0, 0, 1)"
    expected = [(2, direct), (3, bracket)]
    for separator in ("\n", "\r\n", "\r", "\u2028", "\u2029"):
        source = separator.join(("const marker = 1", direct, bracket, ""))
        assert _qml010_locations(source, JAVASCRIPT_PATH) == expected, repr(separator)


def test_masked_comments_preserve_constructor_source_lines():
    direct = "Qt.rgba(1, 0, 0, 1)"
    bracket = "Qt['rgba'](1, 0, 0, 1)"
    javascript_lines = ("/* first", "second */", direct, "// masked", bracket, "")
    qml_lines = (
        "Item {", "/* first", "second */", f"color: {direct}",
        "// masked", f"border.color: {bracket}", "}", "",
    )
    for separator in ("\n", "\r\n", "\r", "\u2028", "\u2029"):
        javascript = separator.join(javascript_lines)
        qml = separator.join(qml_lines)
        assert _qml010_locations(javascript, JAVASCRIPT_PATH) == [
            (3, direct), (5, bracket)
        ], repr(separator)
        assert _qml010_locations(qml, LIBRARY_PATH) == [
            (4, f"color: {direct}"), (6, f"border.color: {bracket}")
        ], repr(separator)


def test_deep_constant_expressions_do_not_break_or_bypass_budget():
    arithmetic = "+".join("1" for _ in range(1200))
    parentheses = "(" * 300 + "1" + ")" * 300
    source = f"""Item {{
    property color arithmetic: Qt.rgba({arithmetic}, 0, 0, 1)
    property color parentheses: Qt.rgba({parentheses}, 0, 0, 1)
    property color alpha: Qt.rgba(base.r, base.g, base.b, {parentheses})
}}
"""

    assert _qml010_lines(source) == []


def test_unclosed_constructor_candidates_are_scanned_in_linear_time():
    source = "Item {\n" + "    Qt.rgba(\n" * 3000 + "}\n"
    started = perf_counter()

    assert _qml010_lines(source) == []
    assert perf_counter() - started < 0.75


def test_constructor_detection_ignores_text_conversions_and_data_resources():
    source = """Item {
    property string description: "Qt.rgba(1, 1, 1, 1)"
    // color: Qt.rgba(0, 0, 0, 1)
    property color converted: Qt.hsla(baseColor)
    property color configured: Qt.rgba(base.r, base.g, base.b, root.opacity)
    property color calculated: Qt.rgba(finalR, finalG, finalB, finalA)
}
"""
    fixed = source.replace("Qt.hsla(baseColor)", "Qt.rgba(1, 1, 1, 0.5)")

    assert _qml010_lines(source) == []
    assert all(_qml010_lines(fixed, path) == [] for path in DATA_PATHS)


def test_javascript_numeric_constructors_share_the_same_rules():
    source = """function paint(ctx, color, alpha) {
    ctx.fillStyle = Qt.rgba(0, 0, 0, 0.5)
    ctx.strokeStyle = Qt.rgba(color.r, color.g, color.b, 0.2)
    ctx.shadowColor = Qt.rgba(color.r, color.g, color.b, alpha)
}
"""

    assert _qml010_lines(source, JAVASCRIPT_PATH) == [2, 3]


def test_repository_numeric_constructor_blind_spots_are_reported():
    for path, expected in REAL_TARGETS.items():
        source = (ROOT / path).read_text(encoding="utf-8")
        actual = set(_qml010_lines(source, path))
        assert expected <= actual, (path, expected - actual)
