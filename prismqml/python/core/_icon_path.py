# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared icon source resolution. 图标来源共享解析。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl


def resolve_icon_path(icon: str) -> str:
    """Resolve file/qrc URLs and local paths for Qt loaders. 解析 Qt 图标路径。"""
    if not icon:
        return ""
    if icon.startswith(":/"):
        return icon

    url = QUrl(icon)
    if url.isLocalFile():
        return url.toLocalFile()
    if url.scheme().lower() == "qrc":
        return ":/" + url.path().lstrip("/")
    return str(Path(icon).resolve())


def resolve_provider_path(provider_id: str) -> str:
    """Decode one QML provider-id layer, then resolve its path. 解码一层 provider id。"""
    url = QUrl(provider_id)
    if url.isLocalFile() or url.scheme().lower() == "qrc":
        return resolve_icon_path(provider_id)
    decoded = QUrl.fromPercentEncoding(provider_id.encode("utf-8"))
    return resolve_icon_path(decoded)
