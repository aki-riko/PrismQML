# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design Gallery screenshot asset tests."""

from pathlib import Path

from PySide6.QtCore import QFile, QResource
from PySide6.QtGui import QImage


ROOT = Path(__file__).resolve().parents[2]
RESOURCE_DIR = ROOT / "examples" / "resources"
PRISM_IMAGE_DIR = RESOURCE_DIR / "image" / "prism-design"
DOCS_PRISM_IMAGE_DIR = ROOT / "docs" / "assets" / "images" / "prism-design"
DOCS_INDEX_PAGE = ROOT / "docs" / "index.zh.md"
DOCS_SKINS_PAGE = ROOT / "docs" / "guide" / "skins.zh.md"
EXPECTED_SIZE = (520, 360)


def _sample_color_count(image: QImage) -> int:
    colors = set()
    step_x = max(1, image.width() // 12)
    step_y = max(1, image.height() // 8)
    for x in range(0, image.width(), step_x):
        for y in range(0, image.height(), step_y):
            color = image.pixelColor(x, y)
            colors.add((color.red(), color.green(), color.blue(), color.alpha()))
    return len(colors)


def _assert_png_image_file(image_path: Path) -> None:
    assert image_path.is_file()
    assert image_path.stat().st_size > 10_000

    image = QImage(str(image_path))
    assert not image.isNull()
    assert (image.width(), image.height()) == EXPECTED_SIZE
    assert _sample_color_count(image) >= 8


def _assert_compare_image(asset_name: str) -> None:
    _assert_png_image_file(RESOURCE_DIR / asset_name)

    qrc_image = QImage(f":/{asset_name}")
    assert not qrc_image.isNull()
    assert (qrc_image.width(), qrc_image.height()) == EXPECTED_SIZE
    assert _sample_color_count(qrc_image) >= 8


def _assert_docs_compare_image(asset_name: str, skins_doc: str, index_doc: str) -> None:
    file_name = Path(asset_name).name
    assert f"../assets/images/prism-design/{file_name}" in skins_doc
    if file_name.endswith("-light.png"):
        assert f"assets/images/prism-design/{file_name}" in index_doc
    _assert_png_image_file(DOCS_PRISM_IMAGE_DIR / file_name)


def test_prism_design_gallery_compare_assets_are_valid(qapp):
    qrc_text = (RESOURCE_DIR / "gallery.qrc").read_text(encoding="utf-8")
    index_doc = DOCS_INDEX_PAGE.read_text(encoding="utf-8")
    skins_doc = DOCS_SKINS_PAGE.read_text(encoding="utf-8")
    rcc_path = RESOURCE_DIR / "gallery.rcc"
    assert QResource.registerResource(str(rcc_path))

    try:
        for theme_name in ("light", "dark"):
            for skin_name in ("fluent", "neobrutalism", "prism-design"):
                asset_name = f"image/prism-design/skin-compare-{skin_name}-{theme_name}.png"
                assert f"<file>{asset_name}</file>" in qrc_text
                assert QFile.exists(f":/{asset_name}")
                _assert_compare_image(asset_name)
                _assert_docs_compare_image(asset_name, skins_doc, index_doc)
    finally:
        QResource.unregisterResource(str(rcc_path))
