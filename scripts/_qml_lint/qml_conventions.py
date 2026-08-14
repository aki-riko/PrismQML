# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Read-only PrismQML convention scanner. 只读 QML 规范扫描器。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
import re
from typing import Sequence

if __package__:
    from . import qml_scan_scope as _scan_scope
    from .qml_color_arrays import color_array_literal_lines
    from .qml_comment_guard import commented_executable_lines
    from .qml_color_contexts import color_literal_lines as _color_literal_lines
    from .qml_color_dataflow import analyze_color_dataflow
    from .qml_lexer import sanitize_qml as _sanitize_qml
    from .qml_local_style_contract import local_style_contract_error
else:
    import qml_scan_scope as _scan_scope
    from qml_color_arrays import color_array_literal_lines
    from qml_comment_guard import commented_executable_lines
    from qml_color_contexts import color_literal_lines as _color_literal_lines
    from qml_color_dataflow import analyze_color_dataflow
    from qml_lexer import sanitize_qml as _sanitize_qml
    from qml_local_style_contract import local_style_contract_error


ChangedQmlFile = _scan_scope.ChangedQmlFile
ChangedScanResult = _scan_scope.ChangedScanResult
QML_ROOT = _scan_scope.QML_ROOT
EXAMPLES_ROOT = _scan_scope.EXAMPLES_ROOT
SCAN_ROOTS = _scan_scope.SCAN_ROOTS
SUPPORTED_SOURCE_SUFFIXES = _scan_scope.SUPPORTED_SOURCE_SUFFIXES
EXAMPLES_ALLOWED_RULES = _scan_scope.EXAMPLES_ALLOWED_RULES
new_violations = _scan_scope.new_violations
_scan_changed = _scan_scope.scan_changed
_scan_repository = _scan_scope.scan_repository


QTQUICK_CONTROLS_EXCEPTIONS = {
    PurePosixPath("prismqml/PrismQML/controls/containers/Widget.qml"),
    PurePosixPath(
        "prismqml/PrismQML/controls/containers/_internal/WidgetToolTipPopup.qml"
    ),
    # PopupWindowCore is the reviewed internal Qt Popup infrastructure wrapper.
    # PopupWindowCore 是已评审的内部 Qt Popup 基础设施封装。
    PurePosixPath("prismqml/PrismQML/controls/utils/PopupWindowCore.qml"),
}
MATRIX_RAIN_PRESETS_PATH = PurePosixPath(
    "prismqml/PrismQML/effects/_internal/MatrixRainPresets.js"
)
LOCAL_STYLE_DATA_EXCEPTIONS = {
    MATRIX_RAIN_PRESETS_PATH: frozenset({"QML010"}),
}
VALID_SECTION_LABELS = {
    "Public Props 公开属性",
    "Required Props 必需属性",
    "Internal Props 内部属性",
    "Readonly State 只读状态",
    "Signals 信号",
    "Public Methods 公开方法",
    "Internal Methods 内部方法",
    "Size 尺寸",
    "Content 内容",
}
SECTION_RE = re.compile(r"^\s*//\s*=+\s*(.*?)\s*=+\s*$")
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|[{}()\[\]:;,.]")
OBJECT_PREFIX_RE = re.compile(
    r"(?:^|[:\[,(;{}])\s*(?:component\s+\w+\s*:\s*)?"
    r"[A-Z]\w*(?:\.[A-Z]\w*)*(?:\s+on\s+[\w.]+)?\s*$"
)
PROPERTY_RE = re.compile(
    r"^(?:(?:default|required|readonly)\s+)*property\s+"
    r"(?:alias|[A-Za-z_]\w*(?:<[^>]+>)?)\s+([A-Za-z_]\w*)"
)
ALIAS_RE = re.compile(
    r"^(?:(?:default|required|readonly)\s+)*property\s+alias\s+"
    r"[A-Za-z_]\w*\s*:\s*([A-Za-z_]\w*)"
)
ID_RE = re.compile(r"^id\s*:\s*([A-Za-z_]\w*)")
CHILD_RE = re.compile(
    r"^(?:component\s+\w+\s*:\s*)?[A-Z]\w*(?:\.[A-Z]\w*)*"
    r"(?:\s+on\s+[\w.]+)?\s*\{"
)
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*:")
GROUPED_PROPERTY_RE = re.compile(r"^[a-z_]\w*(?:\.[A-Za-z_]\w*)*\s*\{")
LOCAL_THEME_PROXY_RE = re.compile(
    r"^(?:(?:default|required|readonly)\s+)*property\s+"
    r"(?:alias|[A-Za-z_]\w*(?:<[^>]+>)?)\s+(?:isDark|fontFamily)\b"
)
METRIC_LITERAL_RE = re.compile(
    r"^\s*(?:(?:(?:default|required|readonly)\s+)*property\s+"
    r"[A-Za-z_]\w*(?:<[^>]+>)?\s+)?"
    r"(?:radius|spacing|padding|leftPadding|rightPadding|topPadding|"
    r"bottomPadding|anchors\.margins|anchors\.[A-Za-z]+Margin|"
    r"Layout\.[A-Za-z]+Margin|font\.pixelSize|duration|border\.width|"
    r"shadowLevel|shadowBlur|shadowOffsetX|shadowOffsetY|shadowSpread|"
    r"shadowHorizontalOffset|shadowVerticalOffset|horizontalOffset|"
    r"verticalOffset|spread|shadowScale)\s*:\s*"
    r"-?\d+(?:\.\d+)?\b"
)
FONT_LITERAL_RE = re.compile(r"^\s*font\.family\s*:\s*['\"]")
QUOTED_HEX_COLOR_RE = re.compile(
    r"(?P<quote>['\"`])#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})(?P=quote)"
)
@dataclass(frozen=True)
class Violation:
    path: PurePosixPath
    line: int
    rule: str
    message: str
    source: str

    def fingerprint(self) -> tuple[str, str, str, str]:
        normalized = re.sub(r"\s+", " ", self.source).strip()
        return (self.path.as_posix(), self.rule, self.message, normalized)


@dataclass
class MemberEvent:
    line: int
    category: str
    rank: int | None
    source: str
    alias_target: str | None = None
    target_context: "ObjectContext | None" = None


@dataclass
class ObjectContext:
    members: list[MemberEvent] = field(default_factory=list)
    id_name: str | None = None


@dataclass
class Frame:
    opener: str
    kind: str
    context: ObjectContext | None = None


def _is_data_resource(path: PurePosixPath) -> bool:
    return path.name == "Enums.qml" or "PrismEnums" in path.parts


def _violation(
    path: PurePosixPath, line: int, rule: str, message: str, source: str
) -> Violation:
    return Violation(path, line, rule, message, source.strip())


def _scan_imports_and_theme(
    code_lines: Sequence[str], source_lines: Sequence[str], path: PurePosixPath
) -> list[Violation]:
    violations: list[Violation] = []
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        stripped = code.strip()
        if re.match(r"^import\s+\S+\s+\d+(?:\.\d+)*\b", stripped):
            violations.append(_violation(path, number, "QML001", "versioned import", source))
        if re.match(r"^import\s+Qt5Compat(?:\.|\s|$)", stripped):
            violations.append(_violation(path, number, "QML002", "Qt5Compat import", source))
        if re.match(r"^import\s+QtQuick\.Controls(?:\s|$)", stripped):
            if path not in QTQUICK_CONTROLS_EXCEPTIONS:
                violations.append(
                    _violation(path, number, "QML003", "QtQuick.Controls import", source)
                )
        if path.name != "Enums.qml" and re.search(r"\bThemeManager\b", stripped):
            violations.append(
                _violation(path, number, "QML004", "direct ThemeManager access", source)
            )
    return violations


def _scan_declarations(
    code_lines: Sequence[str], source_lines: Sequence[str], path: PurePosixPath
) -> list[Violation]:
    violations: list[Violation] = []
    if path.name.endswith("Enums.qml") and path.name != "Enums.qml":
        violations.append(_violation(path, 1, "QML006", "legacy *Enums.qml file", path.name))
    if _is_data_resource(path):
        return violations
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        stripped = code.strip()
        if re.match(r"^enum\s+[A-Za-z_]\w*\s*\{", stripped):
            violations.append(_violation(path, number, "QML005", "component-local enum", source))
        if LOCAL_THEME_PROXY_RE.match(stripped):
            violations.append(
                _violation(path, number, "QML007", "local isDark/fontFamily proxy", source)
            )
    return violations


def _scan_sections(raw_lines: Sequence[str], path: PurePosixPath) -> list[Violation]:
    if _is_data_resource(path):
        return []
    violations: list[Violation] = []
    for number, source in enumerate(raw_lines, start=1):
        match = SECTION_RE.match(source)
        if match and match.group(1).strip() not in VALID_SECTION_LABELS:
            violations.append(
                _violation(path, number, "QML009", "non-standard section label", source)
            )
    return violations


def _scan_style_literals(
    code_lines: Sequence[str],
    source_lines: Sequence[str],
    array_code_lines: Sequence[str],
    numeric_lines: set[int] | frozenset[int],
    path: PurePosixPath,
) -> list[Violation]:
    if _is_data_resource(path):
        return []
    violations: list[Violation] = []
    color_lines = _color_literal_lines(code_lines, source_lines)
    array_masked_text = "\n".join(array_code_lines)
    quoted_text = "\n".join(source_lines)
    color_lines.update(numeric_lines)
    color_lines.update(color_array_literal_lines(array_masked_text, quoted_text))
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        if number in color_lines:
            violations.append(_violation(path, number, "QML010", "hardcoded color", source))
        if METRIC_LITERAL_RE.search(code):
            violations.append(_violation(path, number, "QML011", "hardcoded style metric", source))
        if FONT_LITERAL_RE.search(source):
            violations.append(_violation(path, number, "QML012", "hardcoded font family", source))
    return violations


def _scan_color_dataflow(
    text: str, path: PurePosixPath, findings
) -> list[Violation]:
    if _is_data_resource(path) or "QML010" in LOCAL_STYLE_DATA_EXCEPTIONS.get(
        path, frozenset()
    ):
        return []
    lines = text.splitlines()
    return [
        _violation(
            path, finding.report_line, "QML010", "hardcoded color",
            lines[finding.report_line - 1],
        )
        for finding in findings
    ]


def _scan_local_style_data_contract(text: str, path: PurePosixPath) -> list[Violation]:
    message = local_style_contract_error(text)
    return [] if message is None else [_violation(path, 1, "QML013", message, path.name)]


def _scan_javascript_style_literals(text: str, path: PurePosixPath) -> list[Violation]:
    if _is_data_resource(path):
        return []
    allowed_rules = LOCAL_STYLE_DATA_EXCEPTIONS.get(path, frozenset())
    violations = (
        _scan_local_style_data_contract(text, path)
        if path == MATRIX_RAIN_PRESETS_PATH
        else []
    )
    array_masked_text = _sanitize_qml(
        text, mask_strings=True, mark_values=True
    )
    quoted_text = _sanitize_qml(text, mask_strings=False)
    analysis = analyze_color_dataflow(text, is_qml=False)
    constructor_lines = analysis.numeric_lines
    array_lines = color_array_literal_lines(array_masked_text, quoted_text)
    code_lines = quoted_text.splitlines()
    source_lines = text.splitlines()
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        hardcoded = (
            QUOTED_HEX_COLOR_RE.search(code)
            or number in constructor_lines
            or number in array_lines
        )
        if hardcoded and "QML010" not in allowed_rules:
            violations.append(_violation(path, number, "QML010", "hardcoded color", source))
    violations.extend(_scan_color_dataflow(text, path, analysis.findings))
    return violations


def _classify_member(code: str, source: str, line: int) -> MemberEvent | None:
    if match := ID_RE.match(code):
        return MemberEvent(line, "id", 1, source, alias_target=match.group(1))
    if PROPERTY_RE.match(code):
        alias = ALIAS_RE.match(code)
        target = alias.group(1) if alias else None
        return MemberEvent(line, "property", 2, source, alias_target=target)
    if re.match(r"^signal\s+[A-Za-z_]\w*", code):
        return MemberEvent(line, "signal", 3, source)
    if re.match(r"^function\s+[A-Za-z_]\w*\s*\(", code):
        return MemberEvent(line, "function", 4, source)
    if re.match(r"^states\s*:", code):
        return MemberEvent(line, "states", 7, source)
    if re.match(r"^transitions\s*:", code):
        return MemberEvent(line, "transitions", 8, source)
    if re.match(r"^Behavior\s+on\s+", code):
        return MemberEvent(line, "behavior", None, source)
    if CHILD_RE.match(code):
        return MemberEvent(line, "child", 6, source)
    if ASSIGNMENT_RE.match(code) or GROUPED_PROPERTY_RE.match(code):
        return MemberEvent(line, "assignment", 5, source)
    return None


def _current_object(stack: Sequence[Frame]) -> ObjectContext | None:
    if stack and stack[-1].kind == "object":
        return stack[-1].context
    return None


def _is_object_brace(masked_line: str, column: int) -> bool:
    return OBJECT_PREFIX_RE.search(masked_line[:column]) is not None


def _pop_frame(stack: list[Frame], opener: str) -> None:
    if stack and stack[-1].opener == opener:
        stack.pop()


def _process_delimiters(
    masked_line: str,
    stack: list[Frame],
    contexts: list[ObjectContext],
    line_member: MemberEvent | None,
) -> None:
    linked_member = False
    for token in TOKEN_RE.finditer(masked_line):
        value = token.group(0)
        if value == "{":
            if _is_object_brace(masked_line, token.start()):
                context = ObjectContext()
                contexts.append(context)
                stack.append(Frame("{", "object", context))
                if line_member is not None and not linked_member:
                    line_member.target_context = context
                    linked_member = True
            else:
                stack.append(Frame("{", "block"))
        elif value == "[":
            stack.append(Frame("[", "array"))
        elif value == "(":
            stack.append(Frame("(", "paren"))
        elif value == "}":
            _pop_frame(stack, "{")
        elif value == "]":
            _pop_frame(stack, "[")
        elif value == ")":
            _pop_frame(stack, "(")


def _parse_member_contexts(
    code_lines: Sequence[str], source_lines: Sequence[str]
) -> list[ObjectContext]:
    stack: list[Frame] = []
    contexts: list[ObjectContext] = []
    for number, (masked_line, source) in enumerate(zip(code_lines, source_lines), start=1):
        context = _current_object(stack)
        code = masked_line.strip()
        member = None if code.startswith("}") else _classify_member(code, source, number)
        if context is not None and member is not None:
            context.members.append(member)
            if member.category == "id":
                context.id_name = member.alias_target
        _process_delimiters(masked_line, stack, contexts, member if context else None)
    return contexts


def _alias_near_target(members: Sequence[MemberEvent], index: int) -> bool:
    target = members[index].alias_target
    if target is None:
        return False
    for step in (-1, 1):
        cursor = index + step
        while (
            0 <= cursor < len(members)
            and members[cursor].category == "property"
            and members[cursor].alias_target is not None
        ):
            cursor += step
        if 0 <= cursor < len(members):
            context = members[cursor].target_context
            if context is not None and context.id_name == target:
                return True
    return False


def _context_order_violations(
    context: ObjectContext, path: PurePosixPath
) -> list[Violation]:
    violations: list[Violation] = []
    highest_rank = 0
    for index, member in enumerate(context.members):
        if member.rank is None:
            continue
        if member.rank < highest_rank:
            if member.category == "property" and _alias_near_target(context.members, index):
                continue
            message = f"{member.category} member violates required declaration order"
            violations.append(
                _violation(path, member.line, "QML008", message, member.source)
            )
        highest_rank = max(highest_rank, member.rank)
    return violations


def _scan_member_order(
    code_lines: Sequence[str], source_lines: Sequence[str], path: PurePosixPath
) -> list[Violation]:
    if _is_data_resource(path):
        return []
    violations: list[Violation] = []
    for context in _parse_member_contexts(code_lines, source_lines):
        violations.extend(_context_order_violations(context, path))
    return violations


def scan_text(text: str, path: PurePosixPath) -> list[Violation]:
    raw_lines = text.splitlines()
    code_lines = _sanitize_qml(text, mask_strings=True).splitlines()
    array_code_lines = _sanitize_qml(
        text, mask_strings=True, mark_values=True
    ).splitlines()
    source_lines = _sanitize_qml(text, mask_strings=False).splitlines()
    analysis = analyze_color_dataflow(text, is_qml=True)
    violations = _scan_imports_and_theme(code_lines, source_lines, path)
    violations.extend(_scan_declarations(code_lines, source_lines, path))
    violations.extend(_scan_sections(raw_lines, path))
    violations.extend(
        _violation(
            path, number, "QML014", "line comment swallows executable statement", source
        )
        for number, source in commented_executable_lines(text, code_lines)
    )
    violations.extend(
        _scan_style_literals(
            code_lines, source_lines, array_code_lines, analysis.numeric_lines, path
        )
    )
    violations.extend(_scan_color_dataflow(text, path, analysis.findings))
    violations.extend(_scan_member_order(code_lines, source_lines, path))
    return sorted(violations, key=lambda item: (item.path.as_posix(), item.line, item.rule))


def scan_source_text(
    text: str,
    source_path: PurePosixPath,
    violation_path: PurePosixPath | None = None,
) -> list[Violation]:
    if source_path.suffix == ".qml":
        violations = scan_text(text, source_path)
    elif source_path.suffix == ".js":
        violations = _scan_javascript_style_literals(text, source_path)
    else:
        return []
    target_path = violation_path or source_path
    if target_path == source_path:
        return violations
    return [
        Violation(target_path, item.line, item.rule, item.message, item.source)
        for item in violations
    ]


def scan_repository(root: Path) -> list[Violation]:
    return _scan_repository(root, scan_source_text)


def scan_changed(root: Path, base: str) -> ChangedScanResult[Violation]:
    return _scan_changed(root, base, scan_source_text)
