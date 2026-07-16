# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Atomic updater download files. Updater 原子下载文件。"""

from __future__ import annotations

import os
import tempfile
from typing import BinaryIO

from PySide6.QtCore import QStandardPaths, QUrl


_DOWNLOAD_TEMP_PREFIX = "prismqml-update-"
_DOWNLOAD_PART_SUFFIX = ".part"


def _download_suffix(url: str) -> str:
    """Preserve the URL file extension for installer dispatch. 保留安装包扩展名。"""
    suffix = os.path.splitext(QUrl(url).fileName())[1]
    return suffix or ".bin"


def open_unique_download_file(url: str) -> tuple[BinaryIO, str, str]:
    """Open a process-unique partial file. 打开进程唯一的下载临时文件。"""
    temp_dir = (
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)
        or tempfile.gettempdir()
    )
    handle = tempfile.NamedTemporaryFile(
        mode="w+b",
        prefix=_DOWNLOAD_TEMP_PREFIX,
        suffix=f"{_download_suffix(url)}{_DOWNLOAD_PART_SUFFIX}",
        dir=temp_dir,
        delete=False,
    )
    partial_path = handle.name
    final_path = partial_path[:-len(_DOWNLOAD_PART_SUFFIX)]
    return handle, partial_path, final_path


def write_download_bytes(handle: BinaryIO, payload: bytes) -> None:
    """Require a complete file write. 要求下载块完整写入。"""
    written = handle.write(payload)
    if written != len(payload):
        raise OSError(f"short download write: {written}/{len(payload)} bytes")


def commit_download_file(
    handle: BinaryIO,
    partial_path: str,
    final_path: str,
) -> None:
    """Flush, close, then atomically publish the download. 原子提交下载文件。"""
    handle.flush()
    os.fsync(handle.fileno())
    handle.close()
    os.replace(partial_path, final_path)
