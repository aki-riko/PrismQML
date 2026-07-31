# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Dropped folder URL validation contracts. 拖入文件夹 URL 校验合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QDir, QFileInfo, QUrl

from prismqml.python.core.window_helper import WindowHelper


WINDOW_HELPER_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "prismqml"
    / "python"
    / "core"
    / "window_helper.py"
)


def test_resolve_dropped_folder_path_accepts_real_encoded_directory(
    tmp_path: Path,
) -> None:
    """A real local directory keeps decoded special characters. 保留解码后的特殊字符。"""
    folder = tmp_path / "拖 放#百分%"
    folder.mkdir()

    actual = WindowHelper().resolveDroppedFolderPath(QUrl.fromLocalFile(str(folder)))

    expected = QDir.cleanPath(QFileInfo(str(folder)).absoluteFilePath())
    assert actual == expected


def test_window_helper_defers_folder_drop_implementation_import() -> None:
    """Folder validation loads on the first real drop. 文件夹校验仅在真实拖放时加载。"""
    source = WINDOW_HELPER_SOURCE.read_text(encoding="utf-8")
    assert "from ._folder_drop import FolderDropPathHelper" not in source
    assert "        from ._folder_drop import resolve_dropped_folder_path" in source


def test_resolve_dropped_folder_path_rejects_file_and_missing_path(
    tmp_path: Path,
) -> None:
    """Only an existing directory is accepted. 仅接受真实存在的目录。"""
    regular_file = tmp_path / "not-a-folder.txt"
    regular_file.write_text("fixture", encoding="utf-8")
    missing = tmp_path / "missing"
    helper = WindowHelper()

    assert helper.resolveDroppedFolderPath(QUrl.fromLocalFile(str(regular_file))) == ""
    assert helper.resolveDroppedFolderPath(QUrl.fromLocalFile(str(missing))) == ""


def test_resolve_dropped_folder_path_rejects_query_and_fragment(
    tmp_path: Path,
) -> None:
    """A folder drop must be an unambiguous file URL. 文件夹 URL 不得携带附加组件。"""
    folder = tmp_path / "folder"
    folder.mkdir()
    plain_url = QUrl.fromLocalFile(str(folder))
    query_url = QUrl(plain_url)
    query_url.setQuery("source=drop")
    fragment_url = QUrl(plain_url)
    fragment_url.setFragment("section")
    helper = WindowHelper()

    assert helper.resolveDroppedFolderPath(query_url) == ""
    assert helper.resolveDroppedFolderPath(fragment_url) == ""


@pytest.mark.parametrize(
    "source",
    [
        "",
        "relative/folder",
        "https://example.com/folder",
        "qrc:/folder",
        "file://server/share",
        "file:////?/C:/Windows",
    ],
)
def test_resolve_dropped_folder_path_rejects_untrusted_urls(source: str) -> None:
    """Remote, relative and device-style URLs are rejected before lookup. 查询前拒绝不可信 URL。"""
    assert WindowHelper().resolveDroppedFolderPath(QUrl(source)) == ""
