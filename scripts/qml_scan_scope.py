# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Repository scope for the QML scanner. QML 扫描器仓库范围管理。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import subprocess
from typing import (
    Callable,
    Generic,
    Hashable,
    Iterable,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
)


QML_ROOT = PurePosixPath("prismqml/PrismQML")
EXAMPLES_ROOT = PurePosixPath("examples")
SCAN_ROOTS = (QML_ROOT, EXAMPLES_ROOT)
SUPPORTED_SOURCE_SUFFIXES = frozenset({".js", ".qml"})
EXAMPLES_ALLOWED_RULES = frozenset({"QML010"})


class ScannableViolation(Protocol):
    """Minimal violation contract used by scope orchestration. 范围编排所需违规契约。"""

    rule: str

    def fingerprint(self) -> Hashable:
        """Return a stable baseline fingerprint. 返回稳定基线指纹。"""


ViolationType = TypeVar("ViolationType", bound=ScannableViolation)
SourceScanner = Callable[
    [str, PurePosixPath, Optional[PurePosixPath]], list[ViolationType]
]


@dataclass(frozen=True)
class ChangedQmlFile:
    """Current and baseline paths for a changed source. 改动源码的当前与基线路径。"""

    current_path: PurePosixPath
    base_path: PurePosixPath | None


@dataclass(frozen=True)
class ChangedScanResult(Generic[ViolationType]):
    """Changed-mode scan summary. 改动模式扫描摘要。"""

    violations: tuple[ViolationType, ...]
    changed_files: int
    current_total: int
    base_total: int


def _is_under_root(path: PurePosixPath, root: PurePosixPath) -> bool:
    return path == root or root in path.parents


def _filter_source_scope(
    source_path: PurePosixPath, violations: Iterable[ViolationType]
) -> list[ViolationType]:
    items = list(violations)
    if not _is_under_root(source_path, EXAMPLES_ROOT):
        return items
    return [item for item in items if item.rule in EXAMPLES_ALLOWED_RULES]


def _repository_source_paths(root: Path) -> Iterable[Path]:
    qml_root = root / QML_ROOT
    if not qml_root.is_dir():
        raise FileNotFoundError(f"QML root not found: {qml_root}")
    for source_root in SCAN_ROOTS:
        absolute_root = root / source_root
        if not absolute_root.is_dir():
            continue
        yield from (
            path
            for path in absolute_root.rglob("*")
            if path.is_file() and path.suffix in SUPPORTED_SOURCE_SUFFIXES
        )


def scan_repository(
    root: Path, scanner: SourceScanner[ViolationType]
) -> list[ViolationType]:
    """Scan all configured source roots. 扫描全部已配置源码根。"""
    violations: list[ViolationType] = []
    for path in sorted(_repository_source_paths(root)):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        current = scanner(path.read_text(encoding="utf-8"), relative, None)
        violations.extend(_filter_source_scope(relative, current))
    return violations


def _run_git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def _verify_base(root: Path, base: str) -> None:
    completed = _run_git(root, ["rev-parse", "--verify", f"{base}^{{commit}}"])
    if completed.returncode != 0:
        raise RuntimeError(f"invalid git base {base}: {completed.stderr.strip()}")


def _parse_changed_line(line: str) -> ChangedQmlFile | None:
    fields = line.split("\t")
    status = fields[0]
    if status.startswith("R") and len(fields) == 3:
        return ChangedQmlFile(PurePosixPath(fields[2]), PurePosixPath(fields[1]))
    if status.startswith("M") and len(fields) == 2:
        path = PurePosixPath(fields[1])
        return ChangedQmlFile(path, path)
    if status.startswith("A") and len(fields) == 2:
        return ChangedQmlFile(PurePosixPath(fields[1]), None)
    if status.startswith("C") and len(fields) == 3:
        return ChangedQmlFile(PurePosixPath(fields[2]), None)
    return None


def _tracked_source_files(root: Path, base: str) -> list[ChangedQmlFile]:
    pathspecs = [path.as_posix() for path in SCAN_ROOTS]
    completed = _run_git(
        root, ["diff", "--name-status", "-M", base, "--", *pathspecs]
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git diff failed")
    return [
        item
        for line in completed.stdout.splitlines()
        if (item := _parse_changed_line(line))
        and item.current_path.suffix in SUPPORTED_SOURCE_SUFFIXES
    ]


def _untracked_source_files(
    root: Path, known: set[PurePosixPath]
) -> list[ChangedQmlFile]:
    pathspecs = [path.as_posix() for path in SCAN_ROOTS]
    completed = _run_git(
        root, ["ls-files", "--others", "--exclude-standard", "--", *pathspecs]
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git ls-files failed")
    return [
        ChangedQmlFile(path, None)
        for line in completed.stdout.splitlines()
        if (path := PurePosixPath(line)).suffix in SUPPORTED_SOURCE_SUFFIXES
        and path not in known
    ]


def _changed_source_files(root: Path, base: str) -> list[ChangedQmlFile]:
    changed = _tracked_source_files(root, base)
    known = {item.current_path for item in changed}
    changed.extend(_untracked_source_files(root, known))
    return sorted(changed, key=lambda item: item.current_path.as_posix())


def _base_text(root: Path, base: str, path: PurePosixPath | None) -> str:
    if path is None:
        return ""
    completed = _run_git(root, ["show", f"{base}:{path.as_posix()}"])
    if completed.returncode != 0:
        message = completed.stderr.strip()
        raise RuntimeError(f"cannot read {path} from {base}: {message}")
    return completed.stdout


def new_violations(
    current: Iterable[ViolationType], baseline: Iterable[ViolationType]
) -> list[ViolationType]:
    """Return violations not represented by the baseline. 返回基线中不存在的违规。"""
    remaining = Counter(item.fingerprint() for item in baseline)
    result: list[ViolationType] = []
    for violation in current:
        fingerprint = violation.fingerprint()
        if remaining[fingerprint] > 0:
            remaining[fingerprint] -= 1
        else:
            result.append(violation)
    return result


def _scan_changed_file(
    root: Path,
    base: str,
    item: ChangedQmlFile,
    scanner: SourceScanner[ViolationType],
) -> tuple[list[ViolationType], list[ViolationType]]:
    current_text = (root / item.current_path).read_text(encoding="utf-8")
    current = scanner(current_text, item.current_path, None)
    current = _filter_source_scope(item.current_path, current)
    if item.base_path is None:
        return current, []
    baseline_text = _base_text(root, base, item.base_path)
    baseline = scanner(baseline_text, item.base_path, item.current_path)
    return current, _filter_source_scope(item.base_path, baseline)


def scan_changed(
    root: Path, base: str, scanner: SourceScanner[ViolationType]
) -> ChangedScanResult[ViolationType]:
    """Scan changed sources against a Git baseline. 扫描源码改动相对 Git 基线的新增违规。"""
    _verify_base(root, base)
    added: list[ViolationType] = []
    current_total = 0
    base_total = 0
    changed = _changed_source_files(root, base)
    for item in changed:
        current, baseline = _scan_changed_file(root, base, item, scanner)
        current_total += len(current)
        base_total += len(baseline)
        added.extend(new_violations(current, baseline))
    return ChangedScanResult(tuple(added), len(changed), current_total, base_total)
