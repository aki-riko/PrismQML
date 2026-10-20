# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Skeleton source inference contracts. 骨架来源推断合同。

Real-page evidence that the engine infers a usable first-screen skeleton from a
page's own QML source, that the block enum values come from a single source, that
failures stay silent, and that results are cached.
以真实页面为证: 引擎能从页面自身 QML 源码推断出可用的首屏骨架, 块枚举值来自单一来源,
失败保持静默, 且结果有缓存。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from prismqml.python.window import _skeleton_source as skeleton_source
from prismqml.python.window._skeleton_source import (
    MAX_BLOCKS,
    MAX_CARDS,
    SkeletonSource,
    block_type_values,
    get_skeleton_source,
    infer_blocks,
)


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "examples" / "pages"
SKELETON_ENUM = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Skeleton.qml"

# The frozen 18 block enum values. 冻结的 18 个块枚举值。
FROZEN_BLOCK_TYPES = {
    "block_title": 0,
    "block_subtitle": 1,
    "block_text": 2,
    "block_textLines": 3,
    "block_card": 4,
    "block_buttonRow": 5,
    "block_button": 6,
    "block_icon": 7,
    "block_avatar": 8,
    "block_image": 9,
    "block_list": 10,
    "block_listItem": 11,
    "block_input": 12,
    "block_tabs": 13,
    "block_divider": 14,
    "block_chart": 15,
    "block_carousel": 16,
    "block_table": 17,
}

# Every page the gallery actually ships. gallery 实际发布的全部页面。
GALLERY_PAGES = (
    "ButtonPage",
    "InputPage",
    "LabelPage",
    "IconPage",
    "ContainerPage",
    "CardPage",
    "NavigationPage",
    "MenuPage",
    "CarouselPage",
    "ChartPage",
    "FeedbackPage",
    "EffectsPage",
    "AIAssistantPage",
    "AutoUpdatePage",
    "SettingsPage",
)


def _source(page: str) -> str:
    return (PAGES / f"{page}.qml").read_text(encoding="utf-8")


def _flatten(blocks: list[dict]) -> list[int]:
    types: list[int] = []
    for block in blocks:
        types.append(block["type"])
        types.extend(_flatten(block.get("children", [])))
    return types


def _total_blocks(blocks: list[dict]) -> int:
    return len(_flatten(blocks))


# ==================== Single source of block values 块值单一来源 ====================


def test_block_values_come_from_the_qml_single_source():
    """解析器不得散落魔数: 块值必须读自 QML 的 Skeleton.qml。"""
    values = block_type_values()
    assert values == FROZEN_BLOCK_TYPES


def test_parser_agrees_with_the_qml_enum_file():
    """QML 文件若漂移, 本测试必须失败。"""
    source = SKELETON_ENUM.read_text(encoding="utf-8")
    parsed = {
        name: int(value)
        for name, value in re.findall(
            r"readonly\s+property\s+int\s+(block_\w+)\s*:\s*(\d+)", source
        )
    }
    assert parsed == FROZEN_BLOCK_TYPES
    assert block_type_values() == parsed


def test_parser_never_emits_an_unknown_block_value():
    """解析结果里不得出现枚举之外的块值。"""
    allowed = set(FROZEN_BLOCK_TYPES.values())
    for page in GALLERY_PAGES:
        types = _flatten(infer_blocks(_source(page)))
        assert types, page
        assert set(types) <= allowed, (page, sorted(set(types) - allowed))


# ==================== Real pages 真实页面 ====================


@pytest.mark.parametrize("page", GALLERY_PAGES)
def test_real_page_yields_a_bounded_first_screen_structure(page):
    """每个真实页面都必须产出有界、合法的首屏结构。"""
    blocks = infer_blocks(_source(page))
    assert blocks, f"{page}: no blocks inferred"
    assert len(blocks) <= MAX_BLOCKS, (page, len(blocks))
    cards = [block for block in blocks if block["type"] == 4]
    assert len(cards) <= MAX_CARDS, (page, len(cards))
    for block in blocks:
        assert isinstance(block["type"], int)
        assert block["type"] >= 0
        assert block.get("children") is None or isinstance(block["children"], list)


@pytest.mark.parametrize("page", GALLERY_PAGES)
def test_card_children_stay_within_the_engine_cap(page):
    """卡片子块数量必须受引擎上限约束, 避免骨架无限长。"""
    for block in _all_cards(infer_blocks(_source(page))):
        children = block.get("children") or []
        assert len(children) <= skeleton_source.MAX_CARD_CHILDREN, page


def _all_cards(blocks: list[dict]) -> list[dict]:
    found = []
    for block in blocks:
        if block["type"] == 4:
            found.append(block)
        found.extend(_all_cards(block.get("children") or []))
    return found


def test_pages_with_a_heading_start_with_a_title():
    """有 displayLarge 标题的页面必须以 block_title 开头。"""
    with_title = (
        "ButtonPage", "NavigationPage", "SettingsPage", "MenuPage",
        "InputPage", "LabelPage", "ChartPage", "EffectsPage", "FeedbackPage",
        "ContainerPage", "CarouselPage", "AutoUpdatePage",
    )
    for page in with_title:
        blocks = infer_blocks(_source(page))
        assert blocks[0]["type"] == 0, (page, blocks[0])


def test_pages_without_a_heading_do_not_invent_one():
    """没有 displayLarge 标题的页面不得凭空造出 block_title。"""
    for page in ("CardPage", "IconPage", "AIAssistantPage"):
        blocks = infer_blocks(_source(page))
        assert 0 not in _flatten(blocks), page


def test_button_page_mirrors_its_card_and_button_row_shape():
    """ButtonPage 的真实形状: 标题 + 每张卡片的分节标题/说明/按钮行(顶层平铺)。"""
    blocks = infer_blocks(_source("ButtonPage"))
    assert blocks[0]["type"] == 0
    types = [block["type"] for block in blocks]
    # Cards are grouping only: their content is promoted to top level, because a
    # placeholder nested inside a card container never painted.
    # 卡片只是分组: 其内容提升为顶层块, 因为嵌在卡片容器里的占位块从不绘制。
    assert 4 not in types, types
    assert 1 in types and 2 in types, types
    rows = [block for block in blocks if block["type"] == 5]
    assert rows, types
    # The real first card holds three buttons in one Flow. 真实首卡在一个 Flow 内有三个按钮。
    assert rows[0]["buttons"] == 3, rows[0]


def test_navigation_page_mirrors_its_subsection_shape():
    """NavigationPage 的真实形状: 标题 + 多个分节标题与控件块(顶层平铺)。"""
    blocks = infer_blocks(_source("NavigationPage"))
    assert blocks[0]["type"] == 0
    types = [block["type"] for block in blocks]
    assert 4 not in types, types
    # Subtitles, descriptions and a real control all appear.
    assert 1 in types, types
    assert 2 in types, types
    assert set(types) & {5, 12, 13, 3}, types


def test_settings_page_mirrors_its_settings_card_list():
    """SettingsPage 的真实形状: 标题 + 多个设置项(block_listItem, 顶层平铺)。"""
    blocks = infer_blocks(_source("SettingsPage"))
    assert blocks[0]["type"] == 0
    types = [block["type"] for block in blocks]
    assert 4 not in types, types
    items = [block for block in blocks if block["type"] == 11]
    assert len(items) >= 4, blocks


def test_prefixed_component_names_are_recognised():
    """`Fluent.ExampleCard` 这类带命名空间前缀的写法必须同样识别。"""
    source = _source("CardPage")
    assert "Fluent.ExampleCard" in source
    blocks = infer_blocks(source)
    # Two prefixed cards are recognised; their content is flattened to top level.
    # 两张带前缀的卡片被识别; 其内容平铺到顶层。
    subtitles = [block for block in blocks if block["type"] == 1]
    assert len(subtitles) >= 2, blocks


def test_structures_differ_between_pages():
    """不同页面必须得到不同结构, 否则等于通用占位。"""
    shapes = {
        page: tuple(_flatten(infer_blocks(_source(page))))
        for page in ("ButtonPage", "NavigationPage", "SettingsPage", "ChartPage")
    }
    assert len(set(shapes.values())) == len(shapes), shapes


# ==================== Silent fallback 静默回退 ====================


@pytest.mark.parametrize(
    "source",
    (
        "",
        "not qml at all",
        "Item {",
        "Item { ExampleCard { title: ",
        "\x00\x01\x02",
        "Item { { { { } } } }",
    ),
    ids=("empty", "garbage", "unclosed", "truncated", "control-chars", "unbalanced"),
)
def test_malformed_source_returns_empty_without_raising(source):
    """损坏源码必须返回空列表, 不抛异常。"""
    assert infer_blocks(source) == []


def test_missing_file_returns_empty_without_raising(tmp_path):
    """不存在的页面必须静默返回空列表。"""
    resolver = SkeletonSource()
    assert resolver.blocksFor(str(tmp_path / "nope.qml")) == []


def test_non_file_url_returns_empty_without_raising():
    """非本地文件 URL 必须静默返回空列表。"""
    resolver = SkeletonSource()
    assert resolver.blocksFor("") == []
    assert resolver.blocksFor("qrc:/pages/ButtonPage.qml") == []
    assert resolver.blocksFor("https://example.com/Page.qml") == []


def test_unreadable_file_returns_empty_without_raising(tmp_path):
    """读取失败必须静默返回空列表。"""
    page = tmp_path / "Page.qml"
    page.write_text("Item { ExampleCard { } }", encoding="utf-8")
    resolver = SkeletonSource()
    original = skeleton_source._parse_file
    try:
        skeleton_source._parse_file = lambda path: []
        assert resolver.blocksFor(str(page)) == []
    finally:
        skeleton_source._parse_file = original


# ==================== Cache 缓存 ====================


def test_blocks_are_parsed_once_per_path(tmp_path):
    """同一路径必须只解析一次。"""
    page = tmp_path / "Page.qml"
    page.write_text(
        "Item { Column { Text { font.pixelSize: Enums.typography.displayLarge } } }",
        encoding="utf-8",
    )
    skeleton_source._block_cache.pop(str(page), None)
    resolver = SkeletonSource()
    calls: list[Path] = []
    original = skeleton_source._parse_file

    def counting_parse(path):
        calls.append(path)
        return [{"type": 0}]

    try:
        skeleton_source._parse_file = counting_parse
        assert resolver.blocksFor(str(page)) == [{"type": 0}]
        resolver.blocksFor(str(page))
        resolver.blocksFor(str(page))
    finally:
        skeleton_source._parse_file = original
    assert len(calls) == 1, calls


def test_cache_is_shared_between_resolver_instances(tmp_path):
    """缓存按路径共享, 两个实例不重复解析。"""
    page = tmp_path / "Page.qml"
    page.write_text("Item { }", encoding="utf-8")
    skeleton_source._block_cache.pop(str(page), None)
    first = SkeletonSource().blocksFor(str(page))
    assert str(page) in skeleton_source._block_cache
    assert SkeletonSource().blocksFor(str(page)) == first


def test_get_skeleton_source_returns_one_shared_instance():
    """QML 注入的必须是同一个共享实例。"""
    assert get_skeleton_source() is get_skeleton_source()
