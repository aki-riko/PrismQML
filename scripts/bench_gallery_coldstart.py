# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Interleave real D3D11 Gallery startup A/B samples. 交错测量真实 D3D11 Gallery 启动 A/B。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence

if __package__:
    from ._gallery_coldstart_benchmark import (
        FATAL_RENDER_MARKERS,
        METRIC_FIELDS,
        PROBE_RESULT_PREFIX,
        WINDOW_TYPE_NAMES,
        extract_prefixed_json,
        non_negative_int,
        paired_order,
        percentile,
        positive_float,
        positive_int,
        repo_identity,
        summarize,
        validate_sample,
        write_benchmark_config,
    )
else:
    from _gallery_coldstart_benchmark import (
        FATAL_RENDER_MARKERS,
        METRIC_FIELDS,
        PROBE_RESULT_PREFIX,
        WINDOW_TYPE_NAMES,
        extract_prefixed_json,
        non_negative_int,
        paired_order,
        percentile,
        positive_float,
        positive_int,
        repo_identity,
        summarize,
        validate_sample,
        write_benchmark_config,
    )


RUNNER_RESULT_PREFIX = "PRISMQML_PRIVATE_DESKTOP="
COMPARE_RESULT_PREFIX = "PRISMQML_GALLERY_AB="
DEFAULT_TIMEOUT_SECONDS = 20.0
SUBPROCESS_TIMEOUT_MARGIN_SECONDS = 5.0
PRIVATE_POLL_INTERVAL_SECONDS = 0.005
TIMEOUT_EXIT_CODE = 124


def run_private(command: Sequence[str], timeout_seconds: float) -> int:
    """Run one visible child on a private Windows desktop. 在 Windows 私有桌面运行可见子进程。"""
    from scripts._windows_test_process import (
        WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS,
        _WindowsTestBoundary,
    )

    boundary = _WindowsTestBoundary(command)
    deadline = time.monotonic() + timeout_seconds
    exit_code: int | None = None
    active_before_close: int | None = None
    cleanup_succeeded = False
    try:
        boundary.start()
        while time.monotonic() < deadline:
            exit_code = boundary.root_exit_code()
            if exit_code is not None:
                break
            time.sleep(PRIVATE_POLL_INTERVAL_SECONDS)
        if exit_code is None:
            if not boundary.terminate(TIMEOUT_EXIT_CODE):
                raise RuntimeError("private desktop child did not terminate after timeout")
            exit_code = TIMEOUT_EXIT_CODE
        if not boundary.wait_until_empty(WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS):
            raise RuntimeError("private desktop child left active descendants")
        active_before_close = boundary.active_process_count()
    finally:
        boundary.close()
        cleanup_succeeded = True
    result = {
        "active_processes_before_close": active_before_close,
        "cleanup_succeeded": cleanup_succeeded,
        "exit_code": exit_code,
    }
    print(RUNNER_RESULT_PREFIX + json.dumps(result, sort_keys=True), flush=True)
    return int(exit_code if exit_code is not None else TIMEOUT_EXIT_CODE)


def run_one(
    args: argparse.Namespace,
    label: str,
    repo: Path,
    cache: Path,
    home: Path,
) -> dict[str, object]:
    """Launch and validate one fresh Gallery process. 启动并校验一个全新 Gallery 进程。"""
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(repo),
            "QML_DISK_CACHE_PATH": str(cache),
            "QT_QPA_PLATFORM": "windows",
            "USERPROFILE": str(home),
        }
    )
    environment.pop("QML_DISABLE_DISK_CACHE", None)
    command = [
        str(args.python),
        str(args.script),
        "--private-run",
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--",
        str(args.python),
        str(args.probe),
    ]
    started_ns = time.perf_counter_ns()
    completed = subprocess.run(
        command,
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=args.timeout_seconds + SUBPROCESS_TIMEOUT_MARGIN_SECONDS,
        check=False,
    )
    process_elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000
    combined_output = completed.stdout + completed.stderr
    try:
        row = extract_prefixed_json(completed.stdout, PROBE_RESULT_PREFIX)
        runner = extract_prefixed_json(completed.stdout, RUNNER_RESULT_PREFIX)
    except (json.JSONDecodeError, RuntimeError) as error:
        raise RuntimeError(
            f"{label} did not emit complete benchmark records; rc={completed.returncode}\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        ) from error
    if completed.returncode != 0:
        raise RuntimeError(
            f"{label} failed with rc={completed.returncode}\n{combined_output}"
        )
    if runner.get("cleanup_succeeded") is not True:
        raise RuntimeError(f"{label} private-desktop cleanup failed: {runner}")
    if int(runner.get("active_processes_before_close", -1)) != 0:
        raise RuntimeError(f"{label} left active child processes: {runner}")
    lowered_output = combined_output.lower()
    fatal_markers = [marker for marker in FATAL_RENDER_MARKERS if marker.lower() in lowered_output]
    if fatal_markers:
        raise RuntimeError(f"{label} emitted fatal renderer markers {fatal_markers}")
    validate_sample(row, WINDOW_TYPE_NAMES[args.window_type], args.mica_enabled)
    row.update(
        {
            "cache_path": str(cache),
            "label": label,
            "process_elapsed_ms": process_elapsed_ms,
            "repo": str(repo),
        }
    )
    print(
        f"SAMPLE {label:9s} "
        f"qml={METRIC_FIELDS['qml_load_ms'](row):8.2f}ms "
        f"home={float(row['home_ready_ms']):8.2f}ms "
        f"ready_frame={float(row['ready_frame_ms']):8.2f}ms",
        flush=True,
    )
    return row


def compare(args: argparse.Namespace) -> int:
    """Run warmups and measured interleaved pairs. 运行预热与正式交错配对。"""
    baseline = args.baseline.resolve()
    candidate = args.candidate.resolve()
    cache_root = Path(tempfile.mkdtemp(prefix="prismqml-gallery-ab-"))
    caches = {label: cache_root / label / "qml-cache" for label in ("baseline", "candidate")}
    homes = {label: cache_root / label / "home" for label in ("baseline", "candidate")}
    for label in caches:
        caches[label].mkdir(parents=True)
        write_benchmark_config(
            homes[label],
            window_type=args.window_type,
            lazy_loading=True,
            dwm_shadow=True,
            mica_enabled=args.mica_enabled,
            dpi_scale=args.dpi_scale,
        )
    repos = {"baseline": baseline, "candidate": candidate}

    for index in range(args.warmups):
        order = paired_order(index)
        print(f"WARMUP {index + 1}/{args.warmups} order={','.join(order)}", flush=True)
        for label in order:
            run_one(args, label, repos[label], caches[label], homes[label])

    pairs: list[dict[str, dict[str, object]]] = []
    for index in range(args.pairs):
        order = paired_order(index + args.warmups)
        print(f"PAIR {index + 1}/{args.pairs} order={','.join(order)}", flush=True)
        pair: dict[str, dict[str, object]] = {}
        for label in order:
            pair[label] = run_one(args, label, repos[label], caches[label], homes[label])
        pairs.append(pair)

    result = {
        "cache_root": str(cache_root),
        "identities": {
            "baseline": repo_identity(baseline),
            "candidate": repo_identity(candidate),
        },
        "pair_count": len(pairs),
        "pairs": pairs,
        "settings": {
            "dpi_scale": args.dpi_scale,
            "dwm_shadow": True,
            "graphics_api": "direct3d11",
            "lazy_loading": True,
            "mica_enabled": args.mica_enabled,
            "window_type": args.window_type,
        },
        "summary": summarize(pairs),
        "warmup_count": args.warmups,
    }
    if args.result_file is not None:
        result_file = args.result_file.resolve()
        if result_file.exists():
            raise FileExistsError(f"result file already exists: {result_file}")
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    compact_result = {
        "cache_root": str(cache_root),
        "pair_count": len(pairs),
        "result_file": str(args.result_file.resolve()) if args.result_file else None,
        "summary": result["summary"],
    }
    print(
        COMPARE_RESULT_PREFIX
        + json.dumps(compact_result, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return 0


def parse_private_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the internal private-desktop runner arguments. 解析内部私有桌面运行参数。"""
    parser = argparse.ArgumentParser(description=run_private.__doc__)
    parser.add_argument(
        "--timeout-seconds", type=positive_float, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        parser.error("a child command is required")
    return args


def parse_compare_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse public A/B benchmark arguments. 解析公开 A/B 基准参数。"""
    script = Path(__file__).resolve()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument(
        "--probe", type=Path, default=script.with_name("bench_gallery_coldstart_probe.py")
    )
    parser.add_argument("--warmups", type=non_negative_int, default=2)
    parser.add_argument("--pairs", type=positive_int, default=20)
    parser.add_argument(
        "--timeout-seconds", type=positive_float, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument("--window-type", type=int, choices=WINDOW_TYPE_NAMES, default=1)
    parser.add_argument("--dpi-scale", type=int, choices=(0, 100, 125, 150, 175, 200), default=0)
    parser.add_argument(
        "--mica-enabled", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument("--result-file", type=Path)
    args = parser.parse_args(argv)
    args.script = script
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch private-run or public compare mode. 分发私有运行或公开对比模式。"""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ["--private-run"]:
        private_args = parse_private_args(arguments[1:])
        return run_private(private_args.command, private_args.timeout_seconds)
    return compare(parse_compare_args(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
