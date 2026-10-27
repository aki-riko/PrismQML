# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Run the complete pytest suite in isolated protected shards. 完整测试分片运行器。"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT_SECONDS = 1200
DEFAULT_SUPERVISOR_TIMEOUT_SECONDS = 1500
DEFAULT_SERIAL_TIMEOUT_SECONDS = 180
LOGGER = logging.getLogger("prismqml.test_shards")
SHARD_LAYOUT = (
    ("python", ROOT / "tests", 2),
    ("qml", ROOT / "tests" / "qml", 4),
    ("tooling", ROOT / "tests" / "tooling", 2),
)
SERIAL_RUNTIME_FILES = (
    "tests/test_task_runner.py",
    "tests/qml/test_icon_renderer_layer_lifecycle.py",
    "tests/qml/test_layout_container_conventions.py",
    "tests/qml/test_vintage_ticket_component_state_matrix.py",
    # The vintage-ticket state-matrix fixture asserts that the process owns exactly the
    # same top-level windows before and after the module, so any neighbour that leaks
    # one fails the teardown instead of its own test. It is order-sensitive by
    # construction and needs its own process.
    # 票据状态矩阵夹具断言模块前后顶层窗口完全一致, 因此任何泄漏窗口的邻接测试都会让
    # teardown 失败(而不是失败在它自己身上)。这类夹具按构造就顺序敏感, 需要独立进程。
    "tests/qml/test_vintage_ticket_button_state_matrix.py",
    "tests/qml/test_neumorphism_remaining_surfaces.py",
    "tests/qml/test_timeline_conventions.py",
    "tests/qml/test_effects_page_matrix_controls.py",
    "tests/qml/test_hyperlink_cursor_contracts.py",
    "tests/qml/test_navigation_icon_layer_lifecycle.py",
    "tests/qml/test_window_icon_provider_paths.py",
    "tests/qml/test_drop_zone_conventions.py",
    "tests/qml/test_input_folder_drop.py",
    "tests/qml/test_vintage_ticket_extended_surfaces.py",
    "tests/qml/test_timeline_overshoot_relayout.py",
)
NESTED_ENTRYPOINT_FILES = (
    "tests/tooling/test_headless_test_entrypoints.py",
)
# Runtime hints keep known fixed-wait files from landing in the same QML bucket.
# 运行时提示用于避免已知固定等待文件集中到同一个 QML 分片。
RUNTIME_WEIGHT_HINTS = {
    "tests/qml/test_stacked_widget_loader_lifecycle.py": 9_020,
    "tests/qml/test_scroll_bar_conventions.py": 8_032,
    "tests/qml/test_skin_scope_surfaces.py": 5_650,
    "tests/qml/test_desktop_notification_banner_avoidance.py": 5_070,
    "tests/qml/test_skin_scope.py": 5_000,
    "tests/qml/test_desktop_notification_geometry.py": 4_180,
}
# Measured durations outrank every estimate. File size and the hand-written hints above
# are only proxies, and they are wrong in the direction that hurts most: a shard can
# hold a normal byte total while several fixed-wait files land together, which is how
# qml-2 exhausted a 1200s budget on two separate releases (once on
# test_vintage_ticket_surfaces.py, once on test_accent_foreground_consumers.py) while
# the other buckets finished in about three minutes. Each completed shard therefore
# records per-file seconds, and the partitioner balances on those once available.
# 实测耗时优先于任何估算。文件大小和上面手写的提示都只是代理量, 且它们的偏差恰好落在
# 最伤人的方向: 一个分片的总字节数可以正常, 却同时容纳多个固定等待文件——qml-2 正是
# 这样在两次发布中耗尽 1200s 预算(一次卡在 test_vintage_ticket_surfaces.py, 一次卡在
# test_accent_foreground_consumers.py), 而其它分片三分钟就完成。因此每个完成的分片都会
# 记录逐文件秒数, 分片器在有数据后按实测耗时做均衡。
DURATION_CACHE_NAME = "shard-durations.json"
DURATION_SAMPLE_LIMIT = 5


def _positive_timeout(value: str) -> int:
    timeout = int(value)
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return timeout


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="确认运行包含发布级门禁在内的完整套件",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_timeout,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="每个分片的保护运行超时（秒）",
    )
    parser.add_argument(
        "--supervisor-timeout",
        type=_positive_timeout,
        default=DEFAULT_SUPERVISOR_TIMEOUT_SECONDS,
        help="外层 runner 的总超时，须留时间输出分片失败诊断",
    )
    parser.add_argument(
        "--serial-timeout",
        type=_positive_timeout,
        default=int(
            os.environ.get(
                "PRISM_SERIAL_RUNTIME_TIMEOUT_SECONDS",
                DEFAULT_SERIAL_TIMEOUT_SECONDS,
            )
        ),
        help="串行隔离测试的单进程保护超时（秒）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出稳定分片计划，不启动测试进程",
    )
    args = parser.parse_args(argv)
    if not args.full_suite:
        parser.error("完整分片运行必须显式提供 --full-suite")
    if args.supervisor_timeout <= args.timeout:
        parser.error("外层 supervisor 超时必须大于分片超时")
    return args


def _test_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.glob("test_*.py")))


def _duration_cache_path() -> Path:
    return _artifact_root() / "python" / DURATION_CACHE_NAME


def _load_measured_durations() -> dict[str, float]:
    """Per-file seconds from previous runs, as a median of recent samples."""
    path = _duration_cache_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("无法读取耗时缓存 %s: %s", path, exc)
        return {}
    if not isinstance(raw, dict):
        return {}
    measured: dict[str, float] = {}
    for name, samples in raw.items():
        if not isinstance(samples, list) or not samples:
            continue
        values = sorted(
            float(value) for value in samples if isinstance(value, (int, float))
        )
        if not values:
            continue
        measured[name] = values[len(values) // 2]
    return measured


def _record_measured_durations(shard_name: str, log_text: str) -> None:
    """Persist per-file seconds parsed from one shard's pytest log.

    pytest runs with `--durations=0`, so every test reports its own line and the cache
    covers the whole shard rather than its slowest entries.
    pytest 以 `--durations=0` 运行, 因此每个用例都有自己的一行, 缓存覆盖整个分片而不是
    仅最慢的若干项。
    """
    pattern = re.compile(
        r"^(?P<seconds>\d+\.\d+)s\s+(?:call|setup|teardown)\s+(?P<path>tests/\S+?)::",
        re.MULTILINE,
    )
    per_file: dict[str, float] = {}
    for match in pattern.finditer(log_text):
        path = match.group("path")
        seconds = float(match.group("seconds"))
        # Sum every reported phase of a file; several top entries may share a file.
        # 累加同一文件上报的各个阶段; 最慢列表里多个条目可能属于同一文件。
        per_file[path] = per_file.get(path, 0.0) + seconds
    if not per_file:
        return
    path = _duration_cache_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        if not isinstance(raw, dict):
            raw = {}
        for name, seconds in per_file.items():
            samples = raw.get(name)
            if not isinstance(samples, list):
                samples = []
            samples.append(round(seconds, 3))
            raw[name] = samples[-DURATION_SAMPLE_LIMIT:]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8"
        )
    except OSError as exc:
        LOGGER.warning("无法写入耗时缓存 %s: %s (shard=%s)", path, exc, shard_name)


def _file_weight(path: Path, measured: dict[str, float]) -> int:
    relative = path.relative_to(ROOT).as_posix()
    # Measured seconds win outright; they are the only signal that reflects
    # fixed-wait behaviour rather than source size.
    # 实测秒数优先; 它是唯一反映固定等待行为而非源码体积的信号。
    if relative in measured:
        return max(1, int(measured[relative] * 1_000))
    return max(path.stat().st_size, RUNTIME_WEIGHT_HINTS.get(relative, 0) * 100)


def _partition_files(root: Path, count: int) -> tuple[tuple[str, ...], ...]:
    buckets: list[list[Path]] = [[] for _ in range(count)]
    weights = [0] * count
    excluded_files = set(SERIAL_RUNTIME_FILES) | set(NESTED_ENTRYPOINT_FILES)
    measured = _load_measured_durations()
    files = sorted(
        (
            path
            for path in _test_files(root)
            if path.relative_to(ROOT).as_posix() not in excluded_files
        ),
        key=lambda path: (_file_weight(path, measured), path.as_posix()),
        reverse=True,
    )
    for path in files:
        bucket = min(range(count), key=lambda index: (weights[index], index))
        buckets[bucket].append(path)
        weights[bucket] += _file_weight(path, measured)
    return tuple(
        tuple(path.relative_to(ROOT).as_posix() for path in bucket)
        for bucket in buckets
        if bucket
    )


def _shards() -> tuple[tuple[str, tuple[str, ...]], ...]:
    result = []
    for name, root, count in SHARD_LAYOUT:
        for index, paths in enumerate(_partition_files(root, count), start=1):
            result.append((f"{name}-{index}", paths))
    for index, path in enumerate(SERIAL_RUNTIME_FILES, start=1):
        result.append((f"serial-runtime-{index}", (path,)))
    for index, path in enumerate(NESTED_ENTRYPOINT_FILES, start=1):
        result.append((f"nested-entrypoint-{index}", (path,)))
    return tuple(result)


def _execution_phases(
    shards: tuple[tuple[str, tuple[str, ...]], ...]
):
    """Keep QML engines clear of the nested entrypoint subprocess matrix."""
    python_qml = tuple(
        shard
        for shard in shards
        if not shard[0].startswith(
            ("tooling-", "serial-runtime-", "nested-entrypoint-")
        )
    )
    tooling = tuple(
        shard for shard in shards if shard[0].startswith("tooling-")
    )
    serial = tuple(
        shard for shard in shards if shard[0].startswith("serial-runtime-")
    )
    nested_entrypoints = tuple(
        shard
        for shard in shards
        if shard[0].startswith("nested-entrypoint-")
    )
    return python_qml, tooling, serial, nested_entrypoints


def _artifact_root() -> Path:
    configured = os.environ.get("PRISM_ARTIFACT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return ROOT / ".artifacts"


def _command(name: str, paths: tuple[str, ...], timeout: int) -> list[str]:
    cache_dir = _artifact_root() / "python" / "test-shards" / name / "pytest-cache"
    return [
        sys.executable,
        str(ROOT / "scripts" / "test_process.py"),
        "--qt-platform",
        "offscreen",
        "--timeout",
        str(timeout),
        "--",
        sys.executable,
        "-m",
        "pytest",
        "--full-suite",
        # Report every duration, not just the slowest twenty: the partitioner balances
        # on per-file seconds, so a partial list would leave most files on the size
        # estimate and re-introduce the imbalance. Log growth is a few hundred lines.
        # 报告全部耗时而非仅最慢二十项: 分片器按逐文件秒数均衡, 部分列表会让多数文件退回
        # 体积估算, 从而重新引入不均衡。日志增长只有数百行。
        "--durations=0",
        "-o",
        f"cache_dir={cache_dir}",
        *paths,
    ]


def _start_shards(shards: tuple[tuple[str, tuple[str, ...]], ...], timeout: int):
    log_root = _artifact_root() / "python" / "test-shards"
    processes = []
    for name, paths in shards:
        shard_root = log_root / name
        shard_root.mkdir(parents=True, exist_ok=True)
        log_path = shard_root / "pytest.log"
        log_file = log_path.open("w", encoding="utf-8")
        environment = os.environ.copy()
        environment["PRISM_ARTIFACT_ROOT"] = str(shard_root)
        process = subprocess.Popen(
            _command(name, paths, timeout),
            cwd=ROOT,
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        processes.append((name, process, log_file, log_path))
        LOGGER.info("分片已启动: %s, 日志: %s", name, log_path)
    return processes


def _finish_shards(processes) -> int:
    failures = []
    for name, process, log_file, log_path in processes:
        return_code = process.wait()
        log_file.close()
        LOGGER.info("分片完成: %s, exit=%s", name, return_code)
        # Record durations for successful shards only: a timed-out log is truncated at
        # an arbitrary point, so its per-file numbers would skew the next partition.
        # 只记录成功分片的耗时: 超时日志在任意点被截断, 其逐文件数值会污染下一次分片。
        if return_code == 0:
            try:
                _record_measured_durations(
                    name, log_path.read_text(encoding="utf-8", errors="replace")
                )
            except OSError as exc:
                LOGGER.warning("读取分片日志用于耗时统计失败: %s: %s", log_path, exc)
        if return_code != 0:
            failures.append((name, return_code, log_path))
    if failures:
        for name, return_code, log_path in failures:
            LOGGER.error("分片失败: %s, exit=%s, 详见 %s", name, return_code, log_path)
            try:
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                LOGGER.exception("读取失败分片日志失败: %s: %s", log_path, exc)
                continue
            LOGGER.error("分片失败日志末尾 [%s]:\n%s", name, log_text[-12000:])
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    shards = _shards()
    if args.dry_run:
        LOGGER.info(
            "超时预算: shard=%ss / serial=%ss / supervisor=%ss",
            args.timeout,
            args.serial_timeout,
            args.supervisor_timeout,
        )
        for name, paths in shards:
            if name.startswith("serial-runtime-"):
                phase = "隔离收尾阶段"
            elif name.startswith("nested-entrypoint-"):
                phase = "嵌套入口阶段"
            elif name.startswith("tooling-"):
                phase = "QML 后并行阶段"
            else:
                phase = "Python/QML 并行阶段"
            LOGGER.info("%s [%s]: %s 个文件", name, phase, len(paths))
            LOGGER.info("命令: %s", _command(name, paths, args.timeout))
        return 0
    (
        python_qml_shards,
        tooling_shards,
        serial_shards,
        nested_entrypoint_shards,
    ) = _execution_phases(shards)
    python_qml_status = _finish_shards(
        _start_shards(python_qml_shards, args.timeout)
    )
    # Tooling and nested-entrypoint tests must finish before serial runtime tests.
    # 工具合同与嵌套入口测试必须先收尾，再进入串行运行时阶段，避免多个
    # Qt 进程同时退出时的 QThread 清理竞态。
    tooling_processes = _start_shards(tooling_shards, args.timeout)
    nested_entrypoint_processes = _start_shards(
        nested_entrypoint_shards, args.serial_timeout
    )
    tooling_status = _finish_shards(tooling_processes)
    nested_entrypoint_status = _finish_shards(nested_entrypoint_processes)
    serial_status = 0
    for shard in serial_shards:
        status = _finish_shards(
            _start_shards((shard,), args.serial_timeout)
        )
        serial_status = serial_status or status
        # Keep going after a failure. Breaking here left the remaining serial shards
        # never executed, so their logs still showed the previous run's timestamps
        # while the suite reported a single timeout as if it were the whole picture.
        # 失败后继续执行。此前的 break 让剩余串行分片根本不运行, 它们的日志仍是上一次运行
        # 的时间戳, 而套件只报告一个超时, 像是全部情况。
    return (
        python_qml_status
        or tooling_status
        or serial_status
        or nested_entrypoint_status
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
