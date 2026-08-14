# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Primitive immutable color values. 基础不可变颜色值。"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum
import re

if __package__:
    from .qml_color_constructors import is_fixed_numeric_expression
    from .qml_color_contexts import iter_color_literals
    from .qml_expression_roles import direct_result_path, expression_end
    from .qml_scope_index import (
        IDENTIFIER_RE,
        Scope,
        ScopeKind,
        matching_ends,
        next_nonspace,
        scope_positions,
    )
else:
    from qml_color_constructors import is_fixed_numeric_expression
    from qml_color_contexts import iter_color_literals
    from qml_expression_roles import direct_result_path, expression_end
    from qml_scope_index import (
        IDENTIFIER_RE,
        Scope,
        ScopeKind,
        matching_ends,
        next_nonspace,
        scope_positions,
    )


CONST_START_RE = re.compile(r"(?<![\w$])const\b")
READONLY_PROPERTY_RE = re.compile(
    r"(?<![\w$])(?:(?:default|required)\s+)*readonly\s+property\s+"
    r"(?P<type>[A-Za-z_]\w*(?:\s*<\s*[^>]+\s*>)?)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*:"
)
FOR_HEADER_RE = re.compile(r"\bfor\s*\(")
MAX_BINDINGS = 12000


class ValueKind(Enum):
    COLOR = "color"
    NUMBER = "number"
    ALIAS = "alias"


@dataclass(frozen=True)
class Origin:
    start: int
    end: int
    line: int


@dataclass(frozen=True)
class RawValue:
    kind: ValueKind
    origins: tuple[Origin, ...] = ()
    alias: str | None = None
    alias_position: int | None = None


@dataclass(frozen=True)
class Binding:
    binding_id: int
    name: str
    scope_id: int
    declaration_kind: str
    name_start: int
    value_start: int
    value_end: int
    raw_value: RawValue


@dataclass(frozen=True)
class BindingSpec:
    declaration_kind: str
    name: str
    name_start: int
    value_start: int
    value_end: int | None = None


def _direct_alias(expression: str) -> tuple[str, int] | None:
    candidate = expression.strip()
    while candidate.startswith("(") and candidate.endswith(")"):
        if matching_ends(candidate, "(", ")").get(0) != len(candidate):
            break
        candidate = candidate[1:-1].strip()
    while candidate.startswith("await "):
        candidate = candidate[6:].strip()
    if IDENTIFIER_RE.fullmatch(candidate) is None:
        return None
    return candidate, expression.find(candidate)


def _color_origins(
    source: str,
    expression_view: str,
    start: int,
    end: int,
    pairs: dict[str, dict[int, int]],
    starts: list[int],
) -> tuple[Origin, ...]:
    result: list[Origin] = []
    for match in iter_color_literals(source[start:end]):
        literal_start = start + match.start()
        literal_end = start + match.end()
        if direct_result_path(
            expression_view, start, end, literal_end - 1, literal_end, pairs
        ):
            result.append(Origin(
                literal_start, literal_end, bisect_right(starts, literal_start)
            ))
    return tuple(result)


def _raw_value(
    source: str,
    expression_view: str,
    start: int,
    end: int,
    pairs: dict[str, dict[int, int]],
    starts: list[int],
) -> RawValue | None:
    origins = _color_origins(source, expression_view, start, end, pairs, starts)
    if origins:
        return RawValue(ValueKind.COLOR, origins=origins)
    if is_fixed_numeric_expression(source[start:end]):
        return RawValue(ValueKind.NUMBER)
    alias = _direct_alias(source[start:end])
    if alias is None:
        return None
    return RawValue(ValueKind.ALIAS, alias=alias[0], alias_position=start + alias[1])


def _for_header_spans(
    masked: str, pairs: dict[str, dict[int, int]]
) -> tuple[tuple[int, int], ...]:
    result: list[tuple[int, int]] = []
    for match in FOR_HEADER_RE.finditer(masked):
        opening = match.end() - 1
        end = pairs["("].get(opening)
        if end is not None:
            result.append((opening, end))
    return tuple(result)


def _inside_spans(position: int, spans: tuple[tuple[int, int], ...]) -> bool:
    return any(start < position < end for start, end in spans)


def _const_specs(
    expression_view: str, pairs: dict[str, dict[int, int]]
) -> list[BindingSpec]:
    result: list[BindingSpec] = []
    for declaration in CONST_START_RE.finditer(expression_view):
        cursor = next_nonspace(expression_view, declaration.end())
        while (name_match := IDENTIFIER_RE.match(expression_view, cursor)) is not None:
            operator = next_nonspace(expression_view, name_match.end())
            if operator >= len(expression_view) or expression_view[operator] != "=":
                break
            if expression_view.startswith(("==", "=>"), operator):
                break
            value_start = operator + 1
            value_end = expression_end(
                expression_view, value_start, len(expression_view), pairs,
                comma_boundary=True,
            )
            result.append(BindingSpec(
                "const", name_match.group(), name_match.start(), value_start, value_end
            ))
            boundary = next_nonspace(expression_view, value_end)
            if boundary >= len(expression_view) or expression_view[boundary] != ",":
                break
            cursor = next_nonspace(expression_view, boundary + 1)
    return result


def _readonly_specs(masked: str) -> list[BindingSpec]:
    return [
        BindingSpec("readonly", match.group("name"), match.start("name"), match.end())
        for match in READONLY_PROPERTY_RE.finditer(masked)
    ]


def _materialize_binding(
    item: BindingSpec,
    binding_id: int,
    scope_id: int,
    source: str,
    expression_view: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
    starts: list[int],
) -> Binding | None:
    if item.declaration_kind == "readonly" and scopes[scope_id].kind != ScopeKind.OBJECT:
        return None
    value_end = item.value_end or expression_end(
        expression_view, item.value_start, scopes[scope_id].end, pairs,
        comma_boundary=True,
    )
    value = _raw_value(source, expression_view, item.value_start, value_end, pairs, starts)
    if value is None:
        return None
    return Binding(
        binding_id, item.name, scope_id, item.declaration_kind,
        item.name_start, item.value_start, value_end, value,
    )


def build_bindings(
    source: str,
    masked: str,
    expression_view: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
    starts: list[int],
) -> tuple[Binding, ...]:
    """Build immutable primitive binding candidates. 构建不可变基础绑定候选。"""
    header_spans = _for_header_spans(masked, pairs)
    specs = [
        item for item in _const_specs(expression_view, pairs)
        if not _inside_spans(item.name_start, header_spans)
    ]
    specs.extend(_readonly_specs(masked))
    specs = sorted(specs, key=lambda item: item.name_start)[:MAX_BINDINGS]
    scope_ids = scope_positions((item.name_start for item in specs), scopes)
    result: list[Binding] = []
    for item in specs:
        scope_id = scope_ids[item.name_start]
        binding = _materialize_binding(
            item, len(result), scope_id, source, expression_view, scopes, pairs, starts
        )
        if binding is not None:
            result.append(binding)
    return tuple(result)
