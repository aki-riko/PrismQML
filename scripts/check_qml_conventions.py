# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Read-only PrismQML convention scanner CLI. 只读 QML 规范扫描命令。"""

from __future__ import annotations

import argparse
from collections import Counter
import os
from pathlib import Path
import sys
from typing import Sequence

if __package__:
    from .qml_conventions import (
        Violation,
        scan_changed,
        scan_repository,
        scan_source_text,
        scan_text,
    )
else:
    from qml_conventions import (
        Violation,
        scan_changed,
        scan_repository,
        scan_source_text,
        scan_text,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _print_report(
    violations: Sequence[Violation], scope: str, max_details: int
) -> None:
    print(f"QML convention scan [{scope}]: {len(violations)} violation(s)")
    for violation in violations[:max_details]:
        print(
            f"{violation.path}:{violation.line}: {violation.rule} "
            f"{violation.message} | {violation.source}"
        )
    if len(violations) > max_details:
        print(f"... {len(violations) - max_details} more violation(s) omitted")
    counts = Counter(item.rule for item in violations)
    if counts:
        totals = ", ".join(f"{rule}={counts[rule]}" for rule in sorted(counts))
        print(f"Rule totals: {totals}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--all", action="store_true", help="scan all library QML/JavaScript sources"
    )
    mode.add_argument("--changed", action="store_true", help="report violations added since base")
    parser.add_argument("--base", help="git base for --changed; defaults to env or HEAD")
    parser.add_argument(
        "--report-only", action="store_true", help="always exit zero after reporting"
    )
    parser.add_argument("--max-details", type=int, default=100)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.all:
            violations = scan_repository(root)
            _print_report(violations, "all", max(args.max_details, 0))
        else:
            base = args.base or os.environ.get("PRISMQML_QML_BASE_REF") or "HEAD"
            result = scan_changed(root, base)
            violations = list(result.violations)
            scope = (
                f"changed base={base} files={result.changed_files} "
                f"current={result.current_total} baseline={result.base_total}"
            )
            _print_report(violations, scope, max(args.max_details, 0))
    except (FileNotFoundError, OSError, RuntimeError) as error:
        print(f"QML convention scan failed: {error}", file=sys.stderr)
        return 2
    return 0 if args.report_only or not violations else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())
