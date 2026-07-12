# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Resolve semantic owners for QML color arrays. 解析 QML 颜色数组语义所有者。"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
import heapq
import re

if __package__:
    from .qml_expression_roles import direct_result_path, expression_end
else:
    from qml_expression_roles import direct_result_path, expression_end


PROPERTY_PREFIX_RE = re.compile(
    r"(?:^|[\n;{}])\s*(?:(?:default|required|readonly)\s+)*property\s+"
    r"(?P<type>[A-Za-z_]\w*(?:\s*<\s*[^>]+\s*>)?)\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*:"
)
NAMED_PREFIX_RE = re.compile(
    r"(?:^|[\n;,{}])\s*(?:(?:const|let|var)\s+)?"
    r"(?P<name>(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\s*(?::|=(?!=|>))"
)
RETURN_TOKEN_RE = re.compile(r"\breturn\b")
FUNCTION_TOKEN_RE = re.compile(r"\bfunction\b")
METHOD_HEADER_RE = re.compile(
    r"(?:^|[\n;,{}])\s*(?:(?:async|get|set|static)\s+)*(?:\*\s*)?"
    r"(?P<name>[A-Za-z_$]\w*)\s*\("
)
ARROW_TOKEN_RE = re.compile(r"=>")
COLOR_STOP_CALL_RE = re.compile(r"\b(?:[A-Za-z_]\w*\.)*addColorStop\s*\(")
COLLECTION_SUFFIXES = (
    "color", "colors", "palette", "palettes", "swatch", "swatches",
    "colorstops",
)
COLOR_CONTEXT_NAMES = frozenset({"fillstyle", "strokestyle"})
CONTROL_METHOD_NAMES = frozenset({"catch", "for", "if", "switch", "while", "with"})
CLOSING_OPENERS = {"}": "{", "]": "[", ")": "("}
MAX_PREFIX_LENGTH = 512


@dataclass(frozen=True)
class OwnerFrame:
    """Callable or concise-arrow owner frame. 可调用或简洁箭头所有者区间。"""

    start: int
    end: int
    collection: bool


@dataclass(frozen=True)
class ColorArrayOwnerIndex:
    """Precomputed owner metadata for array starts. 数组起点的预计算所有者元数据。"""

    masked: str
    pair_ends: dict[str, dict[int, int]]
    callable_by_start: dict[int, OwnerFrame]
    arrow_by_start: dict[int, OwnerFrame]
    parameter_starts: frozenset[int]
    return_starts: tuple[int, ...]
    return_ends: tuple[int, ...]

    @classmethod
    def build(
        cls,
        masked: str,
        bracket_ends: dict[int, int],
        paren_ends: dict[int, int],
        brace_ends: dict[int, int],
    ) -> "ColorArrayOwnerIndex":
        pair_ends = {"(": paren_ends, "[": bracket_ends, "{": brace_ends}
        callable_frames, arrow_frames = _owner_frames(masked, pair_ends)
        parameter_spans = _parameter_spans(masked, paren_ends, brace_ends)
        return_matches = tuple(RETURN_TOKEN_RE.finditer(masked))
        starts = sorted(bracket_ends)
        return cls(
            masked=masked,
            pair_ends=pair_ends,
            callable_by_start=_frames_by_position(starts, callable_frames),
            arrow_by_start=_frames_by_position(starts, arrow_frames),
            parameter_starts=_positions_inside_spans(starts, parameter_spans),
            return_starts=tuple(match.start() for match in return_matches),
            return_ends=tuple(match.end() for match in return_matches),
        )

    def in_parameter(self, start: int) -> bool:
        """Return whether an array starts in parameters. 返回数组是否位于参数区。"""
        return start in self.parameter_starts

    def resolves(self, start: int, end: int, lower_bound: int) -> bool:
        """Return whether an array has a semantic color owner. 返回数组是否有颜色语义所有者。"""
        callable_frame = self.callable_by_start.get(start)
        arrow_frame = self.arrow_by_start.get(start)
        scope_start = _scope_start(lower_bound, callable_frame, arrow_frame)
        prefix = _semantic_prefix(self.masked, start, scope_start)
        if _local_owner_is_collection(prefix):
            return True
        if arrow_frame is not None:
            return arrow_frame.collection and direct_result_path(
                self.masked, arrow_frame.start, arrow_frame.end,
                start, end, self.pair_ends,
            )
        if callable_frame is None or not callable_frame.collection:
            return False
        return _return_owns_array(
            self.masked, callable_frame, start, end, self.pair_ends,
            self.return_starts, self.return_ends,
        )


def _scope_start(
    lower_bound: int,
    callable_frame: OwnerFrame | None,
    arrow_frame: OwnerFrame | None,
) -> int:
    starts = [lower_bound]
    if callable_frame is not None:
        starts.append(callable_frame.start + 1)
    if arrow_frame is not None:
        starts.append(arrow_frame.start)
    return max(starts)


def _is_collection_name(name: str) -> bool:
    candidate = name.rsplit(".", 1)[-1].casefold()
    return candidate.endswith(COLLECTION_SUFFIXES) or candidate in COLOR_CONTEXT_NAMES


def _tail_crosses_owner_boundary(
    tail: str, *, comma_boundary: bool = False
) -> bool:
    stack: list[str] = []
    for char in tail:
        if char in "{[(":
            stack.append(char)
        elif char in CLOSING_OPENERS:
            if not stack or stack[-1] != CLOSING_OPENERS[char]:
                return True
            stack.pop()
        elif not stack and (char == ";" or (comma_boundary and char == ",")):
            return True
    return "{" in stack


def _property_is_collection(prefix: str) -> bool:
    matches = list(PROPERTY_PREFIX_RE.finditer(prefix))
    if not matches:
        return False
    match = matches[-1]
    if _tail_crosses_owner_boundary(prefix[match.end():], comma_boundary=True):
        return False
    property_type = re.sub(r"\s+", "", match.group("type")).casefold()
    return property_type in {"color", "list<color>"} or _is_collection_name(
        match.group("name")
    )


def _named_value_is_collection(prefix: str) -> bool:
    for match in reversed(list(NAMED_PREFIX_RE.finditer(prefix))):
        if _tail_crosses_owner_boundary(prefix[match.end():], comma_boundary=True):
            continue
        return _is_collection_name(match.group("name"))
    return False


def _is_second_call_argument(arguments: str) -> bool:
    stack: list[str] = []
    comma_count = 0
    for char in arguments:
        if char in "{[(":
            stack.append(char)
        elif char in CLOSING_OPENERS:
            if not stack or stack[-1] != CLOSING_OPENERS[char]:
                return False
            stack.pop()
        elif char == "," and not stack:
            comma_count += 1
        elif char == ";" and not stack:
            return False
    return comma_count == 1


def _color_stop_owns_array(prefix: str) -> bool:
    return any(
        _is_second_call_argument(prefix[match.end():])
        for match in reversed(list(COLOR_STOP_CALL_RE.finditer(prefix)))
    )


def _local_owner_is_collection(prefix: str) -> bool:
    return (
        _property_is_collection(prefix)
        or _named_value_is_collection(prefix)
        or _color_stop_owns_array(prefix)
    )


def _callable_tail_is_direct(tail: str) -> bool:
    compact = "".join(tail.split())
    while compact.startswith("("):
        compact = compact[1:]
    if compact.startswith("async"):
        compact = compact.removeprefix("async")
    return not compact


def _direct_callable_owner_is_collection(prefix: str) -> bool:
    candidates: list[tuple[int, bool]] = []
    for match in PROPERTY_PREFIX_RE.finditer(prefix):
        if _callable_tail_is_direct(prefix[match.end():]):
            property_type = re.sub(r"\s+", "", match.group("type")).casefold()
            semantic = property_type in {"color", "list<color>"} or _is_collection_name(
                match.group("name")
            )
            candidates.append((match.end(), semantic))
    for match in NAMED_PREFIX_RE.finditer(prefix):
        if _callable_tail_is_direct(prefix[match.end():]):
            candidates.append((match.end(), _is_collection_name(match.group("name"))))
    return max(candidates, default=(-1, False))[1]


def _next_nonspace_index(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _previous_nonspace_index(text: str, index: int) -> int:
    current = index - 1
    while current >= 0 and text[current].isspace():
        current -= 1
    return current


def _function_header(
    masked: str, start: int, paren_ends: dict[int, int]
) -> tuple[str, int, int, int] | None:
    index = _next_nonspace_index(masked, start)
    if index < len(masked) and masked[index] == "*":
        index = _next_nonspace_index(masked, index + 1)
    name_start = index
    while index < len(masked) and (masked[index].isalnum() or masked[index] in "_$"):
        index += 1
    name = masked[name_start:index]
    index = _next_nonspace_index(masked, index)
    if index >= len(masked) or masked[index] != "(":
        return None
    parameter_end = paren_ends.get(index)
    if parameter_end is None:
        return None
    opening = _next_nonspace_index(masked, parameter_end)
    if opening >= len(masked) or masked[opening] != "{":
        return None
    return name, index, parameter_end, opening


def _function_frames(
    masked: str, paren_ends: dict[int, int], brace_ends: dict[int, int]
) -> list[OwnerFrame]:
    result: list[OwnerFrame] = []
    for match in FUNCTION_TOKEN_RE.finditer(masked):
        previous = _previous_nonspace_index(masked, match.start())
        if previous >= 0 and masked[previous] == ".":
            continue
        header = _function_header(masked, match.end(), paren_ends)
        if header is None or (end := brace_ends.get(header[3])) is None:
            continue
        name = header[0]
        prefix = _semantic_prefix(masked, match.start(), 0)
        semantic = _is_collection_name(name) if name else (
            _direct_callable_owner_is_collection(prefix)
        )
        result.append(OwnerFrame(header[3], end, semantic))
    return result


def _method_frames(
    masked: str, paren_ends: dict[int, int], brace_ends: dict[int, int]
) -> list[OwnerFrame]:
    result: list[OwnerFrame] = []
    for match in METHOD_HEADER_RE.finditer(masked):
        name = match.group("name")
        if name in CONTROL_METHOD_NAMES:
            continue
        parameter_end = paren_ends.get(match.end() - 1)
        if parameter_end is None:
            continue
        opening = _next_nonspace_index(masked, parameter_end)
        if (end := brace_ends.get(opening)) is not None:
            result.append(OwnerFrame(opening, end, _is_collection_name(name)))
    return result


def _matching_opening(
    text: str, close: int, opening: str, closing: str
) -> int | None:
    depth = 0
    for index in range(close, -1, -1):
        if text[index] == closing:
            depth += 1
        elif text[index] == opening:
            depth -= 1
            if depth == 0:
                return index
    return None


def _arrow_assignment_prefix(prefix: str) -> str:
    end = _previous_nonspace_index(prefix, len(prefix))
    if end < 0:
        return prefix
    pairs = {")": ("(", ")"), "]": ("[", "]"), "}": ("{", "}")}
    if prefix[end] in pairs:
        opening, closing = pairs[prefix[end]]
        start = _matching_opening(prefix, end, opening, closing)
        return prefix[:start] if start is not None else prefix
    start = end
    while start > 0 and (prefix[start - 1].isalnum() or prefix[start - 1] in "_$"):
        start -= 1
    return prefix[:start]


def _arrow_frames(
    masked: str, pair_ends: dict[str, dict[int, int]]
) -> tuple[list[OwnerFrame], list[OwnerFrame]]:
    block_frames: list[OwnerFrame] = []
    expression_frames: list[OwnerFrame] = []
    for match in ARROW_TOKEN_RE.finditer(masked):
        body_start = _next_nonspace_index(masked, match.end())
        prefix = _semantic_prefix(masked, match.start(), 0)
        owner_prefix = _arrow_assignment_prefix(prefix)
        semantic = _direct_callable_owner_is_collection(owner_prefix)
        if (end := pair_ends["{"].get(body_start)) is not None:
            block_frames.append(OwnerFrame(body_start, end, semantic))
            continue
        end = expression_end(
            masked, body_start, len(masked), pair_ends, comma_boundary=True
        )
        expression_frames.append(OwnerFrame(body_start, end, semantic))
    return block_frames, expression_frames


def _owner_frames(
    masked: str, pair_ends: dict[str, dict[int, int]]
) -> tuple[list[OwnerFrame], list[OwnerFrame]]:
    callable_frames = _function_frames(masked, pair_ends["("], pair_ends["{"])
    callable_frames.extend(_method_frames(masked, pair_ends["("], pair_ends["{"]))
    arrow_blocks, arrow_expressions = _arrow_frames(masked, pair_ends)
    callable_frames.extend(arrow_blocks)
    return callable_frames, arrow_expressions


def _function_parameter_spans(
    masked: str, paren_ends: dict[int, int]
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for match in FUNCTION_TOKEN_RE.finditer(masked):
        previous = _previous_nonspace_index(masked, match.start())
        if previous >= 0 and masked[previous] == ".":
            continue
        header = _function_header(masked, match.end(), paren_ends)
        if header is not None:
            result.append((header[1], header[2]))
    return result


def _method_parameter_spans(
    masked: str,
    paren_ends: dict[int, int],
    brace_ends: dict[int, int],
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for match in METHOD_HEADER_RE.finditer(masked):
        if match.group("name") in CONTROL_METHOD_NAMES:
            continue
        start = match.end() - 1
        end = paren_ends.get(start)
        if end is not None and _next_nonspace_index(masked, end) in brace_ends:
            result.append((start, end))
    return result


def _arrow_parameter_spans(
    masked: str, paren_ends: dict[int, int]
) -> list[tuple[int, int]]:
    return [
        (start, end)
        for start, end in paren_ends.items()
        if masked.startswith("=>", _next_nonspace_index(masked, end))
    ]


def _parameter_spans(
    masked: str,
    paren_ends: dict[int, int],
    brace_ends: dict[int, int],
) -> list[tuple[int, int]]:
    result = _function_parameter_spans(masked, paren_ends)
    result.extend(_method_parameter_spans(masked, paren_ends, brace_ends))
    result.extend(_arrow_parameter_spans(masked, paren_ends))
    return result


def _frames_by_position(
    positions: list[int], frames: list[OwnerFrame]
) -> dict[int, OwnerFrame]:
    ordered = sorted(frames, key=lambda frame: (frame.start, -frame.end))
    active: list[tuple[int, int, int, OwnerFrame]] = []
    result: dict[int, OwnerFrame] = {}
    cursor = 0
    for position in positions:
        while cursor < len(ordered) and ordered[cursor].start <= position:
            frame = ordered[cursor]
            heapq.heappush(active, (-frame.start, frame.end, cursor, frame))
            cursor += 1
        while active and active[0][1] <= position:
            heapq.heappop(active)
        if active:
            result[position] = active[0][3]
    return result


def _positions_inside_spans(
    positions: list[int], spans: list[tuple[int, int]]
) -> frozenset[int]:
    ordered = sorted(spans)
    active_ends: list[int] = []
    result: set[int] = set()
    cursor = 0
    for position in positions:
        while cursor < len(ordered) and ordered[cursor][0] < position:
            heapq.heappush(active_ends, ordered[cursor][1])
            cursor += 1
        while active_ends and active_ends[0] <= position:
            heapq.heappop(active_ends)
        if active_ends:
            result.add(position)
    return frozenset(result)


def _return_owns_array(
    text: str, frame: OwnerFrame, array_start: int, array_end: int,
    pair_ends: dict[str, dict[int, int]], return_starts: tuple[int, ...],
    return_ends: tuple[int, ...],
) -> bool:
    cursor = bisect_left(return_starts, array_start) - 1
    while cursor >= 0 and return_starts[cursor] > frame.start:
        return_start, return_end = return_starts[cursor], return_ends[cursor]
        previous = _previous_nonspace_index(text, return_start)
        if previous >= 0 and text[previous] == ".":
            cursor -= 1
            continue
        tail = text[return_end:array_start]
        if tail.lstrip().startswith(":"):
            cursor -= 1
            continue
        first_newline = tail.find("\n")
        if first_newline >= 0 and not tail[:first_newline].strip():
            return False
        result_end = expression_end(
            text, return_end, frame.end - 1, pair_ends, comma_boundary=False
        )
        if array_start >= result_end:
            cursor -= 1
            continue
        return direct_result_path(
            text, return_end, result_end,
            array_start, array_end, pair_ends,
        )
    return False


def _has_owner_hint(prefix: str) -> bool:
    return bool(
        PROPERTY_PREFIX_RE.search(prefix)
        or NAMED_PREFIX_RE.search(prefix)
        or COLOR_STOP_CALL_RE.search(prefix)
        or RETURN_TOKEN_RE.search(prefix)
    )


def _semantic_prefix(masked: str, start: int, lower_bound: int) -> str:
    short_start = max(lower_bound, start - MAX_PREFIX_LENGTH)
    prefix = masked[short_start:start]
    if short_start == lower_bound or _has_owner_hint(prefix):
        return prefix
    return masked[lower_bound:start]
