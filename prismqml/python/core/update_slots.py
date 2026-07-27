# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Windows A/B update-slot resolution. Windows A/B 更新槽解析。"""

from __future__ import annotations

import configparser
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

from PySide6.QtCore import QObject, QTimer, Signal

from ._updater_install import launch_windows_installer
from .logger import getLogger


logger = getLogger()
SLOT_A = "A"
SLOT_B = "B"
SLOT_STATE_FILENAME = "prism-update-slot.ini"
_SLOT_NAMES = frozenset((SLOT_A, SLOT_B))
_PREPARATION_POLL_MS = 500
_PREPARATION_TIMEOUT_SECONDS = 15 * 60


def _normalize_slot(value: str) -> str:
    normalized = str(value or "").strip().upper()
    return normalized if normalized in _SLOT_NAMES else ""


def _executable_path(executable: Optional[os.PathLike | str]) -> Path:
    return Path(executable or sys.executable).resolve(strict=False)


def current_update_slot(executable: Optional[os.PathLike | str] = None) -> str:
    """Return the A/B slot containing one executable, or an empty string."""
    return _normalize_slot(_executable_path(executable).parent.name.removeprefix("slot-"))


def update_root(executable: Optional[os.PathLike | str] = None) -> Optional[Path]:
    """Return the shared install root for a slot executable."""
    path = _executable_path(executable)
    slot = current_update_slot(path)
    if not slot:
        return None
    return path.parent.parent


def slot_state_path(executable: Optional[os.PathLike | str] = None) -> Optional[Path]:
    root = update_root(executable)
    return root / SLOT_STATE_FILENAME if root else None


def executable_for_slot(
    slot: str, executable: Optional[os.PathLike | str] = None
) -> Optional[Path]:
    normalized = _normalize_slot(slot)
    root = update_root(executable)
    if not normalized or root is None:
        return None
    return root / f"slot-{normalized.lower()}" / _executable_path(executable).name


def read_launch_slot(executable: Optional[os.PathLike | str] = None) -> str:
    """Read the installer-written next-launch slot without broad path access."""
    state_path = slot_state_path(executable)
    if state_path is None or not state_path.is_file():
        return ""
    try:
        raw = state_path.read_bytes()
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw[:32]:
            text = raw.decode("utf-16")
        else:
            text = raw.decode("utf-8-sig")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(text)
        return _normalize_slot(parser.get("Slots", "LaunchSlot", fallback=""))
    except (OSError, UnicodeError, configparser.Error) as exc:
        logger.warning(f"[UpdaterSlots] 读取槽位状态失败: {state_path}: {exc}")
        return ""


def redirect_to_active_update_slot(
    arguments: Optional[Sequence[str]] = None,
    executable: Optional[os.PathLike | str] = None,
) -> bool:
    """Start the installer-selected slot and return whether the caller must exit."""
    if sys.platform != "win32":
        return False
    current = current_update_slot(executable)
    target = read_launch_slot(executable)
    if not current or not target or target == current:
        return False
    target_executable = executable_for_slot(target, executable)
    if target_executable is None or not target_executable.is_file():
        logger.warning(f"[UpdaterSlots] 目标槽可执行文件不存在: {target_executable}")
        return False
    forwarded = list(sys.argv[1:] if arguments is None else arguments)
    if not _start_slot_executable(target_executable, forwarded):
        return False
    logger.info(
        f"[UpdaterSlots] 已从 slot-{current.lower()} 切换到 slot-{target.lower()}"
    )
    return True


def _start_slot_executable(target: Path, arguments: list[str]) -> bool:
    creation_flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    try:
        subprocess.Popen(
            [str(target), *arguments],
            cwd=str(target.parent),
            close_fds=True,
            creationflags=creation_flags,
        )
    except OSError as exc:
        logger.exception(f"[UpdaterSlots] 启动目标槽失败: {exc}")
        return False
    return True


def opposite_slot(slot: str) -> str:
    normalized = _normalize_slot(slot)
    return SLOT_B if normalized == SLOT_A else SLOT_A if normalized == SLOT_B else ""


def _installer_arguments(silent_args: str, current_slot: str) -> list[str]:
    arguments = [
        argument
        for argument in silent_args.split(" ")
        if argument
        and not argument.upper().startswith("/PRISMCURRENTSLOT=")
    ]
    arguments.append(f"/PRISMCURRENTSLOT={current_slot}")
    return arguments


class SlotUpdatePreparation(QObject):
    """Launch and observe one inactive-slot installation. 启动并观察双槽安装。"""

    finished = Signal()
    failed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._preparing = False
        self._next_launch_prepared = False
        self._target_slot = ""
        self._deadline = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(_PREPARATION_POLL_MS)
        self._timer.timeout.connect(self._poll)

    @property
    def next_launch_prepared(self) -> bool:
        return self._next_launch_prepared

    def stage(self, installer_path: str, silent_args: str = "") -> bool:
        if sys.platform != "win32" or self._preparing or self._next_launch_prepared:
            logger.warning("[Updater] 双槽更新不可重复启动或当前平台不受支持")
            return False
        if not installer_path or not os.path.isfile(installer_path):
            logger.warning(f"[Updater] 安装包不存在: {installer_path}")
            return False
        current_slot = current_update_slot()
        target_slot = opposite_slot(current_slot)
        if not current_slot or not target_slot:
            logger.warning("[Updater] 当前可执行文件不在 slot-a/slot-b 中")
            return False
        if not launch_windows_installer(
            installer_path, _installer_arguments(silent_args, current_slot)
        ):
            return False
        self._begin_wait(target_slot)
        return True

    def _begin_wait(self, target_slot: str) -> None:
        self._preparing = True
        self._target_slot = target_slot
        self._deadline = time.monotonic() + _PREPARATION_TIMEOUT_SECONDS
        self._timer.start()
        logger.info(
            f"[Updater] 已在后台准备 slot-{target_slot.lower()},当前进程继续运行"
        )

    def _poll(self) -> None:
        if not self._preparing:
            self._timer.stop()
            return
        target_executable = executable_for_slot(self._target_slot)
        if self._target_is_ready(target_executable):
            self._finish()
        elif time.monotonic() >= self._deadline:
            self._fail_timeout()

    def _target_is_ready(self, target_executable: Optional[Path]) -> bool:
        return (
            read_launch_slot() == self._target_slot
            and target_executable is not None
            and target_executable.is_file()
        )

    def _finish(self) -> None:
        self._preparing = False
        self._next_launch_prepared = True
        self._timer.stop()
        logger.info("[Updater] 双槽安装完成,下次启动将切换到新版")
        self.finished.emit()

    def _fail_timeout(self) -> None:
        self._preparing = False
        self._timer.stop()
        logger.warning("[Updater] 双槽安装等待超时")
        self.failed.emit("后台安装未在规定时间内完成")
