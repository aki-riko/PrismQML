# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""High-confidence primitive color data flow. 高置信基础颜色数据流。"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
import re

if __package__:
    from .qml_color_arrays import color_array_literal_findings
    from .qml_color_constructors import numeric_color_constructor_findings
    from .qml_color_context_findings import color_literal_findings
    from .qml_color_symbols import (
        RawValue,
        Reference,
        SymbolIndex,
        ValueKind,
        build_symbol_index,
    )
    from .qml_expression_roles import direct_result_path
    from .qml_lexer import sanitize_qml
    from .qml_scope_index import build_scopes, line_number, line_starts, pair_ends
else:
    from qml_color_arrays import color_array_literal_findings
    from qml_color_constructors import numeric_color_constructor_findings
    from qml_color_context_findings import color_literal_findings
    from qml_color_symbols import (
        RawValue,
        Reference,
        SymbolIndex,
        ValueKind,
        build_symbol_index,
    )
    from qml_expression_roles import direct_result_path
    from qml_lexer import sanitize_qml
    from qml_scope_index import build_scopes, line_number, line_starts, pair_ends


@dataclass(frozen=True)
class Replacement:
    reference: Reference
    kind: ValueKind
    synthetic_start: int
    synthetic_end: int


@dataclass(frozen=True)
class DataflowFinding:
    report_line: int
    report_start: int
    report_end: int
    use_line: int
    use_start: int
    use_end: int


@dataclass(frozen=True)
class ColorDataflowAnalysis:
    numeric_lines: frozenset[int]
    findings: tuple[DataflowFinding, ...]


@dataclass(frozen=True)
class SourceMap:
    replacements: tuple[Replacement, ...]
    starts: tuple[int, ...]
    cumulative_deltas: tuple[int, ...]
    numeric_prefix: tuple[int, ...]

    def original_position(self, position: int) -> int:
        """Map a synthetic position to original source. 映射合成位置到原始源码。"""
        index = bisect_right(self.starts, position) - 1
        if index < 0:
            return position
        item = self.replacements[index]
        if position < item.synthetic_end:
            return item.reference.start
        return position + self.cumulative_deltas[index]

    def has_numeric(self, start: int, end: int) -> bool:
        """Return whether a range contains numeric replacements. 返回区间是否含数值替换。"""
        left = bisect_left(self.starts, start)
        right = bisect_left(self.starts, end)
        return self.numeric_prefix[right] > self.numeric_prefix[left]


QUOTED_HEX_RE = re.compile(
    r"(?P<quote>['\"`])#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})(?P=quote)"
)
DATAFLOW_TRIGGER_RE = re.compile(r"(?<![\w$])(?:const|readonly|Qt)\b")


def _replacement_text(kind: ValueKind, index: int) -> str:
    if kind == ValueKind.COLOR:
        return f'"#{index + 1:06x}"'
    return "0"


def _synthesize(
    source: str, index: SymbolIndex
) -> tuple[str, tuple[Replacement, ...]]:
    parts: list[str] = []
    replacements: list[Replacement] = []
    source_cursor = 0
    synthetic_cursor = 0
    for number, reference in enumerate(index.references):
        prefix = source[source_cursor:reference.start]
        parts.append(prefix)
        synthetic_cursor += len(prefix)
        kind = index.resolved[reference.binding_id].kind
        replacement_text = _replacement_text(kind, number)
        parts.append(replacement_text)
        replacements.append(Replacement(
            reference, kind, synthetic_cursor, synthetic_cursor + len(replacement_text)
        ))
        synthetic_cursor += len(replacement_text)
        source_cursor = reference.end
    parts.append(source[source_cursor:])
    return "".join(parts), tuple(replacements)


def _source_map(replacements: tuple[Replacement, ...]) -> SourceMap:
    starts: list[int] = []
    deltas: list[int] = []
    numeric_prefix = [0]
    cumulative = 0
    for item in replacements:
        starts.append(item.synthetic_start)
        cumulative += (
            item.reference.end - item.reference.start
            - (item.synthetic_end - item.synthetic_start)
        )
        deltas.append(cumulative)
        numeric_prefix.append(numeric_prefix[-1] + (item.kind == ValueKind.NUMBER))
    return SourceMap(replacements, tuple(starts), tuple(deltas), tuple(numeric_prefix))


def _role_view(masked: str, replacements: tuple[Replacement, ...]) -> str:
    result = list(masked)
    for replacement in replacements:
        if replacement.kind == ValueKind.COLOR:
            result[replacement.synthetic_start:replacement.synthetic_end] = (
                "v" * (replacement.synthetic_end - replacement.synthetic_start)
            )
    return "".join(result)


def _origin_findings(
    replacement: Replacement,
    value: RawValue,
    excluded_origins: frozenset[tuple[int, int]],
) -> list[DataflowFinding]:
    return [
        DataflowFinding(
            origin.line,
            origin.start,
            origin.end,
            replacement.reference.line,
            replacement.reference.start,
            replacement.reference.end,
        )
        for origin in value.origins
        if (origin.start, origin.end) not in excluded_origins
    ]


def _direct_origin_spans(source: str, *, is_qml: bool) -> frozenset[tuple[int, int]]:
    code = sanitize_qml(source, mask_strings=True)
    quoted = sanitize_qml(source, mask_strings=False)
    array_code = sanitize_qml(source, mask_strings=True, mark_values=True)
    spans = {
        (item.start, item.end)
        for item in color_array_literal_findings(array_code, quoted)
    }
    if is_qml:
        spans.update(
            (item.start, item.end)
            for item in color_literal_findings(code.splitlines(), quoted.splitlines())
        )
    else:
        spans.update(match.span() for match in QUOTED_HEX_RE.finditer(quoted))
    return frozenset(spans)


def _context_use_findings(
    synthetic: str,
    replacements: tuple[Replacement, ...],
    index: SymbolIndex,
    excluded_origins: frozenset[tuple[int, int]],
) -> list[DataflowFinding]:
    code = sanitize_qml(synthetic, mask_strings=True)
    quoted = sanitize_qml(synthetic, mask_strings=False)
    role_code = _role_view(code, replacements)
    pairs = pair_ends(role_code)
    by_start = {item.synthetic_start: item for item in replacements}
    result: list[DataflowFinding] = []
    for finding in color_literal_findings(code.splitlines(), quoted.splitlines()):
        replacement = by_start.get(finding.start)
        if replacement is None or replacement.kind != ValueKind.COLOR:
            continue
        if not direct_result_path(
            role_code, finding.expression_start, finding.expression_end,
            finding.start, finding.end, pairs,
        ):
            continue
        result.extend(_origin_findings(
            replacement,
            index.resolved[replacement.reference.binding_id],
            excluded_origins,
        ))
    return result


def _array_use_findings(
    synthetic: str,
    replacements: tuple[Replacement, ...],
    index: SymbolIndex,
    excluded_origins: frozenset[tuple[int, int]],
) -> list[DataflowFinding]:
    code = sanitize_qml(synthetic, mask_strings=True, mark_values=True)
    quoted = sanitize_qml(synthetic, mask_strings=False)
    by_start = {item.synthetic_start: item for item in replacements}
    result: list[DataflowFinding] = []
    for finding in color_array_literal_findings(code, quoted):
        replacement = by_start.get(finding.start)
        if replacement is None or replacement.kind != ValueKind.COLOR:
            continue
        result.extend(_origin_findings(
            replacement,
            index.resolved[replacement.reference.binding_id],
            excluded_origins,
        ))
    return result


def _direct_constructor_starts(source: str) -> set[int]:
    code = sanitize_qml(source, mask_strings=True)
    quoted = sanitize_qml(source, mask_strings=False)
    return {item.start for item in numeric_color_constructor_findings(code, quoted)}


def _direct_numeric_lines(source: str, index: SymbolIndex) -> frozenset[int]:
    code = sanitize_qml(source, mask_strings=True)
    quoted = sanitize_qml(source, mask_strings=False)
    return frozenset(
        item.line
        for item in numeric_color_constructor_findings(code, quoted)
        if index.is_global_name("Qt", item.qt_start)
    )


def _numeric_finding(
    finding,
    source_map: SourceMap,
    index: SymbolIndex,
    direct_starts: set[int],
    starts: list[int],
) -> DataflowFinding | None:
    if not source_map.has_numeric(finding.start, finding.end):
        return None
    original_start = source_map.original_position(finding.start)
    if original_start in direct_starts:
        return None
    qt_start = source_map.original_position(finding.qt_start)
    if not index.is_global_name("Qt", qt_start):
        return None
    report_line = line_number(starts, original_start)
    original_end = source_map.original_position(finding.end)
    return DataflowFinding(
        report_line, original_start, original_end,
        report_line, original_start, original_end,
    )


def _numeric_use_findings(
    source: str,
    synthetic: str,
    source_map: SourceMap,
    index: SymbolIndex,
) -> list[DataflowFinding]:
    code = sanitize_qml(synthetic, mask_strings=True)
    quoted = sanitize_qml(synthetic, mask_strings=False)
    direct_starts = _direct_constructor_starts(source)
    starts = line_starts(source)
    result: list[DataflowFinding] = []
    for finding in numeric_color_constructor_findings(code, quoted):
        item = _numeric_finding(
            finding, source_map, index, direct_starts, starts
        )
        if item is not None:
            result.append(item)
    return result


def _propagated_findings(
    source: str, index: SymbolIndex, *, is_qml: bool
) -> tuple[DataflowFinding, ...]:
    if not index.references:
        return ()
    synthetic, replacements = _synthesize(source, index)
    mapping = _source_map(replacements)
    excluded_origins = _direct_origin_spans(source, is_qml=is_qml)
    findings = _context_use_findings(
        synthetic, replacements, index, excluded_origins
    )
    findings.extend(_array_use_findings(
        synthetic, replacements, index, excluded_origins
    ))
    findings.extend(_numeric_use_findings(source, synthetic, mapping, index))
    return tuple(sorted(
        findings,
        key=lambda item: (item.report_line, item.use_start, item.use_end),
    ))


def analyze_color_dataflow(text: str, *, is_qml: bool) -> ColorDataflowAnalysis:
    """Analyze direct and propagated color constructors. 分析直接及传播构色。"""
    if DATAFLOW_TRIGGER_RE.search(text) is None:
        return ColorDataflowAnalysis(frozenset(), ())
    source = "\n".join(text.splitlines())
    masked = sanitize_qml(source, mask_strings=True)
    expression_view = sanitize_qml(source, mask_strings=True, mark_values=True)
    pairs = pair_ends(expression_view)
    starts = line_starts(source)
    scopes = build_scopes(masked, is_qml)
    index = build_symbol_index(
        source, masked, expression_view, scopes, pairs, starts, is_qml=is_qml
    )
    numeric_lines = _direct_numeric_lines(source, index)
    findings = _propagated_findings(source, index, is_qml=is_qml)
    return ColorDataflowAnalysis(numeric_lines, findings)


def propagated_color_findings(
    text: str, *, is_qml: bool
) -> tuple[DataflowFinding, ...]:
    """Return high-confidence primitive color-flow findings. 返回高置信基础颜色流结果。"""
    return analyze_color_dataflow(text, is_qml=is_qml).findings
