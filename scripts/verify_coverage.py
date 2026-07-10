# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Verify runtime coverage of every public QML type. 验证公开 QML 类型运行时覆盖。"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


LOGGER = logging.getLogger(__name__)
QMLDIR_ENTRY = re.compile(r"^(?:singleton\s+)?([A-Z]\w*)\s+(\S+\.qml)$")


def repository_root() -> Path:
    """Return the source checkout root. 返回源码仓库根目录。"""
    return Path(__file__).resolve().parents[1]


def registered_types(qmldir: Path) -> tuple[str, ...]:
    """Parse and validate public type names. 解析并验证公开类型名。"""
    types: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(
        qmldir.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("module "):
            continue
        match = QMLDIR_ENTRY.fullmatch(line)
        if match is None:
            raise ValueError(f"unsupported qmldir entry at line {line_number}: {line}")
        type_name = match.group(1)
        if type_name in seen:
            raise ValueError(f"duplicate QML type registration: {type_name}")
        seen.add(type_name)
        types.append(type_name)
    if not types:
        raise ValueError(f"no public QML types registered in {qmldir}")
    return tuple(types)


def run_probe(
    root: Path,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> tuple[int, int]:
    """Run the authoritative headless component probe. 运行权威无头组件探测。"""
    qmldir = root / "prismqml" / "PrismQML" / "qmldir"
    total = len(registered_types(qmldir))
    probe = root / "tests" / "qml" / "probe_all_components.py"
    if not probe.is_file():
        raise FileNotFoundError(f"QML component probe not found: {probe}")
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    command = [sys.executable, "-X", "utf8", str(probe)]
    completed = (runner or subprocess.run)(
        command,
        cwd=root,
        env=environment,
        check=False,
    )
    return total, completed.returncode


def main() -> int:
    """Verify that all registered public types are accounted for. 验证全部公开类型。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        total, return_code = run_probe(repository_root())
    except (OSError, ValueError) as error:
        LOGGER.error("QML runtime coverage setup failed: %s", error)
        return 2
    if return_code:
        LOGGER.error("QML runtime coverage failed for %d registered types", total)
    else:
        LOGGER.info("QML runtime coverage passed for %d registered types", total)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
