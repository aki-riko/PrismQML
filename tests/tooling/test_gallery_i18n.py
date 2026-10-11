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
    # 762 = current Gallery catalog after removing the standalone parity batch.
    # 该页改成一整块对话框后，「聊天气泡 / 气泡壳 / 开始 / 中断」不再被引用；译文留在目录里备用。
    # 删除布局、集合、媒体和菜单 standalone Gallery 后，目录同步收敛到 762 条。
    # 图标页「图标组件」区块并入图标网格后，其标题 1 条引用消失：762 - 1 = 761。
    # Gallery 英文文案源化后新增 105 条：761 + 105 = 866。
    # 单词级内容标签（按钮/选项/图例）源化后新增 63 条：866 + 63 = 929。
    # 引号键导航/托盘/面板标签源化后新增 14 条：929 + 14 = 943。
    # 并行移除 Waterfall 展示后其 2 条引用消失：943 - 2 = 941。
    assert gallery_i18n.validate_catalogs() == 941


def test_gallery_sources_have_no_inline_untranslated_literals():
    # 中文源串必须已经由 --localize 转成 Translator.tr()，不得再留在源码里。
    assert gallery_i18n.localize_sources(check=True) == 0


def test_gallery_has_no_untranslated_visible_copy():
    # 用户可见的英文文案必须源化成中文并进入目录，不得硬编码。
    assert gallery_i18n.find_untranslated_copy() == []


def test_gallery_copy_policy_separates_identifiers_from_copy():
    technical = (
        "Button",
        "style_default",
        "PrismQML Gallery",
        "NavigationView / NavigationBar / ToggleNavigationBar",
        "SegmentedControl (orientation: Qt.Vertical)",
        "size / iconSize / iconColor",
        "shadowLevel: level2 / level4 / level8 / level16 / level28",
        "Indet. Ring",
        "qrc:/app_icon.svg",
        # Single tokens: API value captions, acronyms, camelCase and skin names
        # 单词级：API 取值标签、缩写、camelCase 与皮肤名
        "horizontal",
        "level16",
        "src",
        "ID",
        "A",
        "ColorDialog",
        "DropDown",
        "Fluent",
        "Neo",
        "Ticket",
        "Chip",
    )
    copy = (
        "Swipe / drag a row to reveal actions",
        "One action on the right only",
        "Pull down from the top of the list to refresh",
        "Flat selector with a sliding pill",
        "Stacked Area Chart",
        "This operation cannot be undone.",
        # Single tokens that are content labels 单词级内容标签
        "Archive",
        "Delete",
        "Mail",
        "Flag",
        "Mon",
        "Sep",
        "Filled",
        "Overview",
        "Countdown",
        "Item ",
    )
    for value in technical:
        assert gallery_i18n.is_translatable_copy(value) is False, value
    for value in copy:
        assert gallery_i18n.is_translatable_copy(value) is True, value


def test_gallery_notification_menu_uses_reviewed_chinese_terminology():
    simplified = _catalog("zh_CN")
    expected = {
        "通知管理器": "通知管理器",
        "选择通知类型、承载区域和弹出位置": "选择通知类型、承载区域和弹出位置",
        "消息条": "消息条",
        "吐司": "吐司",
        "窗口内部": "窗口内部",
        "窗口外部": "窗口外部",
        "桌面": "桌面",
        "左侧位置": "左侧位置",
        "中心位置": "中心位置",
        "右侧位置": "右侧位置",
    }
    for source, translation in expected.items():
        assert simplified[gallery_i18n.translation_key(source)] == translation


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
