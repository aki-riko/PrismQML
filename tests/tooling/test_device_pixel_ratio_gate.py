# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Device-pixel-ratio gate contracts. 设备像素比门禁合同。

The gate exists because the default offscreen runner pins the device pixel ratio to
1.0, where every physical-pixel snap is an identity. A gate that silently accepts a
factor of 1.0, or that covers no physical-pixel file, would re-open exactly the blind
spot it was built to close, so those properties are locked here.
该门禁存在的原因: 默认 offscreen 运行器把设备像素比固定为 1.0, 此时所有物理像素对齐
都是恒等操作。若门禁悄悄接受因子 1.0, 或没有覆盖任何物理像素文件, 就会重新打开它本要
消除的盲区, 因此这些性质在此锁定。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "device_pixel_ratio_gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("device_pixel_ratio_gate", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_gate_refuses_a_factor_that_cannot_break_a_one_to_one_host():
    """A factor of 1.0 leaves a 1.0 host blind, so it must be rejected.

    因子 1.0 会让 1.0 宿主仍然盲, 因此必须拒绝。
    """
    gate = _load_gate()
    assert gate.main(["--scale-factor", "1.0"]) == 2
    assert gate.main(["--scale-factor", "0"]) == 2
    assert gate.main(["--scale-factor", "-2"]) == 2
    assert gate.main(["--scale-factor", "not-a-number"]) == 2
    # A non-1.0 factor is accepted by the validation layer.
    # 非 1.0 的因子能通过校验层。
    assert gate._is_safe_factor("1.5")
    assert gate._is_safe_factor("2")
    assert not gate._is_safe_factor("1.0")


def test_gate_covers_physical_pixel_contracts():
    """The gate must actually cover the files that express physical-pixel rules.

    门禁必须真正覆盖表达物理像素规则的文件。
    """
    gate = _load_gate()
    files = tuple(gate.PHYSICAL_PIXEL_FILES)
    # The three defects found through this blind spot live in the scroll-bar file, so
    # dropping it would make the gate meaningless.
    # 通过该盲区发现的三个缺陷都在滚动条文件里, 因此去掉它会使命禁失去意义。
    assert "tests/qml/test_scroll_bar_conventions.py" in files
    assert len(files) >= 3
    for name in files:
        assert (ROOT / name).is_file(), name
    # Every covered file must actually reference a physical-pixel or dpr contract,
    # otherwise the gate would spend runtime on files that cannot regress this way.
    # 每个被覆盖的文件都必须真正引用物理像素或 dpr 合同, 否则门禁会把运行时间花在不可能
    # 以此种方式回归的文件上。
    markers = ("devicePixelRatio", "physical", "Physical", "物理像素", "_pixel",
               "dpr", "DPI", "dpi")
    for name in files:
        source = (ROOT / name).read_text(encoding="utf-8")
        assert any(marker in source for marker in markers), name


def test_gate_runs_the_full_suite_flag_so_runtime_tests_are_not_skipped():
    """Runtime contracts are gated behind --full-suite and must not be skipped.

    运行时合同被 --full-suite 门控, 不得被跳过。
    """
    source = GATE_PATH.read_text(encoding="utf-8")
    assert '"--full-suite"' in source
    # The gate must force a non-1.0 factor by default.
    # 门禁必须默认强制非 1.0 因子。
    gate = _load_gate()
    assert gate.DEFAULT_SCALE_FACTOR != "1.0"
    assert float(gate.DEFAULT_SCALE_FACTOR) != 1.0


@pytest.mark.parametrize("factor", ("1.5", "2", "3"))
def test_gate_documents_the_multiplier_semantics(factor):
    """QT_SCALE_FACTOR multiplies the host ratio; documented so it is not misread.

    QT_SCALE_FACTOR 是宿主比例的乘数; 记录于此以免被误读为绝对值。
    """
    gate = _load_gate()
    source = GATE_PATH.read_text(encoding="utf-8")
    assert "multiplies the host ratio" in source
    assert gate._is_safe_factor(factor)
