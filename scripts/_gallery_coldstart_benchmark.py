# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Pure helpers for the Gallery cold-start benchmark. Gallery 冷启动基准纯辅助函数。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
from collections.abc import Callable, Sequence


PROBE_RESULT_PREFIX = "PRISMQML_GALLERY_PROBE="
EXPECTED_GRAPHICS_API = "Direct3D11"
EXPECTED_NATIVE_SHADOW_MODE = 1
WINDOW_TYPE_NAMES = {0: "WindowsSplit", 1: "WindowsBar", 2: "WindowsFilled"}
FATAL_RENDER_MARKERS = (
    "DXGI_ERROR_DEVICE_HUNG",
    "DXGI_ERROR_DEVICE_REMOVED",
    "device lost",
)
METRIC_FIELDS: dict[str, Callable[[dict[str, object]], float]] = {
    "qml_load_ms": lambda row: float(row["qml_end_ms"]) - float(row["qml_start_ms"]),
    "event_loop_ready_ms": lambda row: float(row["event_loop_ready_ms"]),
    "first_frame_ms": lambda row: float(row["first_frame_ms"]),
    "home_ready_ms": lambda row: float(row["home_ready_ms"]),
    "splash_finished_ms": lambda row: float(row["splash_finished_ms"]),
    "shell_ready_ms": lambda row: float(row["shell_ready_ms"]),
    "ready_frame_ms": lambda row: float(row["ready_frame_ms"]),
    "load_to_ready_frame_ms": (
        lambda row: float(row["ready_frame_ms"]) - float(row["qml_start_ms"])
    ),
}


def positive_int(value: str) -> int:
    """Parse a positive CLI integer. 解析正整数命令行参数。"""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def non_negative_int(value: str) -> int:
    """Parse a non-negative CLI integer. 解析非负整数命令行参数。"""
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must not be negative")
    return parsed


def positive_float(value: str) -> float:
    """Parse a positive CLI float. 解析正浮点命令行参数。"""
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def paired_order(index: int) -> tuple[str, str]:
    """Alternate order to balance time drift. 交替顺序以平衡时间漂移。"""
    return ("baseline", "candidate") if index % 2 == 0 else ("candidate", "baseline")


def percentile(values: Sequence[float], fraction: float) -> float:
    """Return an interpolated percentile. 返回线性插值百分位数。"""
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be between zero and one")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize(pairs: Sequence[dict[str, dict[str, object]]]) -> dict[str, object]:
    """Summarize paired medians, tails, and wins. 汇总配对中位数、尾部与胜出数。"""
    if not pairs:
        raise ValueError("at least one measured pair is required")
    summary: dict[str, object] = {}
    for field, getter in METRIC_FIELDS.items():
        baseline = [getter(pair["baseline"]) for pair in pairs]
        candidate = [getter(pair["candidate"]) for pair in pairs]
        deltas = [right - left for left, right in zip(baseline, candidate, strict=True)]
        summary[field] = {
            "baseline_median_ms": statistics.median(baseline),
            "candidate_median_ms": statistics.median(candidate),
            "paired_delta_median_ms": statistics.median(deltas),
            "paired_delta_mean_ms": statistics.fmean(deltas),
            "paired_delta_p10_ms": percentile(deltas, 0.10),
            "paired_delta_p90_ms": percentile(deltas, 0.90),
            "paired_delta_min_ms": min(deltas),
            "paired_delta_max_ms": max(deltas),
            "candidate_wins": sum(delta < 0 for delta in deltas),
            "pairs": len(pairs),
            "paired_deltas_ms": deltas,
        }
    return summary


def extract_prefixed_json(output: str, prefix: str) -> dict[str, object]:
    """Extract exactly one JSON record with a prefix. 提取唯一带前缀 JSON 记录。"""
    records = [
        json.loads(line.removeprefix(prefix))
        for line in output.splitlines()
        if line.startswith(prefix)
    ]
    if len(records) != 1:
        raise RuntimeError(f"expected one {prefix!r} record, got {len(records)}")
    return records[0]


def _validate_path_invariants(
    row: dict[str, object], expected_window_type: str, expected_mica: bool
) -> None:
    if row.get("timed_out") or int(row.get("exit_code", -1)) != 0:
        raise RuntimeError(f"probe did not finish cleanly: {row}")
    if row.get("requested_graphics_api") != EXPECTED_GRAPHICS_API:
        raise RuntimeError(f"unexpected requested graphics API: {row}")
    if row.get("renderer_graphics_api") != EXPECTED_GRAPHICS_API:
        raise RuntimeError(f"unexpected renderer graphics API: {row}")
    if row.get("window_type") != expected_window_type:
        raise RuntimeError(f"unexpected Gallery window type: {row}")
    if int(row.get("caption_button_count", -1)) != 3:
        raise RuntimeError(f"caption-button invariant failed: {row}")
    if row.get("lazy_loading") is not True:
        raise RuntimeError(f"lazy-loading invariant failed: {row}")
    if row.get("mica_enabled") is not expected_mica:
        raise RuntimeError(f"Mica setting invariant failed: {row}")
    if int(row.get("shadow_mode", -1)) != EXPECTED_NATIVE_SHADOW_MODE:
        raise RuntimeError(f"native-shadow invariant failed: {row}")


def _validate_completion_invariants(row: dict[str, object]) -> None:
    if row.get("dwm_initialization_done") is not True:
        raise RuntimeError(f"DWM initialization invariant failed: {row}")
    if row.get("show_animation_started") is not True:
        raise RuntimeError(f"show-animation invariant failed: {row}")
    if row.get("splash_visible") is not False:
        raise RuntimeError(f"Splash completion invariant failed: {row}")
    if int(row.get("frame_count", 0)) < 2:
        raise RuntimeError(f"ready-frame invariant failed: {row}")


def _validate_milestone_order(row: dict[str, object]) -> None:
    ordered = (
        "qml_start_ms",
        "qml_end_ms",
        "event_loop_ready_ms",
        "home_ready_ms",
        "splash_finished_ms",
        "shell_ready_ms",
        "ready_frame_ms",
    )
    missing = sorted(set(ordered).difference(row))
    if missing:
        raise RuntimeError(f"probe result is missing metrics: {missing}")
    values = [float(row[name]) for name in ordered]
    if values != sorted(values):
        raise RuntimeError(f"startup milestones are not monotonic: {row}")
    if not (
        float(row["event_loop_ready_ms"])
        <= float(row["first_frame_ms"])
        <= float(row["ready_frame_ms"])
    ):
        raise RuntimeError(f"frame milestones are not monotonic: {row}")


def validate_sample(
    row: dict[str, object], expected_window_type: str, expected_mica: bool
) -> None:
    """Validate visual-path and readiness invariants. 校验视觉路径与就绪不变量。"""
    _validate_path_invariants(row, expected_window_type, expected_mica)
    _validate_completion_invariants(row)
    _validate_milestone_order(row)


def write_benchmark_config(
    home: Path,
    *,
    window_type: int,
    lazy_loading: bool,
    dwm_shadow: bool,
    mica_enabled: bool,
    dpi_scale: int,
) -> Path:
    """Write an isolated Gallery config without touching user state. 写入隔离配置且不触碰用户状态。"""
    config_path = home / ".prismqml" / "app.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "Window": {
            "DpiScale": dpi_scale,
            "DwmShadow": dwm_shadow,
            "LazyLoading": lazy_loading,
            "MicaEnabled": mica_enabled,
            "WindowType": window_type,
        }
    }
    config_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    return config_path


def _git_text(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def _source_digest(repo: Path) -> str:
    source_files = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "examples",
            "prismqml",
        ],
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    digest = hashlib.sha256()
    for relative_bytes in sorted(path for path in source_files if path):
        digest.update(relative_bytes)
        digest.update(b"\0")
        digest.update((repo / relative_bytes.decode("utf-8")).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def repo_identity(repo: Path) -> dict[str, object]:
    """Capture source identity for reproducible evidence. 捕获源码身份供结果复现。"""
    status = _git_text(repo, "status", "--short").splitlines()
    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", "HEAD"],
        capture_output=True,
        check=True,
    ).stdout
    return {
        "path": str(repo),
        "commit": _git_text(repo, "rev-parse", "HEAD").strip(),
        "dirty": bool(status),
        "status": status,
        "source_sha256": _source_digest(repo),
        "tracked_diff_sha256": hashlib.sha256(diff).hexdigest(),
    }
