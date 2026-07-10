# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Read-only PrismQML convention scanner. 只读 QML 规范扫描器。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Iterable, Sequence


QML_ROOT = PurePosixPath("prismqml/PrismQML")
QTQUICK_CONTROLS_EXCEPTIONS = {
    PurePosixPath("prismqml/PrismQML/controls/containers/Widget.qml"),
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
COLOR_LITERAL_RE = re.compile(
    r"^\s*(?:(?:(?:default|required|readonly)\s+)*property\s+color\s+\w+|"
    r"(?:color|border\.color))\s*:\s*"
    r"['\"](?:#[0-9A-Fa-f]{3,8}|transparent|white|black)['\"]"
)
METRIC_LITERAL_RE = re.compile(
    r"^\s*(?:(?:(?:default|required|readonly)\s+)*property\s+"
    r"[A-Za-z_]\w*(?:<[^>]+>)?\s+)?"
    r"(?:radius|spacing|padding|leftPadding|rightPadding|topPadding|"
    r"bottomPadding|anchors\.margins|anchors\.[A-Za-z]+Margin|"
    r"Layout\.[A-Za-z]+Margin|font\.pixelSize|duration|border\.width|"
    r"shadowLevel|shadowBlur|shadowOffsetX|shadowOffsetY)\s*:\s*"
    r"-?\d+(?:\.\d+)?\b"
)
FONT_LITERAL_RE = re.compile(r"^\s*font\.family\s*:\s*['\"]")


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


@dataclass(frozen=True)
class ChangedQmlFile:
    current_path: PurePosixPath
    base_path: PurePosixPath | None


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


@dataclass(frozen=True)
class ChangedScanResult:
    violations: tuple[Violation, ...]
    changed_files: int
    current_total: int
    base_total: int


def _blank(segment: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in segment)


def _quoted_end(text: str, start: int, quote: str) -> int:
    index = start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == quote:
            return index + 1
        index += 1
    return len(text)


def _sanitize_qml(text: str, *, mask_strings: bool) -> str:
    result: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            result.append(_blank(text[index:end]))
            index = end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = len(text) if end < 0 else end + 2
            result.append(_blank(text[index:end]))
            index = end
        elif text[index] in {'"', "'", "`"}:
            end = _quoted_end(text, index, text[index])
            segment = text[index:end]
            result.append(_blank(segment) if mask_strings else segment)
            index = end
        else:
            result.append(text[index])
            index += 1
    return "".join(result)


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
    code_lines: Sequence[str], source_lines: Sequence[str], path: PurePosixPath
) -> list[Violation]:
    if _is_data_resource(path):
        return []
    violations: list[Violation] = []
    for number, (code, source) in enumerate(zip(code_lines, source_lines), start=1):
        if COLOR_LITERAL_RE.search(source):
            violations.append(_violation(path, number, "QML010", "hardcoded color", source))
        if METRIC_LITERAL_RE.search(code):
            violations.append(_violation(path, number, "QML011", "hardcoded style metric", source))
        if FONT_LITERAL_RE.search(source):
            violations.append(_violation(path, number, "QML012", "hardcoded font family", source))
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
    source_lines = _sanitize_qml(text, mask_strings=False).splitlines()
    violations = _scan_imports_and_theme(code_lines, source_lines, path)
    violations.extend(_scan_declarations(code_lines, source_lines, path))
    violations.extend(_scan_sections(raw_lines, path))
    violations.extend(_scan_style_literals(code_lines, source_lines, path))
    violations.extend(_scan_member_order(code_lines, source_lines, path))
    return sorted(violations, key=lambda item: (item.path.as_posix(), item.line, item.rule))


def scan_repository(root: Path) -> list[Violation]:
    qml_root = root / QML_ROOT
    if not qml_root.is_dir():
        raise FileNotFoundError(f"QML root not found: {qml_root}")
    violations: list[Violation] = []
    for path in sorted(qml_root.rglob("*.qml")):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        violations.extend(scan_text(path.read_text(encoding="utf-8"), relative))
    return violations


def _run_git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def _verify_base(root: Path, base: str) -> None:
    completed = _run_git(root, ["rev-parse", "--verify", f"{base}^{{commit}}"])
    if completed.returncode != 0:
        raise RuntimeError(f"invalid git base {base}: {completed.stderr.strip()}")


def _parse_changed_line(line: str) -> ChangedQmlFile | None:
    fields = line.split("\t")
    status = fields[0]
    if status.startswith("R") and len(fields) == 3:
        return ChangedQmlFile(PurePosixPath(fields[2]), PurePosixPath(fields[1]))
    if status.startswith("M") and len(fields) == 2:
        path = PurePosixPath(fields[1])
        return ChangedQmlFile(path, path)
    if status.startswith("A") and len(fields) == 2:
        return ChangedQmlFile(PurePosixPath(fields[1]), None)
    if status.startswith("C") and len(fields) == 3:
        return ChangedQmlFile(PurePosixPath(fields[2]), None)
    return None


def _changed_qml_files(root: Path, base: str) -> list[ChangedQmlFile]:
    completed = _run_git(
        root, ["diff", "--name-status", "-M", base, "--", QML_ROOT.as_posix()]
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git diff failed")
    changed = [
        item
        for line in completed.stdout.splitlines()
        if (item := _parse_changed_line(line))
    ]
    untracked = _run_git(
        root, ["ls-files", "--others", "--exclude-standard", "--", QML_ROOT.as_posix()]
    )
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files failed")
    known = {item.current_path for item in changed}
    for line in untracked.stdout.splitlines():
        path = PurePosixPath(line)
        if path.suffix == ".qml" and path not in known:
            changed.append(ChangedQmlFile(path, None))
    return sorted(changed, key=lambda item: item.current_path.as_posix())


def _base_text(root: Path, base: str, path: PurePosixPath | None) -> str:
    if path is None:
        return ""
    completed = _run_git(root, ["show", f"{base}:{path.as_posix()}"])
    if completed.returncode != 0:
        raise RuntimeError(f"cannot read {path} from {base}: {completed.stderr.strip()}")
    return completed.stdout


def new_violations(
    current: Iterable[Violation], baseline: Iterable[Violation]
) -> list[Violation]:
    remaining = Counter(item.fingerprint() for item in baseline)
    result: list[Violation] = []
    for violation in current:
        fingerprint = violation.fingerprint()
        if remaining[fingerprint] > 0:
            remaining[fingerprint] -= 1
        else:
            result.append(violation)
    return result


def scan_changed(root: Path, base: str) -> ChangedScanResult:
    _verify_base(root, base)
    added: list[Violation] = []
    current_total = 0
    base_total = 0
    changed = _changed_qml_files(root, base)
    for item in changed:
        current_file = root / item.current_path
        current = scan_text(current_file.read_text(encoding="utf-8"), item.current_path)
        baseline = scan_text(_base_text(root, base, item.base_path), item.current_path)
        current_total += len(current)
        base_total += len(baseline)
        added.extend(new_violations(current, baseline))
    return ChangedScanResult(tuple(added), len(changed), current_total, base_total)
