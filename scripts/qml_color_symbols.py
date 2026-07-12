# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Scope-aware primitive color symbols. 作用域感知的基础颜色符号。"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import re

if __package__:
    from .qml_color_binders import (
        Declaration,
        DeclarationTable,
        ID_BINDER_RE,
        build_declaration_table,
    )
    from .qml_color_values import (
        Binding,
        RawValue,
        ValueKind,
        build_bindings,
    )
    from .qml_lexer import sanitize_qml
    from .qml_scope_index import (
        IDENTIFIER_RE,
        Scope,
        ScopeKind,
        ancestors,
        crosses_object,
        next_nonspace,
        previous_nonspace,
        scope_positions,
    )
else:
    from qml_color_binders import (
        Declaration,
        DeclarationTable,
        ID_BINDER_RE,
        build_declaration_table,
    )
    from qml_color_values import Binding, RawValue, ValueKind, build_bindings
    from qml_lexer import sanitize_qml
    from qml_scope_index import (
        IDENTIFIER_RE,
        Scope,
        ScopeKind,
        ancestors,
        crosses_object,
        next_nonspace,
        previous_nonspace,
        scope_positions,
    )


QUALIFIED_RE = re.compile(
    r"(?<![\w$])(?P<owner>[A-Za-z_$][\w$]*)\s*\.\s*"
    r"(?P<name>[A-Za-z_$][\w$]*)"
)
STATIC_BRACKET_RE = re.compile(
    r"(?<![\w$])(?P<owner>[A-Za-z_$][\w$]*)\s*\[\s*"
    r"(?P<quote>['\"`])(?P<name>[A-Za-z_$][\w$]*)(?P=quote)\s*\]"
)
DYNAMIC_BRACKET_RE = re.compile(
    r"(?<![\w$])(?P<owner>[A-Za-z_$][\w$]*)\s*\["
)
FOR_WRITE_RE = re.compile(
    r"\bfor\s*\([^;)]*?(?P<name>[A-Za-z_$][\w$]*)\s+(?:of|in)\b"
)
ASSIGNMENT_OPERATORS = (
    ">>>=", "<<=", ">>=", "**=", "&&=", "||=", "??=", "+=", "-=", "*=",
    "/=", "%=", "&=", "|=", "^=", "=",
)
MAX_REFERENCES = 24000
MAX_ALIAS_DEPTH = 128


@dataclass(frozen=True)
class Reference:
    start: int
    end: int
    line: int
    binding_id: int


@dataclass(frozen=True)
class SymbolIndex:
    scopes: tuple[Scope, ...]
    scope_starts: tuple[int, ...]
    scope_ids: tuple[int, ...]
    bindings: tuple[Binding, ...]
    table: DeclarationTable
    resolved: dict[int, RawValue]
    references: tuple[Reference, ...]

    def scope_at(self, position: int) -> int:
        """Return the innermost containing scope. 返回最内层包含作用域。"""
        item = bisect_right(self.scope_starts, position - 1) - 1
        scope_id = self.scope_ids[max(item, 0)]
        while not (self.scopes[scope_id].start < position < self.scopes[scope_id].end):
            parent = self.scopes[scope_id].parent
            if parent is None:
                return 0
            scope_id = parent
        return scope_id

    def is_global_name(self, name: str, position: int) -> bool:
        """Return whether a built-in name is unshadowed. 返回内建名称是否未被遮蔽。"""
        return not _visible_declarations(self, name, position, self.scope_at(position))


def _line_number(starts: list[int], position: int) -> int:
    return bisect_right(starts, position)


def _visible_declarations(
    index: SymbolIndex, name: str, position: int, scope_id: int
) -> tuple[Declaration, ...]:
    intervals = index.table.intervals.get(name)
    if intervals is not None and intervals.contains(position):
        return (Declaration(name, position, position, scope_id, "interval"),)
    for scope in ancestors(scope_id, index.scopes):
        declarations = index.table.declarations.get((scope.scope_id, name), ())
        if declarations:
            return declarations
    return ()


def _resolve_binding(
    index: SymbolIndex,
    name: str,
    position: int,
    scope_id: int,
    invalid: frozenset[int] = frozenset(),
    *,
    for_write: bool = False,
) -> int | None:
    declarations = _visible_declarations(index, name, position, scope_id)
    if len(declarations) != 1 or declarations[0].binding_id is None:
        return None
    binding = index.bindings[declarations[0].binding_id]
    if binding.binding_id in invalid:
        return None
    if not for_write and binding.declaration_kind == "const" and position < binding.value_end:
        return None
    if binding.declaration_kind == "readonly" and crosses_object(
        binding.scope_id, scope_id, index.scopes
    ):
        return None
    return binding.binding_id


def _is_assignment_operator(text: str, position: int) -> bool:
    return (
        any(text.startswith(operator, position) for operator in ASSIGNMENT_OPERATORS)
        and not text.startswith(("==", "=>"), position)
    )


def _write_target(masked: str, match: re.Match[str]) -> bool:
    previous = previous_nonspace(masked, match.start())
    following = next_nonspace(masked, match.end())
    if previous >= 0 and masked[previous] == ".":
        return False
    if following < len(masked) and masked[following] == ".":
        return False
    suffix = _is_assignment_operator(masked, following) or masked.startswith(("++", "--"), following)
    prefix = previous >= 1 and masked[previous - 1:previous + 1] in {"++", "--"}
    return suffix or prefix


def _visible_id_scope(
    index: SymbolIndex, owner: str, position: int, use_scope: int
) -> int | None:
    declarations = _visible_declarations(index, owner, position, use_scope)
    if len(declarations) != 1 or declarations[0].kind != "id":
        return None
    object_scope = declarations[0].scope_id
    if index.scopes[object_scope].kind != ScopeKind.OBJECT:
        return None
    return object_scope


def _qualified_target(
    index: SymbolIndex, match: re.Match[str], use_scope: int
) -> int | None:
    object_scope = _visible_id_scope(
        index, match.group("owner"), match.start("owner"), use_scope
    )
    declarations = index.table.declarations.get(
        (object_scope, match.group("name")), ()
    )
    if object_scope is None or len(declarations) != 1:
        return None
    return declarations[0].binding_id


def _bare_write_bindings(masked: str, index: SymbolIndex) -> set[int]:
    names = {binding.name for binding in index.bindings}
    matches = [match for match in IDENTIFIER_RE.finditer(masked) if match.group() in names]
    scope_ids = scope_positions((match.start() for match in matches), index.scopes)
    result: set[int] = set()
    for match in matches:
        if match.span() in index.table.spans or not _write_target(masked, match):
            continue
        target = _resolve_binding(
            index, match.group(), match.start(), scope_ids[match.start()], for_write=True
        )
        if target is not None:
            result.add(target)
    return result


def _qualified_write_bindings(masked: str, index: SymbolIndex) -> set[int]:
    matches = list(QUALIFIED_RE.finditer(masked))
    scope_ids = scope_positions((match.start() for match in matches), index.scopes)
    result: set[int] = set()
    for match in matches:
        following = next_nonspace(masked, match.end())
        previous = previous_nonspace(masked, match.start())
        suffix = _is_assignment_operator(masked, following) or masked.startswith(("++", "--"), following)
        prefix = previous >= 1 and masked[previous - 1:previous + 1] in {"++", "--"}
        if not (suffix or prefix):
            continue
        target = _qualified_target(index, match, scope_ids[match.start()])
        if target is not None:
            result.add(target)
    return result


def _static_bracket_write_bindings(
    masked: str, quoted: str, index: SymbolIndex
) -> set[int]:
    matches = [
        match for match in STATIC_BRACKET_RE.finditer(quoted)
        if masked[match.start("owner"):match.end("owner")] == match.group("owner")
    ]
    scope_ids = scope_positions((match.start() for match in matches), index.scopes)
    result: set[int] = set()
    for match in matches:
        following = next_nonspace(masked, match.end())
        previous = previous_nonspace(masked, match.start())
        suffix = _is_assignment_operator(masked, following) or masked.startswith(("++", "--"), following)
        prefix = previous >= 1 and masked[previous - 1:previous + 1] in {"++", "--"}
        if suffix or prefix:
            target = _qualified_target(index, match, scope_ids[match.start()])
            if target is not None:
                result.add(target)
    return result


def _object_binding_ids(index: SymbolIndex, object_scope: int) -> set[int]:
    return {
        declaration.binding_id
        for (scope_id, _), declarations in index.table.declarations.items()
        if scope_id == object_scope
        for declaration in declarations
        if declaration.binding_id is not None
    }


def _dynamic_bracket_write_bindings(
    masked: str,
    quoted: str,
    index: SymbolIndex,
    pairs: dict[str, dict[int, int]],
) -> set[int]:
    result: set[int] = set()
    for match in DYNAMIC_BRACKET_RE.finditer(masked):
        opening = match.end() - 1
        end = pairs["["].get(opening)
        if end is None or STATIC_BRACKET_RE.fullmatch(quoted[match.start():end]):
            continue
        following = next_nonspace(masked, end)
        previous = previous_nonspace(masked, match.start())
        suffix = _is_assignment_operator(masked, following) or masked.startswith(
            ("++", "--"), following
        )
        prefix = previous >= 1 and masked[previous - 1:previous + 1] in {"++", "--"}
        if not (suffix or prefix):
            continue
        use_scope = index.scope_at(match.start() + 1)
        object_scope = _visible_id_scope(
            index, match.group("owner"), match.start("owner"), use_scope
        )
        if object_scope is not None:
            result.update(_object_binding_ids(index, object_scope))
    return result


def _pattern_write_bindings(
    masked: str,
    index: SymbolIndex,
    pairs: dict[str, dict[int, int]],
) -> set[int]:
    result: set[int] = set()
    for opening in "[{":
        for start, end in pairs[opening].items():
            following = next_nonspace(masked, end)
            if not _is_assignment_operator(masked, following):
                continue
            if any(
                start < declaration_start < declaration_end < end
                for declaration_start, declaration_end in index.table.spans
            ):
                continue
            scope_id = index.scope_at(start + 1)
            for match in IDENTIFIER_RE.finditer(masked, start + 1, end - 1):
                target = _resolve_binding(
                    index, match.group(), match.start(), scope_id, for_write=True
                )
                if target is not None:
                    result.add(target)
    return result


def _loop_write_bindings(masked: str, index: SymbolIndex) -> set[int]:
    result: set[int] = set()
    for match in FOR_WRITE_RE.finditer(masked):
        scope_id = index.scope_at(match.start("name") + 1)
        target = _resolve_binding(
            index, match.group("name"), match.start("name"), scope_id,
            for_write=True,
        )
        if target is not None:
            result.add(target)
    return result


def _invalid_bindings(
    masked: str,
    quoted: str,
    index: SymbolIndex,
    pairs: dict[str, dict[int, int]],
) -> frozenset[int]:
    result = _bare_write_bindings(masked, index)
    result.update(_qualified_write_bindings(masked, index))
    result.update(_static_bracket_write_bindings(masked, quoted, index))
    result.update(_dynamic_bracket_write_bindings(masked, quoted, index, pairs))
    result.update(_pattern_write_bindings(masked, index, pairs))
    result.update(_loop_write_bindings(masked, index))
    return frozenset(result)


def _alias_targets(
    index: SymbolIndex, invalid: frozenset[int]
) -> dict[int, int]:
    result: dict[int, int] = {}
    for binding in index.bindings:
        value = binding.raw_value
        if value.kind != ValueKind.ALIAS or value.alias is None or value.alias_position is None:
            continue
        target = _resolve_binding(
            index, value.alias, value.alias_position,
            index.scope_at(value.alias_position + 1), invalid,
        )
        if target is not None:
            result[binding.binding_id] = target
    return result


def _resolved_values(
    bindings: tuple[Binding, ...],
    targets: dict[int, int],
    invalid: frozenset[int],
) -> dict[int, RawValue]:
    resolved = {
        item.binding_id: item.raw_value
        for item in bindings
        if item.binding_id not in invalid and item.raw_value.kind != ValueKind.ALIAS
    }
    for binding in bindings:
        if binding.binding_id in resolved or binding.binding_id in invalid:
            continue
        path: list[int] = []
        seen: set[int] = set()
        current = binding.binding_id
        while current not in resolved and current not in seen and len(path) < MAX_ALIAS_DEPTH:
            seen.add(current)
            path.append(current)
            if current not in targets:
                break
            current = targets[current]
        if current in resolved:
            for item in reversed(path):
                resolved[item] = resolved[current]
    return resolved


def _qualified_references(
    masked: str,
    starts: list[int],
    index: SymbolIndex,
    resolved: dict[int, RawValue],
) -> tuple[list[Reference], set[tuple[int, int]]]:
    matches = list(QUALIFIED_RE.finditer(masked))
    scope_ids = scope_positions((match.start() for match in matches), index.scopes)
    result: list[Reference] = []
    covered = {span for match in matches for span in (match.span("owner"), match.span("name"))}
    for match in matches:
        target = _qualified_target(index, match, scope_ids[match.start()])
        if target not in resolved:
            continue
        result.append(Reference(
            match.start(), match.end(), _line_number(starts, match.start()), target
        ))
    return result, covered


def _bare_reference(masked: str, match: re.Match[str]) -> bool:
    previous = previous_nonspace(masked, match.start())
    following = next_nonspace(masked, match.end())
    if previous >= 0 and masked[previous] == ".":
        return False
    if following < len(masked) and masked[following] in ".:(":
        return False
    return not _is_assignment_operator(masked, following)


def _references(
    masked: str,
    starts: list[int],
    index: SymbolIndex,
    resolved: dict[int, RawValue],
    invalid: frozenset[int],
) -> tuple[Reference, ...]:
    qualified, covered = _qualified_references(masked, starts, index, resolved)
    names = {item.name for item in index.bindings if item.binding_id in resolved}
    matches = [match for match in IDENTIFIER_RE.finditer(masked) if match.group() in names]
    scope_ids = scope_positions((match.start() for match in matches), index.scopes)
    result = list(qualified)
    for match in matches:
        if match.span() in index.table.spans or match.span() in covered:
            continue
        if not _bare_reference(masked, match):
            continue
        target = _resolve_binding(
            index, match.group(), match.start(), scope_ids[match.start()], invalid
        )
        if target in resolved:
            result.append(Reference(
                match.start(), match.end(), _line_number(starts, match.start()), target
            ))
        if len(result) >= MAX_REFERENCES:
            return ()
    return tuple(sorted(result, key=lambda item: item.start))


def _scope_lookup(scopes: tuple[Scope, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    ordered = sorted(scopes, key=lambda item: item.start)
    return (
        tuple(item.start for item in ordered),
        tuple(item.scope_id for item in ordered),
    )


def build_symbol_index(
    source: str,
    masked: str,
    expression_view: str,
    scopes: tuple[Scope, ...],
    pairs: dict[str, dict[int, int]],
    starts: list[int],
    *,
    is_qml: bool,
) -> SymbolIndex:
    """Build resolved high-confidence symbols. 构建已解析的高置信符号。"""
    bindings = build_bindings(source, masked, expression_view, scopes, pairs, starts)
    eligible = {
        (item.name_start, item.name_start + len(item.name)): (
            item.binding_id, item.name, item.scope_id
        )
        for item in bindings
    }
    table = build_declaration_table(masked, scopes, pairs, eligible, is_qml=is_qml)
    scope_starts, scope_ids = _scope_lookup(scopes)
    empty = SymbolIndex(scopes, scope_starts, scope_ids, bindings, table, {}, ())
    quoted = sanitize_qml(source, mask_strings=False)
    invalid = _invalid_bindings(masked, quoted, empty, pairs)
    targets = _alias_targets(empty, invalid)
    resolved = _resolved_values(bindings, targets, invalid)
    references = _references(masked, starts, empty, resolved, invalid)
    return SymbolIndex(
        scopes, scope_starts, scope_ids, bindings, table, resolved, references
    )
