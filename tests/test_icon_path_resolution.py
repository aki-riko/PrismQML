# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Icon file URL resolution regressions. 图标文件 URL 解析回归。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QIcon, QImage

from prismqml.python.core.window_helper import WindowHelper
from prismqml.python.window.system_tray import SystemTrayIcon
from prismqml.python.window.window_core import WindowCore


def _normalized(path: str) -> str:
    """Normalize separators without changing URL-decoded characters. 归一化分隔符。"""
    return path.replace("\\", "/")


def _encoded_file_url(path: Path) -> str:
    """Build the same fully encoded URL that QML receives. 构造 QML 实际 URL。"""
    return bytes(QUrl.fromLocalFile(str(path)).toEncoded()).decode("ascii")


def _write_real_icon(path: Path) -> None:
    """Write a real bitmap used by every public icon path. 写入真实图标。"""
    image = QImage(8, 8, QImage.Format.Format_ARGB32)
    image.fill(QColor("#d02040"))
    assert image.save(str(path))


def _load_icon(entrypoint: str, qapp, source: str) -> QIcon:
    """Load through one public Python entrypoint. 经一个公开入口加载。"""
    if entrypoint == "WindowHelper":
        WindowHelper().setAppIcon(source)
        return qapp.windowIcon()
    if entrypoint == "WindowCore":
        WindowCore._setAppIcon(None, source)
        return qapp.windowIcon()
    tray = SystemTrayIcon()
    try:
        tray.setIcon(source)
        return tray.icon()
    finally:
        tray.deleteLater()
        qapp.processEvents()


@pytest.mark.parametrize(
    "source",
    [
        "file:///C:/Icons/A%20B/%23mark%25.png",
        "file://server/share/A%20B/%23mark.png",
        "file:///home/user/A%20B/%23mark%25%3F.svg",
    ],
)
def test_window_helper_decodes_file_urls(source: str) -> None:
    """file URLs must follow QUrl.toLocalFile on every platform. 遵循 Qt 合同。"""
    assert WindowHelper._resolveIconPath(source) == QUrl(source).toLocalFile()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("qrc:/icons/A%20B.svg", ":/icons/A B.svg"),
        ("qrc:///icons/A%20B.svg", ":/icons/A B.svg"),
        (":/icons/A B.svg", ":/icons/A B.svg"),
    ],
)
def test_window_helper_normalizes_resource_urls(source: str, expected: str) -> None:
    """qrc variants must resolve to one QFile resource path. qrc 归一为资源路径。"""
    assert WindowHelper._resolveIconPath(source) == expected


@pytest.mark.parametrize(
    "entrypoint",
    ["WindowHelper", "WindowCore", "SystemTrayIcon"],
)
def test_encoded_real_icon_loads_through_python_entrypoint(
    entrypoint: str,
    qapp,
    tmp_path: Path,
) -> None:
    """Each Python entrypoint loads one real encoded path. 各入口加载真实路径。"""
    icon_path = tmp_path / "图 标#百分%.png"
    _write_real_icon(icon_path)
    source = _encoded_file_url(icon_path)
    assert QUrl(source).toLocalFile() == _normalized(str(icon_path))
    assert not QIcon(str(icon_path)).isNull()
    assert QIcon(source).isNull()

    original_icon = qapp.windowIcon()
    before_widgets = set(qapp.topLevelWidgets())
    try:
        qapp.setWindowIcon(QIcon())
        assert not _load_icon(entrypoint, qapp, source).isNull()
        assert set(qapp.topLevelWidgets()) == before_widgets
    finally:
        qapp.setWindowIcon(original_icon)
