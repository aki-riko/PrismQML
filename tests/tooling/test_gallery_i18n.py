# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery internationalization regression tests. Gallery 国际化回归测试。"""

from __future__ import annotations

import json
from pathlib import Path

from scripts import gallery_i18n


ROOT = Path(__file__).resolve().parents[2]
I18N_ROOT = ROOT / "prismqml" / "PrismQML" / "i18n"
EXPECTED_LANGUAGES = {
    "ar", "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko",
    "nl", "pl", "pt", "ru", "th", "tr", "uk", "vi", "zh_CN", "zh_TW",
}
MANUAL_LONG_TEXT_ALLOWLISTS = {
    "ar": set(),
    "de": {"effect_slide (horizontal)"},
    "es": {
        "ScrollBar (vertical/horizontal)",
        "Vertical (orientation: Qt.Vertical)",
        "effect_slide (horizontal)",
        "effect_slide + vertical",
    },
    "fr": {
        "Vertical (orientation: Qt.Vertical)",
        "effect_slide (horizontal)",
        "effect_slide + vertical",
    },
    "hi": set(),
    "id": {"effect_slide (horizontal)"},
    "it": set(),
    "nl": set(),
    "pl": set(),
    "pt": {
        "ScrollBar (vertical/horizontal)",
        "Vertical (orientation: Qt.Vertical)",
        "effect_slide (horizontal)",
        "effect_slide + vertical",
    },
    "th": set(),
    "tr": set(),
    "uk": set(),
    "vi": set(),
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


def test_japanese_gallery_catalog_is_a_complete_manual_translation():
    japanese = _catalog("ja")
    english = _catalog("en")
    keys = gallery_i18n.referenced_keys()
    identical = {
        english[key] for key in keys
        if japanese[key] == english[key]
    }
    assert identical == {
        "InfoBar",
        "PrismQML Gallery",
        "TeachingTip",
    }


def test_korean_gallery_catalog_is_a_complete_manual_translation():
    korean = _catalog("ko")
    english = _catalog("en")
    keys = gallery_i18n.referenced_keys()
    identical = {
        english[key] for key in keys
        if korean[key] == english[key]
    }
    assert identical == {
        "InfoBar",
        "PrismQML Gallery",
        "TeachingTip",
    }


def test_russian_gallery_catalog_is_a_complete_manual_translation():
    russian = _catalog("ru")
    english = _catalog("en")
    keys = gallery_i18n.referenced_keys()
    identical = {
        english[key] for key in keys
        if russian[key] == english[key]
    }
    assert identical == {
        "InfoBar",
        "PrismQML Gallery",
        "TeachingTip",
    }


def test_completed_gallery_catalogs_have_no_untranslated_sentences():
    english = _catalog("en")
    keys = gallery_i18n.referenced_keys()
    for language, allowed in MANUAL_LONG_TEXT_ALLOWLISTS.items():
        catalog = _catalog(language)
        identical_sentences = {
            english[key] for key in keys
            if catalog[key] == english[key]
            and (len(english[key]) > 24 or len(english[key].split()) >= 3)
        }
        assert identical_sentences == allowed, language


def test_traditional_chinese_gallery_catalog_uses_reviewed_taiwan_terminology():
    traditional = _catalog("zh_TW")
    expected = {
        "标签": "標籤",
        "菜单": "選單",
        "反馈": "回饋",
        "项目经理": "專案經理",
        "复制": "複製",
        "粘贴": "貼上",
        "窗口设置": "視窗設定",
        "界面语言": "介面語系",
        "帮助文档": "說明文件",
        "Toast 的四种进度 feature": "Toast 的四種進度功能",
        "feat: 创建 gallery 分支": "feat: 建立 gallery 分支",
    }
    for source, translation in expected.items():
        assert traditional[gallery_i18n.translation_key(source)] == translation

    forbidden = {
        "標簽", "菜單", "反饋", "支持", "窗口", "文檔", "項目經理",
        "創建", "復制", "粘貼", "界面", "后端", "賬戶", "控件",
        "面包屑", "保存", "全局", "自定義", "托盤", "演示", "檢測",
        "當前", "錄入", "布局", "屏幕", "消息框", "搜索", "字符集",
        "交互", "拖拽", "運行",
    }
    values = [
        traditional[key]
        for key in gallery_i18n.referenced_keys()
    ]
    remaining = {
        phrase for phrase in forbidden
        if any(phrase in value for value in values)
    }
    assert not remaining


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
