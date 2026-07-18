# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Frame benchmark output-path regressions. 帧基准输出路径回归。"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH_PATH = ROOT / "tests" / "qml" / "bench_skin_frames.py"


def _load_benchmark_module():
    spec = importlib.util.spec_from_file_location("bench_skin_frames", BENCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explicit_output_path_takes_priority(tmp_path, monkeypatch):
    benchmark = _load_benchmark_module()
    monkeypatch.setenv(benchmark.OUTPUT_ENV, str(tmp_path / "environment.txt"))

    expected = (tmp_path / "explicit.txt").resolve()
    assert benchmark.resolve_output_path(tmp_path / "explicit.txt") == expected


def test_environment_and_temp_directory_fallbacks(tmp_path, monkeypatch):
    benchmark = _load_benchmark_module()
    configured = tmp_path / "configured.txt"
    monkeypatch.setenv(benchmark.OUTPUT_ENV, str(configured))
    assert benchmark.resolve_output_path(None) == configured.resolve()

    monkeypatch.delenv(benchmark.OUTPUT_ENV)
    fallback = benchmark.resolve_output_path(None)
    assert fallback.name == "frame_bench.txt"
    assert fallback.parent.name == "prismqml"


def test_benchmark_source_has_no_user_specific_output_path():
    source = BENCH_PATH.read_text(encoding="utf-8")

    assert "C:/Users/Kotori" not in source
    assert "--output" in source
    assert "PRISMQML_FRAME_BENCH_OUTPUT" in source
