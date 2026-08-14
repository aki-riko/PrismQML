# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tests for the Gallery cold-start benchmark. Gallery 冷启动基准测试。"""

from __future__ import annotations

import json

import pytest

from scripts import bench_gallery_coldstart as benchmark


def _sample(offset: float) -> dict[str, object]:
    return {
        "qml_start_ms": 10.0 + offset,
        "qml_end_ms": 20.0 + offset,
        "event_loop_ready_ms": 21.0 + offset,
        "first_frame_ms": 22.0 + offset,
        "home_ready_ms": 30.0 + offset,
        "splash_finished_ms": 40.0 + offset,
        "shell_ready_ms": 41.0 + offset,
        "ready_frame_ms": 42.0 + offset,
    }


def test_paired_order_balances_adjacent_pairs() -> None:
    assert benchmark.paired_order(0) == ("baseline", "candidate")
    assert benchmark.paired_order(1) == ("candidate", "baseline")


def test_percentile_interpolates_and_rejects_empty_input() -> None:
    assert benchmark.percentile([0.0, 10.0], 0.25) == pytest.approx(2.5)
    with pytest.raises(ValueError, match="at least one"):
        benchmark.percentile([], 0.5)


def test_summarize_preserves_paired_deltas() -> None:
    pairs = [
        {"baseline": _sample(0.0), "candidate": _sample(-2.0)},
        {"baseline": _sample(1.0), "candidate": _sample(4.0)},
    ]

    summary = benchmark.summarize(pairs)

    ready = summary["ready_frame_ms"]
    assert ready["paired_deltas_ms"] == [-2.0, 3.0]
    assert ready["paired_delta_median_ms"] == pytest.approx(0.5)
    assert ready["candidate_wins"] == 1


def test_extract_prefixed_json_requires_exactly_one_record() -> None:
    prefix = "RESULT="
    assert benchmark.extract_prefixed_json('noise\nRESULT={"ok": true}\n', prefix) == {
        "ok": True
    }
    with pytest.raises(RuntimeError, match="expected one"):
        benchmark.extract_prefixed_json("noise", prefix)


def test_validate_sample_checks_visual_path_and_monotonicity() -> None:
    row = {
        **_sample(0.0),
        "caption_button_count": 3,
        "dwm_initialization_done": True,
        "exit_code": 0,
        "frame_count": 2,
        "lazy_loading": True,
        "mica_enabled": True,
        "renderer_graphics_api": "Direct3D11",
        "requested_graphics_api": "Direct3D11",
        "shadow_mode": 1,
        "show_animation_started": True,
        "splash_visible": False,
        "timed_out": False,
        "window_type": "WindowsBar",
    }
    benchmark.validate_sample(row, "WindowsBar", True)

    row["ready_frame_ms"] = 39.0
    with pytest.raises(RuntimeError, match="not monotonic"):
        benchmark.validate_sample(row, "WindowsBar", True)


def test_write_benchmark_config_isolated_settings(tmp_path) -> None:
    path = benchmark.write_benchmark_config(
        tmp_path,
        window_type=1,
        lazy_loading=True,
        dwm_shadow=True,
        mica_enabled=True,
        dpi_scale=0,
    )

    assert path == tmp_path / ".prismqml" / "app.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "Window": {
            "DpiScale": 0,
            "DwmShadow": True,
            "LazyLoading": True,
            "MicaEnabled": True,
            "WindowType": 1,
        }
    }
