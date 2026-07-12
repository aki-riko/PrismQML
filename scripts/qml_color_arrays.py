# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Detect direct color literals in semantic arrays. 检测语义数组中的直接颜色字面量。"""

from __future__ import annotations

from bisect import bisect_left, bisect_right

if __package__:
    from .qml_color_array_owners import ColorArrayOwnerIndex
    from .qml_color_contexts import iter_color_literals
else:
    from qml_color_array_owners import ColorArrayOwnerIndex
    from qml_color_contexts import iter_color_literals


CLOSING_OPENERS = {"}": "{", "]": "[", ")": "("}
ARRAY_PREFIX_WORDS = frozenset({"await", "return"})


def _normalize_views(masked: str, quoted: str) -> tuple[str, str] | None:
    masked_result = "\n".join(masked.splitlines())
    quoted_result = "\n".join(quoted.splitlines())
    if len(masked_result) != len(quoted_result):
        return None
    return masked_result, quoted_result


def _matching_ends(text: str, opening: str, closing: str) -> dict[int, int]:
    stack: list[int] = []
    result: dict[int, int] = {}
    for index, char in enumerate(text):
        if char == opening:
            stack.append(index)
        elif char == closing and stack:
            result[stack.pop()] = index + 1
    return result


def _previous_nonspace_index(text: str, index: int) -> int:
    current = index - 1
    while current >= 0 and text[current].isspace():
        current -= 1
    return current


def _previous_token(masked: str, index: int) -> str:
    end = _previous_nonspace_index(masked, index)
    if end < 0:
        return ""
    if not (masked[end].isalnum() or masked[end] in "_$"):
        return masked[end]
    start = end
    while start > 0 and (
        masked[start - 1].isalnum() or masked[start - 1] in "_$"
    ):
        start -= 1
    return masked[start : end + 1]


def _ends_with_quoted_value(quoted: str, index: int) -> bool:
    previous = _previous_nonspace_index(quoted, index)
    return previous >= 0 and quoted[previous] in "'\"`"


def _is_spread_before(masked: str, index: int) -> bool:
    previous = _previous_nonspace_index(masked, index)
    return previous >= 2 and masked[previous - 2 : previous + 1] == "..."


def _is_array_literal_open(masked: str, quoted: str, index: int) -> bool:
    token = _previous_token(masked, index)
    if not token or token in ARRAY_PREFIX_WORDS or _is_spread_before(masked, index):
        return True
    if _ends_with_quoted_value(quoted, index):
        return False
    previous = token[-1]
    return not (previous.isalnum() or previous in "_$)]}./")


def _is_call_parenthesis(masked: str, quoted: str, index: int) -> bool:
    if _is_spread_before(masked, index):
        return False
    if _ends_with_quoted_value(quoted, index):
        return True
    token = _previous_token(masked, index)
    if not token:
        return False
    previous = token[-1]
    return previous.isalnum() or previous in "_$)]}./"


def _context_blocks_literal(
    masked: str, quoted: str, index: int, opener: str
) -> bool:
    if opener == "{":
        return True
    if opener == "(":
        return _is_call_parenthesis(masked, quoted, index)
    return not _is_array_literal_open(masked, quoted, index)


def _context_depths_at(
    masked: str, quoted: str, positions: list[int]
) -> dict[int, tuple[int, int]]:
    targets = set(positions)
    result: dict[int, tuple[int, int]] = {}
    stack: list[tuple[str, bool, bool]] = []
    blocked_depth = 0
    index_depth = 0
    for index, char in enumerate(masked):
        if index in targets:
            result[index] = blocked_depth, index_depth
        if char in "{[(":
            blocked = _context_blocks_literal(masked, quoted, index, char)
            indexed = char == "[" and blocked
            stack.append((char, blocked, indexed))
            blocked_depth += int(blocked)
            index_depth += int(indexed)
        elif char in CLOSING_OPENERS and stack:
            opener, blocked, indexed = stack[-1]
            if opener == CLOSING_OPENERS[char]:
                stack.pop()
                blocked_depth -= int(blocked)
                index_depth -= int(indexed)
    return result


def _literal_positions_by_depth(
    masked: str, quoted: str
) -> dict[int, list[int]]:
    matches = list(iter_color_literals(quoted, allow_array_items=True))
    starts = [match.start() for match in matches]
    contexts = _context_depths_at(masked, quoted, starts)
    result: dict[int, list[int]] = {}
    for start in starts:
        depth = contexts.get(start, (0, 0))[0]
        result.setdefault(depth, []).append(start)
    return result


def _line_starts(text: str) -> list[int]:
    return [0, *(index + 1 for index, char in enumerate(text) if char == "\n")]


def _array_literal_lines(
    start: int,
    end: int,
    depth: int,
    positions_by_depth: dict[int, list[int]],
    line_starts: list[int],
) -> set[int]:
    positions = positions_by_depth.get(depth, [])
    first = bisect_left(positions, start + 1)
    last = bisect_left(positions, end - 1)
    return {
        bisect_right(line_starts, position)
        for position in positions[first:last]
    }


def _is_covered_array(
    start: int,
    end: int,
    active_arrays: list[tuple[int, int, int]],
    array_depths: dict[int, int],
    owners: ColorArrayOwnerIndex,
) -> bool:
    if not active_arrays:
        return False
    parent_start, _, parent_depth = active_arrays[-1]
    if array_depths.get(start, 0) == parent_depth:
        return True
    return not owners.resolves(start, end, parent_start + 1)


def _is_reportable_array(
    masked: str,
    quoted: str,
    start: int,
    end: int,
    active_arrays: list[tuple[int, int, int]],
    array_depths: dict[int, int],
    array_contexts: dict[int, tuple[int, int]],
    owners: ColorArrayOwnerIndex,
) -> bool:
    if owners.in_parameter(start):
        return False
    if _is_covered_array(
        start, end, active_arrays, array_depths, owners
    ):
        return False
    inside_index = array_contexts.get(start, (0, 0))[1] > 0
    return bool(
        not inside_index
        and _is_array_literal_open(masked, quoted, start)
        and owners.resolves(start, end, 0)
    )


def _scan_array_lines(
    masked: str,
    quoted: str,
    bracket_ends: dict[int, int],
    owners: ColorArrayOwnerIndex,
) -> set[int]:
    line_starts = _line_starts(quoted)
    array_contexts = _context_depths_at(masked, quoted, list(bracket_ends))
    array_depths = {
        position: depths[0] for position, depths in array_contexts.items()
    }
    literal_positions = _literal_positions_by_depth(masked, quoted)
    result: set[int] = set()
    active_arrays: list[tuple[int, int, int]] = []
    for start, end in sorted(bracket_ends.items()):
        while active_arrays and start >= active_arrays[-1][1]:
            active_arrays.pop()
        if _is_reportable_array(
            masked, quoted, start, end, active_arrays,
            array_depths, array_contexts, owners,
        ):
            depth = array_depths.get(start, 0)
            result.update(
                _array_literal_lines(
                    start, end, depth, literal_positions, line_starts
                )
            )
            active_arrays.append((start, end, depth))
    return result


def color_array_literal_lines(masked_text: str, quoted_text: str) -> set[int]:
    """Return lines with direct literals in color arrays. 返回颜色数组直接字面量行。"""
    views = _normalize_views(masked_text, quoted_text)
    if views is None:
        return set()
    masked, quoted = views
    bracket_ends = _matching_ends(masked, "[", "]")
    paren_ends = _matching_ends(masked, "(", ")")
    brace_ends = _matching_ends(masked, "{", "}")
    owners = ColorArrayOwnerIndex.build(
        masked, bracket_ends, paren_ends, brace_ends
    )
    return _scan_array_lines(masked, quoted, bracket_ends, owners)
