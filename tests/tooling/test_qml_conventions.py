# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML convention scanner regression tests. QML 规范扫描器回归测试。"""

from pathlib import Path, PurePosixPath
import subprocess

from scripts import check_qml_conventions as scanner


ROOT = Path(__file__).resolve().parents[2]
LIBRARY_PATH = PurePosixPath("prismqml/PrismQML/Test.qml")
JAVASCRIPT_PATH = PurePosixPath("prismqml/PrismQML/effects/_internal/Test.js")
MATRIX_PRESETS_PATH = PurePosixPath(
    "prismqml/PrismQML/effects/_internal/MatrixRainPresets.js"
)
HIGH_CONFIDENCE_SOURCE = """
import QtQuick 2.15
import Qt5Compat.GraphicalEffects
import QtQuick.Controls
Item {
    property bool isDark: true
    enum LocalType { One, Two }
    color: "#ffffff"
    radius: 4
    font.family: "Arial"
    target: ThemeManager
}
"""
VALID_MATRIX_PRESETS_SOURCE = """.pragma library
var themes = {
    "classic": { main: "#00ff00", head: "#aaffaa", bg: "#000000" }
}
var themeNames = ["classic"]
"""


def _rules(text: str, path: PurePosixPath = LIBRARY_PATH) -> set[str]:
    return {item.rule for item in scanner.scan_source_text(text, path)}


def test_high_confidence_rules_and_explicit_exceptions():
    assert {
        "QML001",
        "QML002",
        "QML003",
        "QML004",
        "QML005",
        "QML007",
        "QML010",
        "QML011",
        "QML012",
    } <= _rules(HIGH_CONFIDENCE_SOURCE)

    widget = PurePosixPath("prismqml/PrismQML/controls/containers/Widget.qml")
    assert "QML003" not in _rules("import QtQuick.Controls\nPopup {}\n", widget)
    enums = PurePosixPath("prismqml/PrismQML/Enums.qml")
    assert "QML004" not in _rules("QtObject { target: ThemeManager }\n", enums)


def test_style_rules_ignore_log_message_contents():
    source = """Item {
    Component.onCompleted: console.log("radius: 4 color: \\\"#fff\\\"")
    Component.onDestruction: console.log(`radius: 8 color: "#000"`)
}
"""

    assert "QML010" not in _rules(source)
    assert "QML011" not in _rules(source)


def test_comment_swallowed_statements_report_high_confidence_cases():
    source = """Item {
    property bool _isInViewport: true
    // Calculate viewport    function _updateViewport() {
    // Recompute state    if (ready) {
    // Fallback state    _isInViewport = true
    // Hide now    visible = false
    // Reset size    implicitWidth = 0
    // Reparent now    parent = target
    // Fill parent    anchors.fill = parent
}
"""

    violations = scanner.scan_source_text(source, LIBRARY_PATH)
    lines = [item.line for item in violations if item.rule == "QML014"]

    assert lines == [3, 4, 5, 6, 7, 8, 9]


def test_comment_swallowed_guard_ignores_commented_code_examples():
    source = """Item {
    property bool _isInViewport: true
    // Usage:
    //   function _updateViewport() {
    //       if (ready) {
    //           _isInViewport = true
    // The function and if words are documentation.
}
"""

    assert "QML014" not in _rules(source)


def test_comment_swallowed_guard_ignores_block_comments_and_template_strings():
    source = """Item {
    /*
    // Block example    function demo() {
    */
    property string template: `first
    // Template example    visible = false
    last`
}
"""

    assert "QML014" not in _rules(source)


def test_color_bindings_report_literals_inside_expressions():
    source = """Item {
    readonly property color contrast: tinted ? "#000000" : "#ffffff"
    color: enabled ? Enums.accentColor : "transparent"
    border.color: active ? "white" : "black"
}
"""

    violations = scanner.scan_source_text(source, LIBRARY_PATH)
    color_lines = [item.line for item in violations if item.rule == "QML010"]

    assert color_lines == [2, 3, 4]


def test_multiline_and_custom_color_bindings_report_literals():
    source = """Item {
    readonly property color hoverColor: active
        ? "#4dffffff"
        : "transparent"
    dotColor: active ? "magenta" : Enums.transparent
    property string bgColorOverride: "#708090"
}
"""

    violations = scanner.scan_source_text(source, LIBRARY_PATH)
    color_lines = [item.line for item in violations if item.rule == "QML010"]

    assert color_lines == [3, 4, 5, 6]


def test_color_blocks_inline_objects_and_canvas_report_literals():
    source = """Item {
    readonly property color calculated: {
        if (active) return "red"
        return "#112233"
    }
    property var fallback: ({ color: "transparent", label: "white", blur: 0 })
    layer.effect: Shadow { color: "#00ccff" }
    function getAccentColor() { return "aliceblue" }
    function paint(ctx) {
        ctx.fillStyle = "white"
        ctx.strokeStyle = "#445566"
        gradient.addColorStop(0, "#abcdef")
    }
}
"""

    violations = scanner.scan_source_text(source, LIBRARY_PATH)
    color_lines = [item.line for item in violations if item.rule == "QML010"]

    assert color_lines == [3, 4, 6, 7, 8, 10, 11, 12]


def test_color_bindings_ignore_non_color_strings_and_comparisons():
    source = """Item {
    property string sample: "#ffffff"
    property bool tinted: sample !== "transparent"
    text: "#000000"
    color: state === "red" ? Enums.accentColor : Enums.cardColor
    readonly property color reverseComparison: "black" === sample ? Enums.accentColor : Enums.cardColor
    readonly property color indexedColor: palette["red"]
    property bool matchesColor: backgroundColor === "#000000"
    function stateName() { return "magenta" }
    readonly property color loggedColor: {
        console.log("white")
        if (sample === "transparent") return Enums.accentColor
        return Enums.cardColor
    }
    Component.onCompleted: console.log(`color: "#fff"`)
}
"""

    assert "QML010" not in _rules(source)


def test_color_binding_expressions_keep_data_resource_exceptions():
    source = """QtObject {
    readonly property color contrast: {
        if (tinted) return "red"
        return "#ffffff"
    }
    property string bgColorOverride: "#708090"
    dotColor: tinted ? "magenta" : Enums.accentColor
    property var fallback: ({ color: "transparent", blur: 0 })
    function paint(ctx) { ctx.fillStyle = "white" }
}
"""
    paths = [
        PurePosixPath("prismqml/PrismQML/Enums.qml"),
        PurePosixPath("prismqml/PrismQML/PrismEnums/Test.qml"),
    ]

    assert all("QML010" not in _rules(source, path) for path in paths)


def test_shadow_offsets_spread_and_scale_are_style_metrics():
    source = """MultiEffect {
    shadowHorizontalOffset: 4
    shadowVerticalOffset: -6
    property real shadowSpread: 0
    property real horizontalOffset: 0
    property real verticalOffset: -2
    property real spread: 0.0
    shadowScale: 1
}
"""

    violations = scanner.scan_source_text(source, LIBRARY_PATH)
    assert [item.line for item in violations if item.rule == "QML011"] == list(
        range(2, 9)
    )

    near_misses = """Item {
    property real contentHorizontalOffset: 4
    property real dataSpread: 2
    property real shadowScaleFactor: 1
}
"""
    assert "QML011" not in _rules(near_misses)


def test_javascript_colors_require_the_exact_local_data_exception():
    source = 'var preset = { main: "#00ff00" }\n'

    assert "QML010" in _rules(source, JAVASCRIPT_PATH)
    assert _rules(VALID_MATRIX_PRESETS_SOURCE, MATRIX_PRESETS_PATH) == set()

    similar_path = MATRIX_PRESETS_PATH.with_name("MatrixRainPreset.js")
    assert "QML010" in _rules(VALID_MATRIX_PRESETS_SOURCE, similar_path)

    comments_only = '// "#00ff00"\n/* "#aaffaa" */\nvar name = "classic"\n'
    assert "QML010" not in _rules(comments_only, JAVASCRIPT_PATH)


def test_local_style_data_exception_rejects_logic_metrics_and_name_drift():
    logic = VALID_MATRIX_PRESETS_SOURCE + (
        "var duration = 250\nfunction mutate() { return duration }\n"
    )
    name_drift = VALID_MATRIX_PRESETS_SOURCE.replace('["classic"]', '["cyan"]')
    extra_metric = VALID_MATRIX_PRESETS_SOURCE.replace(
        'bg: "#000000"', 'bg: "#000000", duration: 250'
    )

    for source in (logic, name_drift, extra_metric):
        assert "QML013" in _rules(source, MATRIX_PRESETS_PATH)


def test_repository_local_style_data_contract_is_valid():
    source = (ROOT / MATRIX_PRESETS_PATH).read_text(encoding="utf-8")

    assert scanner.scan_source_text(source, MATRIX_PRESETS_PATH) == []


def test_javascript_regex_literals_do_not_mask_following_qml():
    regexes = [
        r"line.match(/^```(\w*)\s*$/)",
        r'content.replace(/[#*`>\-]/g, "")',
        r"/[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]/.test(password)",
        r"text.replace(/\"/g, '&quot;').replace(/'/g, '&#39;')",
    ]
    for expression in regexes:
        source = f"Item {{\n    property var result: {expression}\n    spacing: 8\n}}\n"
        violations = scanner.scan_text(source, LIBRARY_PATH)
        metric_lines = [item.line for item in violations if item.rule == "QML011"]
        assert metric_lines == [3], expression


def test_member_order_accepts_forward_readonly_alias_and_behavior_exceptions():
    source = """
import QtQuick
Item {
    id: root
    readonly property bool hovered: area.containsMouse
    signal clicked()
    function reset() {}
    width: 100
    property alias mouseArea: area
    MouseArea {
        id: area
    }
    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
    Rectangle {}
    states: [State { name: "active" }]
    transitions: Transition {}
}
"""

    assert "QML008" not in _rules(source)


def test_member_order_reports_property_and_function_after_child():
    source = """
import QtQuick
Item {
    Rectangle { id: background }
    property string text: ""
    function reset() {}
}
"""

    violations = scanner.scan_text(source, LIBRARY_PATH)
    order_lines = [item.line for item in violations if item.rule == "QML008"]
    assert order_lines == [5, 6]


def test_section_labels_are_strict_but_data_resources_are_exempt():
    source = """
Item {
    // ==================== Public Props 公开属性 ====================
    property string text: ""
    // ==================== Properties 属性 ====================
}
"""

    violations = scanner.scan_text(source, LIBRARY_PATH)
    assert [item.line for item in violations if item.rule == "QML009"] == [5]
    data_path = PurePosixPath("prismqml/PrismQML/PrismEnums/Metrics.qml")
    assert "QML009" not in _rules(source, data_path)


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def _initialize_repo(root: Path, content: str) -> Path:
    qml = root / "prismqml" / "PrismQML" / "Legacy.qml"
    qml.parent.mkdir(parents=True)
    qml.write_text(content, encoding="utf-8")
    _git(root, "init")
    _git(root, "config", "user.name", "PrismQML Test")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "baseline")
    return qml


def test_changed_mode_reports_only_new_violation_fingerprints(tmp_path):
    baseline = """import QtQuick
Item {
    Rectangle {}
    property string legacy: ""
}
"""
    qml = _initialize_repo(tmp_path, baseline)
    current = baseline.replace("Item {\n", "Item {\n    property int radius: 4\n")
    qml.write_text(current, encoding="utf-8")

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert [item.rule for item in result.violations] == ["QML011"]


def test_changed_mode_detects_context_regression_on_unchanged_member(tmp_path):
    baseline = """import QtQuick
Item {
    property string text: ""
}
"""
    qml = _initialize_repo(tmp_path, baseline)
    current = baseline.replace("    property", "    Rectangle {}\n    property")
    qml.write_text(current, encoding="utf-8")

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert [item.rule for item in result.violations] == ["QML008"]
    assert result.violations[0].source == 'property string text: ""'


def test_changed_mode_maps_renames_to_the_old_baseline_path(tmp_path):
    baseline = """import QtQuick
Item {
    Rectangle {}
    property string legacy: ""
}
"""
    qml = _initialize_repo(tmp_path, baseline)
    renamed = qml.with_name("Renamed.qml")
    _git(tmp_path, "mv", str(qml.relative_to(tmp_path)), str(renamed.relative_to(tmp_path)))

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert result.violations == ()


def test_changed_mode_uses_old_suffix_to_scan_rename_baseline(tmp_path):
    _initialize_repo(tmp_path, "import QtQuick\nItem {}\n")
    javascript = tmp_path / JAVASCRIPT_PATH
    javascript.parent.mkdir(parents=True, exist_ok=True)
    javascript.write_text(
        'import QtQuick 2.15\nvar color = "#fff"\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "javascript baseline")

    renamed = javascript.with_suffix(".qml")
    _git(
        tmp_path,
        "mv",
        str(javascript.relative_to(tmp_path)),
        str(renamed.relative_to(tmp_path)),
    )

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert [item.rule for item in result.violations] == ["QML001"]
    assert result.violations[0].path == PurePosixPath(
        renamed.relative_to(tmp_path).as_posix()
    )


def test_changed_mode_scans_untracked_javascript_and_ignores_assets(tmp_path):
    _initialize_repo(tmp_path, "import QtQuick\nItem {}\n")
    javascript = tmp_path / JAVASCRIPT_PATH
    javascript.parent.mkdir(parents=True, exist_ok=True)
    javascript.write_text('var color = "#fff"\n', encoding="utf-8")
    javascript.with_suffix(".svg").write_text('<svg fill="#fff"/>\n', encoding="utf-8")
    javascript.with_suffix(".json").write_text('{"color":"#fff"}\n', encoding="utf-8")

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert [item.rule for item in result.violations] == ["QML010"]
    assert result.violations[0].path == JAVASCRIPT_PATH


def test_changed_mode_reports_invalid_untracked_local_style_data(tmp_path):
    _initialize_repo(tmp_path, "import QtQuick\nItem {}\n")
    presets = tmp_path / MATRIX_PRESETS_PATH
    presets.parent.mkdir(parents=True, exist_ok=True)
    presets.write_text(
        VALID_MATRIX_PRESETS_SOURCE + "var duration = 250\n",
        encoding="utf-8",
    )

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.base_total == 0
    assert [item.rule for item in result.violations] == ["QML013"]
    assert result.violations[0].path == MATRIX_PRESETS_PATH


def test_all_mode_is_enforcing_unless_report_only(tmp_path):
    qml = tmp_path / "prismqml" / "PrismQML" / "Bad.qml"
    qml.parent.mkdir(parents=True)
    qml.write_text("import QtQuick 2.15\nItem {}\n", encoding="utf-8")

    assert scanner.main(["--all", "--root", str(tmp_path), "--max-details", "0"]) == 1
    assert scanner.main(
        ["--all", "--root", str(tmp_path), "--report-only", "--max-details", "0"]
    ) == 0


def test_repository_theme_entrypoints_are_unified():
    violations = scanner.scan_repository(ROOT)
    theme_violations = [
        violation for violation in violations if violation.rule in {"QML004", "QML007"}
    ]

    assert theme_violations == []
