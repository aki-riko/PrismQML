# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery internationalization regression tests. Gallery 国际化回归测试。"""

from __future__ import annotations

import json
from pathlib import Path

from scripts import gallery_i18n


ROOT = Path(__file__).resolve().parents[1]
I18N_ROOT = ROOT / "prismqml" / "PrismQML" / "i18n"
EXPECTED_LANGUAGES = {
    "ar", "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko",
    "nl", "pl", "pt", "ru", "th", "tr", "uk", "vi", "zh_CN", "zh_TW",
}


def _catalog(language: str) -> dict[str, str]:
    return json.loads((I18N_ROOT / f"{language}.json").read_text(encoding="utf-8"))


def test_gallery_catalogs_cover_every_supported_language():
    assert {path.stem for path in I18N_ROOT.glob("*.json")} == EXPECTED_LANGUAGES
    assert gallery_i18n.validate_catalogs() == 742


def test_non_chinese_gallery_catalogs_do_not_reuse_source_strings():
    keys = gallery_i18n.referenced_keys()
    source = _catalog("zh_CN")
    neutral = {
        key for key in keys
        if _catalog("en")[key] == source[key]
    }
    for language in EXPECTED_LANGUAGES - {"zh_CN", "zh_TW", "ja"}:
        catalog = _catalog(language)
        untranslated = [
            key for key in keys
            if catalog[key] == source[key] and key not in neutral
        ]
        assert not untranslated, f"{language}: {untranslated}"


def test_japanese_only_reuses_intentionally_shared_ideographs():
    source = _catalog("zh_CN")
    japanese = _catalog("ja")
    english = _catalog("en")
    keys = gallery_i18n.referenced_keys()
    identical = {
        source[key] for key in keys
        if japanese[key] == source[key] and english[key] != source[key]
    }
    assert identical == {
        "effect_slide + 垂直", "effect_slide (水平)", "ScrollBar (垂直/水平)",
        "右", "左", "成功", "警告", "垂直", "水平", "保存", "音量",
    }


def test_english_gallery_catalog_is_a_complete_manual_baseline():
    source = _catalog("zh_CN")
    english = _catalog("en")
    keys = gallery_i18n.referenced_keys()
    identical = {
        key for key in keys
        if english[key] == source[key]
    }
    assert identical == {
        gallery_i18n.translation_key("Labels, Badges, Chips, Tags"),
        gallery_i18n.translation_key("Git graph · 150% DPI"),
        gallery_i18n.translation_key("PrismQML Gallery"),
    }
