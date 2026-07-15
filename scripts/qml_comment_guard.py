# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""High-confidence swallowed-line-comment guard. 高置信度注释吞语句护栏。"""

from __future__ import annotations

import re
from typing import Sequence

if __package__:
    from .qml_lexer import line_comment_lines
else:
    from qml_lexer import line_comment_lines


LINE_COMMENT_RE = re.compile(r"^\s*//(?P<body>.*)$")
COMMENT_SWALLOWED_RE = re.compile(
    r"(?P<gap>[ \t]{2,})(?P<statement>"
    r"(?P<structural>"
    r"function\s+[A-Za-z_$]\w*\s*\([^{}]*\)\s*\{"
    r"|(?:if|for|while|switch|catch)\s*\([^{}]*\)\s*\{"
    r"|(?:try|else|finally)\s*\{"
    r"|(?:(?:readonly|required|default)\s+)*property\s+"
    r"(?:alias|[A-Za-z_$]\w*(?:<[^>]+>)?)\s+[A-Za-z_$]\w*\s*:"
    r"|signal\s+[A-Za-z_$]\w*\s*\("
    r")"
    r"|(?P<lhs>[A-Za-z_$]\w*(?:\.[A-Za-z_$]\w*)*)\s*"
    r"(?:=(?!=|>)|\+=|-=|\*=|/=)\s*\S.*$"
    r")"
)
PROPERTY_DECLARATION_RE = re.compile(
    r"^(?:(?:default|required|readonly)\s+)*property\s+"
    r"(?:alias|[A-Za-z_]\w*(?:<[^>]+>)?)\s+([A-Za-z_]\w*)"
)
ID_DECLARATION_RE = re.compile(r"^id\s*:\s*([A-Za-z_]\w*)")
LOCAL_DECLARATION_RE = re.compile(r"\b(?:var|let|const)\s+([A-Za-z_$]\w*)")
QML_BUILTIN_ASSIGNMENTS = frozenset(
    {
        "activeFocusOnTab", "clip", "color", "enabled", "focus", "height",
        "implicitHeight", "implicitWidth", "loading", "opacity", "parent",
        "rotation", "running", "scale", "state", "text", "visible", "width",
        "x", "y", "z",
    }
)
QML_BUILTIN_OBJECTS = frozenset({"Layout", "anchors", "border", "font", "layer"})


def _declared_names(code_lines: Sequence[str]) -> set[str]:
    names: set[str] = set()
    for code in code_lines:
        stripped = code.strip()
        if match := PROPERTY_DECLARATION_RE.match(stripped):
            names.add(match.group(1))
        if match := ID_DECLARATION_RE.match(stripped):
            names.add(match.group(1))
        names.update(LOCAL_DECLARATION_RE.findall(code))
    return names


def commented_executable_lines(
    text: str, code_lines: Sequence[str]
) -> tuple[tuple[int, str], ...]:
    """Return actual // comments that swallow executable syntax. 返回吞掉语句的真实行注释。"""
    declared_names = _declared_names(code_lines)
    actual_comments = line_comment_lines(text)
    findings: list[tuple[int, str]] = []
    for number, source in enumerate(text.splitlines(), start=1):
        if number not in actual_comments:
            continue
        line_match = LINE_COMMENT_RE.match(source)
        if not line_match:
            continue
        body = line_match.group("body")
        match = COMMENT_SWALLOWED_RE.search(body)
        if not match or not body[:match.start()].strip():
            continue
        if not match.group("structural"):
            lhs = match.group("lhs")
            base, leaf = lhs.split(".", 1)[0], lhs.rsplit(".", 1)[-1]
            if (
                base not in declared_names
                and base not in QML_BUILTIN_OBJECTS
                and leaf not in declared_names
                and leaf not in QML_BUILTIN_ASSIGNMENTS
                and not leaf.startswith("_")
            ):
                continue
        findings.append((number, source))
    return tuple(findings)
