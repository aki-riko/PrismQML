# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Performance budgets for primitive color flow. 基础颜色流性能预算。"""

from time import perf_counter

import scripts._qml_lint.qml_color_dataflow as color_dataflow
from scripts._qml_lint.qml_color_dataflow import propagated_color_findings


def _timed_flow(source: str) -> tuple[int, float]:
    start = perf_counter()
    findings = propagated_color_findings(source, is_qml=False)
    return len(findings), perf_counter() - start


def test_non_candidate_source_skips_symbol_index(monkeypatch):
    def unexpected_symbol_index(*args, **kwargs):
        raise AssertionError("non-candidate source reached the symbol index")

    monkeypatch.setattr(color_dataflow, "build_symbol_index", unexpected_symbol_index)

    assert propagated_color_findings(
        'function fallbackColors() { return ["red"] }', is_qml=False
    ) == ()


def test_large_color_flow_stays_within_linear_budgets():
    color_source = "\n".join(
        f'const color{index} = "red";' for index in range(6000)
    )
    color_source += "\n" + "\n".join(
        f"ctx.fillStyle = color{index};" for index in range(6000)
    )
    numeric_source = "\n".join(
        f"const alpha{index} = 0.25;" for index in range(6000)
    )
    numeric_source += "\n" + "\n".join(
        f"Qt.rgba(alpha{index}, 0, 0, 1);" for index in range(6000)
    )
    cycle_source = "\n".join(
        f"const alias{index} = alias{(index + 1) % 4000};"
        for index in range(4000)
    )
    cycle_source += "\nctx.fillStyle = alias0;\n"

    color_count, color_time = _timed_flow(color_source)
    numeric_count, numeric_time = _timed_flow(numeric_source)
    cycle_count, cycle_time = _timed_flow(cycle_source)

    assert (color_count, numeric_count, cycle_count) == (6000, 6000, 0)
    assert color_time < 12.0
    assert numeric_time < 12.0
    assert cycle_time < 5.0
