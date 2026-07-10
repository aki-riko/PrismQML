# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Safely synchronize Microsoft Fluent UI SVG assets. 安全同步 Fluent 图标。"""

import argparse
import hashlib
import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

if __package__:
    from .extract_icons import render_outputs, validate_icon_names, validate_svg_file
    from .maintenance_io import MovePath, move_path, remove_path, replace_many
else:
    from extract_icons import render_outputs, validate_icon_names, validate_svg_file
    from maintenance_io import MovePath, move_path, remove_path, replace_many


logger = logging.getLogger("prismqml.icon_sync")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "fluentui-system-icons" / "assets"
DEFAULT_TARGET_DIR = PROJECT_ROOT / "prismqml" / "PrismQML" / "controls" / "icons" / "fluent"
DEFAULT_PYTHON_OUTPUT = PROJECT_ROOT / "prismqml" / "python" / "core" / "icons.py"
DEFAULT_QML_OUTPUT = PROJECT_ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Icons.qml"
SOURCE_SIZE_PRIORITY = (20, 24, 16)
MIN_EXPECTED_ICON_COUNT = 2497
REQUIRED_ICON_NAMES = frozenset({"Add", "Dismiss", "Search", "Settings"})
CopyFile = Callable[[Path, Path], object]


class IconSyncMismatch(ValueError):
    """Raised when check mode finds stale synchronized outputs. 同步检查不一致。"""


@dataclass(frozen=True)
class IconSource:
    """One selected upstream icon source. 一个已选中的上游图标。"""

    name: str
    path: Path


def _select_svg(icon_folder: Path) -> Optional[Path]:
    svg_folder = icon_folder / "SVG"
    if not svg_folder.is_dir():
        return None
    for size in SOURCE_SIZE_PRIORITY:
        matches = sorted(svg_folder.glob(f"*_{size}_regular.svg"))
        if len(matches) > 1:
            raise ValueError(f"ambiguous regular SVG variants: {matches}")
        if matches:
            return matches[0]
    return None


def collect_source_icons(
    source_dir: Path,
    minimum_icons: int = MIN_EXPECTED_ICON_COUNT,
    required_icons: Sequence[str] = tuple(REQUIRED_ICON_NAMES),
) -> list[IconSource]:
    """Select and validate all upstream icons before writing. 写入前选择并验证上游图标。"""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Fluent icon source does not exist: {source_dir}")
    selected = []
    for icon_folder in sorted(source_dir.iterdir(), key=lambda path: path.name.casefold()):
        source_svg = _select_svg(icon_folder) if icon_folder.is_dir() else None
        if source_svg is None:
            continue
        name = icon_folder.name.replace(" ", "")
        validate_svg_file(source_svg)
        selected.append(IconSource(name, source_svg))
    _validate_source_set(selected, minimum_icons, required_icons)
    return selected


def _validate_source_set(
    selected: Sequence[IconSource], minimum_icons: int, required_icons: Sequence[str]
) -> None:
    names = [item.name for item in selected]
    validate_icon_names(names)
    if len(names) < minimum_icons:
        raise ValueError(f"expected at least {minimum_icons} icons, found {len(names)}")
    missing = sorted(set(required_icons) - set(names))
    if missing:
        raise ValueError(f"required Fluent icons are missing: {missing}")


def _copy_to_stage(
    selected: Sequence[IconSource], staged_icons: Path, copy_file: CopyFile
) -> None:
    staged_icons.mkdir()
    for item in selected:
        destination = staged_icons / f"{item.name}.svg"
        copy_file(item.path, destination)
        validate_svg_file(destination)


def _write_stage_file(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def _file_manifest(directory: Path) -> list[tuple[str, str]]:
    if not directory.is_dir():
        return []
    manifest = []
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.append((path.relative_to(directory).as_posix(), digest))
    return manifest


def _check_staged_outputs(
    staged: Sequence[tuple[Path, Path]], staged_icons: Path, target_dir: Path
) -> None:
    mismatches = []
    if _file_manifest(staged_icons) != _file_manifest(target_dir):
        mismatches.append(str(target_dir))
    for source, destination in staged[1:]:
        if not destination.is_file() or source.read_bytes() != destination.read_bytes():
            mismatches.append(str(destination))
    if mismatches:
        raise IconSyncMismatch(f"synchronized icon outputs are stale: {mismatches}")


def _prepare_stage(
    selected: Sequence[IconSource], stage_root: Path, copy_file: CopyFile
) -> list[tuple[Path, str]]:
    staged_icons = stage_root / "fluent"
    _copy_to_stage(selected, staged_icons, copy_file)
    python_content, qml_content = render_outputs([item.name for item in selected])
    staged_files = [
        (stage_root / "icons.py", python_content),
        (stage_root / "Icons.qml", qml_content),
    ]
    for path, content in staged_files:
        _write_stage_file(path, content)
    return staged_files


def _replacement_pairs(
    stage_root: Path,
    staged_files: Sequence[tuple[Path, str]],
    destinations: Sequence[Path],
) -> list[tuple[Path, Path]]:
    staged = [(stage_root / "fluent", destinations[0])]
    staged.extend(
        (path, destination)
        for (path, _), destination in zip(staged_files, destinations[1:])
    )
    return staged


def _apply_stage(
    staged: Sequence[tuple[Path, Path]],
    target_dir: Path,
    check: bool,
    mover: MovePath,
) -> None:
    if check:
        _check_staged_outputs(staged, staged[0][0], target_dir)
    else:
        replace_many(staged, mover=mover)


def sync_icons(
    source_dir: Path = DEFAULT_SOURCE_DIR,
    target_dir: Path = DEFAULT_TARGET_DIR,
    python_output: Path = DEFAULT_PYTHON_OUTPUT,
    qml_output: Path = DEFAULT_QML_OUTPUT,
    check: bool = False,
    minimum_icons: int = MIN_EXPECTED_ICON_COUNT,
    required_icons: Sequence[str] = tuple(REQUIRED_ICON_NAMES),
    copy_file: CopyFile = shutil.copy2,
    mover: MovePath = move_path,
) -> int:
    """Synchronize SVG and generated registries without partial updates. 原子同步资源。"""
    selected = collect_source_icons(source_dir, minimum_icons, required_icons)
    destinations = [Path(target_dir), Path(python_output), Path(qml_output)]
    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=".copy-all-icons-", dir=destinations[0].parent))
    try:
        staged_files = _prepare_stage(selected, stage_root, copy_file)
        staged = _replacement_pairs(stage_root, staged_files, destinations)
        _apply_stage(staged, destinations[0], check, mover)
    finally:
        remove_path(stage_root)
    return len(selected)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments. 解析命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET_DIR)
    parser.add_argument("--python-output", type=Path, default=DEFAULT_PYTHON_OUTPUT)
    parser.add_argument("--qml-output", type=Path, default=DEFAULT_QML_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run safe icon synchronization. 执行安全图标同步。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        count = sync_icons(
            args.source, args.target, args.python_output, args.qml_output, args.check
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        logger.error("icon synchronization failed: %s", exc)
        return 1
    except Exception:
        logger.exception("unexpected icon synchronization failure")
        return 1
    logger.info("validated %s Fluent icons", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
