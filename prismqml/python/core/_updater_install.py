# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Installer launch helpers for the updater. 更新器安装启动辅助函数。"""

from __future__ import annotations

import ctypes
import os
import stat
import sys

from PySide6.QtCore import QProcess, QUrl
from PySide6.QtGui import QDesktopServices

from .logger import getLogger


logger = getLogger()

if sys.platform == "win32":
    from ctypes import wintypes
else:
    wintypes = None


_SHELL_EXECUTE_ERRORS = (
    OSError,
    AttributeError,
    ctypes.ArgumentError,
    TypeError,
    ValueError,
)


def _configure_shell_execute():
    """Configure ShellExecuteW's pointer-safe ctypes contract. 配置指针安全签名。"""
    shell_execute = ctypes.windll.shell32.ShellExecuteW
    shell_execute.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_int,
    ]
    shell_execute.restype = wintypes.HINSTANCE
    return shell_execute


def launch_windows_installer(installer_path: str, args: list[str]) -> bool:
    """Launch through the manifest-aware Windows shell. 通过 Windows shell 启动。"""
    try:
        shell_execute = _configure_shell_execute()
        result = int(shell_execute(
            None, "open", installer_path, " ".join(args) or None, None, 1
        ) or 0)
    except _SHELL_EXECUTE_ERRORS as exc:
        logger.exception(
            "[Updater] 启动安装包异常: "
            f"{type(exc).__name__}: {exc}"
        )
        return False
    if result <= 32:
        logger.warning(
            f"[Updater] 启动安装包失败(ShellExecute 返回 {result}): {installer_path}"
        )
        return False
    return True


def launch_detached_installer(installer_path: str, args: list[str]) -> bool:
    """Launch through QProcess without blocking. 通过 QProcess 分离启动。"""
    ok, _pid = QProcess.startDetached(installer_path, args)
    if not ok:
        logger.warning(f"[Updater] 启动安装包失败: {installer_path}")
    return ok


def _launch_macos_installer(installer_path: str) -> bool:
    """Open a DMG or PKG with the macOS handler. 用 macOS 默认处理器打开安装包。"""
    ok, _pid = QProcess.startDetached("/usr/bin/open", [installer_path])
    if not ok:
        logger.warning(f"[Updater] 打开 macOS 安装包失败: {installer_path}")
    return ok


def _launch_linux_installer(installer_path: str, args: list[str]) -> bool:
    """Open DEB packages or execute self-contained Linux installers. 启动 Linux 安装包。"""
    if installer_path.lower().endswith(".deb"):
        ok = QDesktopServices.openUrl(QUrl.fromLocalFile(installer_path))
    else:
        try:
            mode = os.stat(installer_path).st_mode
            os.chmod(installer_path, mode | stat.S_IXUSR)
        except OSError as exc:
            logger.exception(f"[Updater] 设置安装包执行权限失败: {exc}")
            return False
        ok, _pid = QProcess.startDetached(installer_path, args)
    if not ok:
        logger.warning(f"[Updater] 启动 Linux 安装包失败: {installer_path}")
    return ok


def launch_non_windows_installer(installer_path: str, args: list[str]) -> bool:
    """Dispatch a supported non-Windows installer. 分派受支持的非 Windows 安装包。"""
    if sys.platform == "darwin":
        return _launch_macos_installer(installer_path)
    if sys.platform.startswith("linux"):
        return _launch_linux_installer(installer_path, args)
    logger.warning(f"[Updater] 当前平台不支持启动外部安装包: {installer_path}")
    return False
