# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Conservative QML/JavaScript brace scopes. 保守 QML/JavaScript 花括号作用域。"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable


IDENTIFIER_RE = re.compile(r"[A-Za-z_$][\w$]*")
OBJECT_PREFIX_RE = re.compile(
    r"(?:^|[:\[,(;{}])\s*(?:component\s+\w+\s*:\s*)?"
    r"[A-Z]\w*(?:\.[A-Z]\w*)*(?:\s+on\s+[\w.]+)?\s*$"
)
CONTROL_CALL_WORDS = frozenset({"catch", "for", "if", "switch", "while", "with"})


class ScopeKind(Enum):
    ROOT = "root"
    OBJECT = "object"
    FUNCTION = "function"
    BLOCK = "block"


@dataclass(frozen=True)
class Scope:
    scope_id: int
    start: int
    end: int
    parent: int | None
    kind: ScopeKind


def line_starts(text: str) -> list[int]:
    """Return normalized source line starts. 返回规范化源码行起点。"""
    return [0, *(index + 1 for index, char in enumerate(text) if char == "\n")]


def line_number(starts: list[int], position: int) -> int:
    """Return a 1-based line number. 返回从一开始的行号。"""
    return bisect_right(starts, position)


def matching_ends(text: str, opening: str, closing: str) -> dict[int, int]:
    """Return matched delimiter ends. 返回配对分隔符终点。"""
    stack: list[int] = []
    result: dict[int, int] = {}
    for index, char in enumerate(text):
        if char == opening:
            stack.append(index)
        elif char == closing and stack:
            result[stack.pop()] = index + 1
    return result


def pair_ends(text: str) -> dict[str, dict[int, int]]:
    """Return all balanced delimiter maps. 返回全部平衡分隔符映射。"""
    return {
        "(": matching_ends(text, "(", ")"),
        "[": matching_ends(text, "[", "]"),
        "{": matching_ends(text, "{", "}"),
    }


def _is_object_brace(masked: str, position: int) -> bool:
    line_start = masked.rfind("\n", 0, position) + 1
    return OBJECT_PREFIX_RE.search(masked[line_start:position]) is not None


def _word_before(text: str, position: int) -> str:
    end = previous_nonspace(text, position) + 1
    start = end
    while start > 0 and (text[start - 1].isalnum() or text[start - 1] in "_$"):
        start -= 1
    return text[start:end]


def _is_function_brace(
    masked: str, position: int, reverse_parens: dict[int, int]
) -> bool:
    previous = previous_nonspace(masked, position)
    if previous >= 1 and masked[previous - 1:previous + 1] == "=>":
        return True
    if previous < 0 or masked[previous] != ")":
        return False
    opening = reverse_parens.get(previous)
    if opening is None:
        return False
    return _word_before(masked, opening) not in CONTROL_CALL_WORDS


def build_scopes(masked: str, is_qml: bool) -> tuple[Scope, ...]:
    """Build a conservative nested scope tree. 构建保守嵌套作用域树。"""
    brace_ends = matching_ends(masked, "{", "}")
    reverse_parens = {
        end - 1: start for start, end in matching_ends(masked, "(", ")").items()
    }
    scopes = [Scope(0, 0, len(masked), None, ScopeKind.ROOT)]
    active = [0]
    for start, end in sorted(brace_ends.items()):
        while len(active) > 1 and scopes[active[-1]].end <= start:
            active.pop()
        parent = active[-1]
        if is_qml and _is_object_brace(masked, start):
            kind = ScopeKind.OBJECT
        elif _is_function_brace(masked, start, reverse_parens):
            kind = ScopeKind.FUNCTION
        else:
            kind = ScopeKind.BLOCK
        if end <= scopes[parent].end:
            scope = Scope(len(scopes), start, end, parent, kind)
            scopes.append(scope)
            active.append(scope.scope_id)
    return tuple(scopes)


def scope_positions(
    positions: Iterable[int], scopes: tuple[Scope, ...]
) -> dict[int, int]:
    """Resolve sorted positions to innermost scopes. 解析位置对应的最内层作用域。"""
    ordered = sorted(scopes[1:], key=lambda item: item.start)
    result: dict[int, int] = {}
    active = [scopes[0]]
    cursor = 0
    for position in sorted(set(positions)):
        while cursor < len(ordered) and ordered[cursor].start < position:
            scope = ordered[cursor]
            while len(active) > 1 and active[-1].end <= scope.start:
                active.pop()
            if scope.end <= active[-1].end:
                active.append(scope)
            cursor += 1
        while len(active) > 1 and active[-1].end <= position:
            active.pop()
        result[position] = active[-1].scope_id
    return result


def ancestors(scope_id: int, scopes: tuple[Scope, ...]) -> Iterable[Scope]:
    """Yield one scope and its ancestors. 迭代作用域及其祖先。"""
    current: int | None = scope_id
    while current is not None:
        scope = scopes[current]
        yield scope
        current = scope.parent


def crosses_object(
    owner_scope: int, use_scope: int, scopes: tuple[Scope, ...]
) -> bool:
    """Return whether lookup crosses a child QML object. 返回查找是否跨越子 QML 对象。"""
    for scope in ancestors(use_scope, scopes):
        if scope.scope_id == owner_scope:
            return False
        if scope.kind == ScopeKind.OBJECT:
            return True
    return True


def next_nonspace(text: str, position: int) -> int:
    """Return the next non-space position. 返回下一非空白位置。"""
    while position < len(text) and text[position].isspace():
        position += 1
    return position


def previous_nonspace(text: str, position: int) -> int:
    """Return the previous non-space position. 返回上一非空白位置。"""
    position -= 1
    while position >= 0 and text[position].isspace():
        position -= 1
    return position
