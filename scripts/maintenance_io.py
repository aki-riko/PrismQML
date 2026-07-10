# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Transactional helpers for maintenance scripts. 维护脚本事务辅助函数。"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Callable, Iterable, Sequence, Tuple


logger = logging.getLogger("prismqml.maintenance")
PathPair = Tuple[Path, Path]
MovePath = Callable[[Path, Path], None]


def move_path(source: Path, destination: Path) -> None:
    """Move one staged path into place. 将一个暂存路径移入目标位置。"""
    source.replace(destination)


def remove_path(path: Path) -> None:
    """Remove a known temporary or backup path. 删除已知临时或备份路径。"""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _validate_replacements(replacements: Sequence[PathPair]) -> None:
    destinations = []
    for source, destination in replacements:
        if not source.exists():
            raise FileNotFoundError(f"staged path does not exist: {source}")
        resolved = destination.resolve(strict=False)
        if resolved == Path(resolved.anchor):
            raise ValueError(f"refusing to replace filesystem root: {destination}")
        if not destination.parent.is_dir():
            raise FileNotFoundError(f"destination parent does not exist: {destination.parent}")
        destinations.append(resolved)
    if len(destinations) != len(set(destinations)):
        raise ValueError("replacement destinations must be unique")


def _restore_originals(
    installed: Iterable[Path], backups: Sequence[PathPair], mover: MovePath
) -> None:
    for destination in reversed(list(installed)):
        remove_path(destination)
    for destination, backup in reversed(backups):
        if backup.exists():
            mover(backup, destination)


def _cleanup_backups(backups: Iterable[PathPair]) -> None:
    for _, backup in backups:
        try:
            remove_path(backup)
        except OSError as exc:
            logger.warning("backup cleanup failed for %s: %s", backup, exc)


def replace_many(
    replacements: Iterable[PathPair], mover: MovePath = move_path
) -> None:
    """Replace multiple paths with rollback on commit failure. 事务替换多个路径。"""
    normalized = [(Path(source), Path(destination)) for source, destination in replacements]
    _validate_replacements(normalized)
    token = uuid.uuid4().hex
    backups = []
    installed = []
    try:
        for _, destination in normalized:
            if destination.exists():
                backup = destination.with_name(f".{destination.name}.backup-{token}")
                mover(destination, backup)
                backups.append((destination, backup))
        for source, destination in normalized:
            mover(source, destination)
            installed.append(destination)
    except (Exception, KeyboardInterrupt) as original_error:
        logger.error("replacement commit failed; rolling back", exc_info=True)
        try:
            _restore_originals(installed, backups, mover)
        except (Exception, KeyboardInterrupt) as rollback_error:
            logger.error("replacement rollback failed", exc_info=True)
            raise RuntimeError(
                f"replacement failed and rollback failed: {rollback_error}"
            ) from original_error
        raise
    _cleanup_backups(backups)
