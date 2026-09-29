# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Run the complete pytest suite in isolated protected shards. 完整测试分片运行器。"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT_SECONDS = 1800
DEFAULT_SUPERVISOR_TIMEOUT_SECONDS = 2100
LOGGER = logging.getLogger("prismqml.test_shards")
SHARD_LAYOUT = (
    ("python", ROOT / "tests", 2),
    ("qml", ROOT / "tests" / "qml", 4),
    ("tooling", ROOT / "tests" / "tooling", 2),
)
SERIAL_RUNTIME_FILES = (
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


def _file_weight(path: Path) -> int:
    relative = path.relative_to(ROOT).as_posix()
    return max(path.stat().st_size, RUNTIME_WEIGHT_HINTS.get(relative, 0) * 100)


def _partition_files(root: Path, count: int) -> tuple[tuple[str, ...], ...]:
    buckets: list[list[Path]] = [[] for _ in range(count)]
    weights = [0] * count
    files = sorted(
        (
            path
            for path in _test_files(root)
            if path.relative_to(ROOT).as_posix() not in SERIAL_RUNTIME_FILES
        ),
        key=lambda path: (_file_weight(path), path.as_posix()),
        reverse=True,
    )
    for path in files:
        bucket = min(range(count), key=lambda index: (weights[index], index))
        buckets[bucket].append(path)
        weights[bucket] += _file_weight(path)
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
    return tuple(result)


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
        "--durations=20",
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
            "超时预算: shard=%ss / supervisor=%ss",
            args.timeout,
            args.supervisor_timeout,
        )
        for name, paths in shards:
            if name.startswith("serial-runtime-"):
                phase = "串行收尾"
            elif name.startswith("tooling-"):
                phase = "tooling 阶段"
            else:
                phase = "Python/QML 并行阶段"
            LOGGER.info("%s [%s]: %s 个文件", name, phase, len(paths))
            LOGGER.info("命令: %s", _command(name, paths, args.timeout))
        return 0
    python_qml_shards = tuple(
        shard
        for shard in shards
        if not shard[0].startswith(("tooling-", "serial-runtime-"))
    )
    tooling_shards = tuple(
        shard for shard in shards if shard[0].startswith("tooling-")
    )
    serial_shards = tuple(
        shard for shard in shards if shard[0].startswith("serial-runtime-")
    )
    python_qml_status = _finish_shards(
        _start_shards(python_qml_shards, args.timeout)
    )
    tooling_status = _finish_shards(_start_shards(tooling_shards, args.timeout))
    serial_status = _finish_shards(_start_shards(serial_shards, args.timeout))
    return python_qml_status or tooling_status or serial_status


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
