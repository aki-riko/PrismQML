# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Lexical binder collection for color analysis. 颜色分析的词法绑定收集。"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import re
from typing import Iterable

if __package__:
    from .qml_expression_roles import expression_end
    from .qml_scope_index import (
        IDENTIFIER_RE,
        Scope,
        ScopeKind,
        ancestors,
        next_nonspace,
        previous_nonspace,
        scope_positions,
    )
else:
    from qml_expression_roles import expression_end
    from qml_scope_index import (
        IDENTIFIER_RE,
        Scope,
        ScopeKind,
        ancestors,
        next_nonspace,
        previous_nonspace,
        scope_positions,
    )


PROPERTY_DECLARATION_RE = re.compile(
    r"(?<![\w$])(?P<readonly>(?:(?:default|required)\s+)*readonly\s+)?"
    r"property\s+(?:alias|[A-Za-z_]\w*(?:\s*<\s*[^>]+\s*>)?)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)"
)
NAMED_BINDER_RE = re.compile(
    r"(?<![\w$])(?P<kind>function|class)\s+(?P<name>[A-Za-z_$][\w$]*)"
)
ID_BINDER_RE = re.compile(r"(?<![\w$])id\s*:\s*(?P<name>[A-Za-z_$][\w$]*)")
QML_IMPORT_ALIAS_RE = re.compile(
    r"(?m)^\s*import\b[^\n;]*\bas\s+(?P<name>[A-Za-z_$][\w$]*)"
)
JS_IMPORT_RE = re.compile(r"(?m)^\s*import\s+(?P<body>[^\n;]+)")
DEFAULT_IMPORT_RE = re.compile(
    r"^\s*(?:type\s+)?(?P<name>[A-Za-z_$][\w$]*)(?=\s*(?:,|$))"
)
NAMESPACE_IMPORT_RE = re.compile(
    r"\*\s+as\s+(?P<name>[A-Za-z_$][\w$]*)"
)
NAMED_IMPORT_RE = re.compile(r"\{(?P<body>[^{}]*)\}")
NAMED_IMPORT_ITEM_RE = re.compile(
    r"^\s*(?:type\s+)?(?P<imported>[A-Za-z_$][\w$]*)"
    r"(?:\s+as\s+(?P<local>[A-Za-z_$][\w$]*))?\s*$"
)
DECLARATION_START_RE = re.compile(r"(?<![\w$])(?P<kind>const|let|var)\b")
CATCH_RE = re.compile(r"\bcatch\s*\(")
ARROW_RE = re.compile(r"=>")


@dataclass(frozen=True)
class BinderSpec:
    name: str
    start: int
    end: int
    kind: str
    scope_id: int | None = None
    function_scoped: bool = False


@dataclass(frozen=True)
class Declaration:
    name: str
    start: int
    end: int
    scope_id: int
    kind: str
    binding_id: int | None = None


@dataclass(frozen=True)
class IntervalBlocker:
    name: str
    start: int
    end: int
    kind: str


@dataclass(frozen=True)
class IntervalIndex:
    blockers: tuple[IntervalBlocker, ...]
    starts: tuple[int, ...]
    prefix_ends: tuple[int, ...]

    def contains(self, position: int) -> bool:
        """Return whether a blocker contains a position. 返回阻断区间是否包含位置。"""
        index = bisect_right(self.starts, position) - 1
        return index >= 0 and self.prefix_ends[index] > position


@dataclass(frozen=True)
class DeclarationTable:
    declarations: dict[tuple[int, str], tuple[Declaration, ...]]
    spans: frozenset[tuple[int, int]]
    intervals: dict[str, IntervalIndex]


def _non_declaration_specs(masked: str) -> list[BinderSpec]:
    result = [
        BinderSpec(match.group("name"), *match.span("name"), "property")
        for match in PROPERTY_DECLARATION_RE.finditer(masked)
    ]
    result.extend(
        BinderSpec(match.group("name"), *match.span("name"), match.group("kind"))
        for match in NAMED_BINDER_RE.finditer(masked)
    )
    result.extend(
        BinderSpec(match.group("name"), *match.span("name"), "id")
        for match in ID_BINDER_RE.finditer(masked)
    )
    return result


def _trim_range(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _top_level_position(
    text: str,
    start: int,
    end: int,
    targets: str,
    pairs: dict[str, dict[int, int]],
) -> int | None:
    index = start
    while index < end:
        jump = pairs.get(text[index], {}).get(index)
        if jump is not None and jump <= end:
            index = jump
            continue
        if text[index] in targets:
            return index
        index += 1
    return None


def _split_ranges(
    text: str,
    start: int,
    end: int,
    pairs: dict[str, dict[int, int]],
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = start
    while cursor < end:
        comma = _top_level_position(text, cursor, end, ",", pairs)
        item_end = end if comma is None else comma
        result.append(_trim_range(text, cursor, item_end))
        if comma is None:
            break
        cursor = comma + 1
    return result


def _pattern_binders(
    masked: str,
    start: int,
    end: int,
    pairs: dict[str, dict[int, int]],
) -> list[tuple[str, int, int]]:
    start, end = _trim_range(masked, start, end)
    if start >= end:
        return []
    if masked.startswith("...", start):
        return _pattern_binders(masked, start + 3, end, pairs)
    if masked[start] in "{[" and pairs[masked[start]].get(start) == end:
        is_object = masked[start] == "{"
        result: list[tuple[str, int, int]] = []
        for item_start, item_end in _split_ranges(masked, start + 1, end - 1, pairs):
            if item_start >= item_end:
                continue
            target_start = item_start
            if is_object:
                colon = _top_level_position(masked, item_start, item_end, ":", pairs)
                target_start = item_start if colon is None else colon + 1
            equal = _top_level_position(masked, target_start, item_end, "=", pairs)
            target_end = item_end if equal is None else equal
            result.extend(_pattern_binders(masked, target_start, target_end, pairs))
        return result
    match = IDENTIFIER_RE.match(masked, start)
    if match is None or match.end() > end:
        return []
    return [(match.group(), match.start(), match.end())]


def _pattern_end(
    masked: str, start: int, pairs: dict[str, dict[int, int]]
) -> int | None:
    if start < len(masked) and masked[start] in "{[":
        return pairs[masked[start]].get(start)
    match = IDENTIFIER_RE.match(masked, start)
    return match.end() if match is not None else None


def _declaration_specs(
    masked: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
) -> list[BinderSpec]:
    matches = list(DECLARATION_START_RE.finditer(masked))
    declaration_scopes = scope_positions((match.start() for match in matches), scopes)
    result: list[BinderSpec] = []
    for match in matches:
        cursor = next_nonspace(masked, match.end())
        while (pattern_end := _pattern_end(masked, cursor, pairs)) is not None:
            for name, start, end in _pattern_binders(masked, cursor, pattern_end, pairs):
                result.append(BinderSpec(
                    name, start, end, match.group("kind"),
                    scope_id=declaration_scopes[match.start()],
                    function_scoped=match.group("kind") == "var",
                ))
            boundary = next_nonspace(masked, pattern_end)
            if boundary < len(masked) and masked[boundary] == "=":
                boundary = expression_end(
                    masked, boundary + 1, len(masked), pairs, comma_boundary=True
                )
                boundary = next_nonspace(masked, boundary)
            if boundary >= len(masked) or masked[boundary] != ",":
                break
            cursor = next_nonspace(masked, boundary + 1)
    return result


def _named_import_specs(match: re.Match[str]) -> list[BinderSpec]:
    body_match = NAMED_IMPORT_RE.search(match.group("body"))
    if body_match is None:
        return []
    result: list[BinderSpec] = []
    for start, end in _split_ranges(body_match.group("body"), 0, len(body_match.group("body")), {}):
        item = NAMED_IMPORT_ITEM_RE.fullmatch(body_match.group("body")[start:end])
        if item is None:
            continue
        group = "local" if item.group("local") is not None else "imported"
        local_start = match.start("body") + body_match.start("body") + start + item.start(group)
        result.append(BinderSpec(
            item.group(group), local_start, local_start + len(item.group(group)), "import", 0
        ))
    return result


def _import_specs(masked: str, *, is_qml: bool) -> list[BinderSpec]:
    if is_qml:
        return [
            BinderSpec(match.group("name"), *match.span("name"), "import", 0)
            for match in QML_IMPORT_ALIAS_RE.finditer(masked)
        ]
    result: list[BinderSpec] = []
    for match in JS_IMPORT_RE.finditer(masked):
        body = match.group("body")
        clause_end = re.search(r"\bfrom\b", body)
        clause = body[:clause_end.start()] if clause_end else body
        if default := DEFAULT_IMPORT_RE.search(clause):
            start = match.start("body") + default.start("name")
            result.append(BinderSpec(
                default.group("name"), start, start + len(default.group("name")),
                "import", 0,
            ))
        if namespace := NAMESPACE_IMPORT_RE.search(clause):
            start = match.start("body") + namespace.start("name")
            result.append(BinderSpec(
                namespace.group("name"), start, start + len(namespace.group("name")),
                "import", 0,
            ))
        result.extend(_named_import_specs(match))
    return result


def _parameter_specs(
    masked: str,
    start: int,
    end: int,
    scope_id: int,
    pairs: dict[str, dict[int, int]],
) -> list[BinderSpec]:
    return [
        BinderSpec(name, item_start, item_end, "parameter", scope_id)
        for range_start, range_end in _split_ranges(masked, start, end, pairs)
        for name, item_start, item_end in _pattern_binders(
            masked, range_start,
            _top_level_position(masked, range_start, range_end, "=", pairs)
            or range_end,
            pairs,
        )
    ]


def _reverse_parentheses(
    pairs: dict[str, dict[int, int]]
) -> dict[int, int]:
    return {end - 1: start for start, end in pairs["("].items()}


def _parameter_range_before(
    masked: str, position: int, reverse: dict[int, int]
) -> tuple[int, int] | None:
    previous = previous_nonspace(masked, position)
    if previous >= 1 and masked[previous - 1:previous + 1] == "=>":
        previous = previous_nonspace(masked, previous - 1)
    if previous >= 0 and masked[previous] == ")":
        opening = reverse.get(previous)
        return (opening + 1, previous) if opening is not None else None
    end = previous + 1
    while previous >= 0 and (masked[previous].isalnum() or masked[previous] in "_$"):
        previous -= 1
    return (previous + 1, end) if previous + 1 < end else None


def _function_parameter_specs(
    masked: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
) -> list[BinderSpec]:
    reverse = _reverse_parentheses(pairs)
    result: list[BinderSpec] = []
    for scope in scopes:
        if scope.kind != ScopeKind.FUNCTION:
            continue
        parameter_range = _parameter_range_before(masked, scope.start, reverse)
        if parameter_range is not None:
            result.extend(_parameter_specs(
                masked, *parameter_range, scope.scope_id, pairs
            ))
    return result


def _catch_parameter_specs(
    masked: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
) -> list[BinderSpec]:
    result: list[BinderSpec] = []
    for match in CATCH_RE.finditer(masked):
        opening = match.end() - 1
        end = pairs["("].get(opening)
        if end is None:
            continue
        brace = next_nonspace(masked, end)
        if brace >= len(masked) or masked[brace] != "{":
            continue
        scope_id = scope_positions((brace + 1,), scopes)[brace + 1]
        result.extend(_parameter_specs(
            masked, opening + 1, end - 1, scope_id, pairs
        ))
    return result


def _concise_arrow_specs(
    masked: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
) -> tuple[list[BinderSpec], list[IntervalBlocker]]:
    reverse = _reverse_parentheses(pairs)
    parameters: list[BinderSpec] = []
    blockers: list[IntervalBlocker] = []
    for match in ARROW_RE.finditer(masked):
        body_start = next_nonspace(masked, match.end())
        if body_start < len(masked) and masked[body_start] == "{":
            continue
        parameter_range = _parameter_range_before(masked, match.start(), reverse)
        if parameter_range is None:
            continue
        scope_id = scope_positions((body_start,), scopes)[body_start]
        body_end = expression_end(
            masked, body_start, scopes[scope_id].end, pairs, comma_boundary=True
        )
        specs = _parameter_specs(masked, *parameter_range, scope_id, pairs)
        parameters.extend(specs)
        blockers.extend(
            IntervalBlocker(item.name, body_start, body_end, item.kind) for item in specs
        )
    return parameters, blockers


def _function_scope(scope_id: int, scopes: tuple[Scope, ...]) -> int:
    for scope in ancestors(scope_id, scopes):
        if scope.kind in {ScopeKind.FUNCTION, ScopeKind.ROOT}:
            return scope.scope_id
    return 0


def _scope_for_spec(
    item: BinderSpec,
    dynamic_scopes: dict[int, int],
    scopes: tuple[Scope, ...],
) -> int:
    scope_id = item.scope_id if item.scope_id is not None else dynamic_scopes[item.start]
    return _function_scope(scope_id, scopes) if item.function_scoped else scope_id


def _indexed_declarations(
    specs: Iterable[BinderSpec],
    eligible: dict[tuple[int, int], int],
    scopes: tuple[Scope, ...],
) -> tuple[dict[tuple[int, str], tuple[Declaration, ...]], frozenset[tuple[int, int]]]:
    items = list(specs)
    dynamic = [item for item in items if item.scope_id is None]
    dynamic_scopes = scope_positions((item.start for item in dynamic), scopes)
    grouped: dict[tuple[int, str], list[Declaration]] = {}
    seen: set[tuple[str, int, int, int]] = set()
    for item in items:
        scope_id = _scope_for_spec(item, dynamic_scopes, scopes)
        key = (item.name, item.start, item.end, scope_id)
        if key in seen:
            continue
        seen.add(key)
        declaration = Declaration(
            item.name, item.start, item.end, scope_id, item.kind,
            eligible.get((item.start, item.end)),
        )
        grouped.setdefault((scope_id, item.name), []).append(declaration)
    return (
        {key: tuple(value) for key, value in grouped.items()},
        frozenset((item.start, item.end) for item in items),
    )


def _interval_index(
    blockers: Iterable[IntervalBlocker],
) -> dict[str, IntervalIndex]:
    grouped: dict[str, list[IntervalBlocker]] = {}
    for blocker in blockers:
        grouped.setdefault(blocker.name, []).append(blocker)
    result: dict[str, IntervalIndex] = {}
    for key, value in grouped.items():
        ordered = tuple(sorted(value, key=lambda item: item.start))
        maximum = 0
        prefix: list[int] = []
        for item in ordered:
            maximum = max(maximum, item.end)
            prefix.append(maximum)
        result[key] = IntervalIndex(
            ordered, tuple(item.start for item in ordered), tuple(prefix)
        )
    return result


def build_declaration_table(
    masked: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
    eligible: dict[tuple[int, int], tuple[int, str, int]],
    *,
    is_qml: bool,
) -> DeclarationTable:
    """Build scope-aware lexical declarations. 构建作用域感知的词法声明。"""
    specs = _non_declaration_specs(masked)
    specs.extend(_declaration_specs(masked, scopes, pairs))
    specs.extend(
        BinderSpec(name, start, end, "candidate", scope_id)
        for (start, end), (_, name, scope_id) in eligible.items()
    )
    specs.extend(_import_specs(masked, is_qml=is_qml))
    specs.extend(_function_parameter_specs(masked, scopes, pairs))
    specs.extend(_catch_parameter_specs(masked, scopes, pairs))
    arrow_specs, blockers = _concise_arrow_specs(masked, scopes, pairs)
    binding_ids = {span: item[0] for span, item in eligible.items()}
    declarations, spans = _indexed_declarations(specs, binding_ids, scopes)
    spans = spans.union((item.start, item.end) for item in arrow_specs)
    return DeclarationTable(declarations, spans, _interval_index(blockers))
