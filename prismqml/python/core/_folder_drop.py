# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Local folder drop validation for QML. QML 本地文件夹拖放校验。"""

from PySide6.QtCore import QDir, QFileInfo, QUrl


def resolve_dropped_folder_path(folder_url: QUrl) -> str:
    """Return one validated local folder path. 返回通过校验的本地文件夹路径。"""
    if (
        not folder_url.isValid()
        or not folder_url.isLocalFile()
        or folder_url.host()
        or folder_url.hasQuery()
        or folder_url.hasFragment()
    ):
        return ""
    local_path = folder_url.toLocalFile()
    normalized_path = QDir.fromNativeSeparators(local_path)
    if (
        not local_path
        or "\x00" in local_path
        or normalized_path.startswith("//")
    ):
        return ""
    file_info = QFileInfo(local_path)
    if (
        not file_info.isAbsolute()
        or not file_info.exists()
        or not file_info.isDir()
    ):
        return ""
    return QDir.cleanPath(file_info.absoluteFilePath())
