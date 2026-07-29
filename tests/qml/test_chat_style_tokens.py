# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Chat style token runtime regressions. 聊天样式令牌运行时回归测试。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
CHAT_ROOT = ROOT / "prismqml" / "PrismQML" / "controls" / "chat"
SOURCE_TOKEN_REFERENCES = {
    CHAT_ROOT / "CodeBlock.qml": {
        "Enums.codeBlockColors.background",
        "Enums.codeBlockColors.border",
        "Enums.codeBlockColors.secondaryText",
        "Enums.codeBlockColors.hover",
        "Enums.codeBlockColors.copySuccess",
        "Enums.codeBlockColors.foreground",
        "Enums.controlSize.codeBlockDefaultWidth",
        "Enums.controlSize.codeBlockHeaderHeight",
        "Enums.controlSize.codeBlockCopyButtonWidth",
        "Enums.controlSize.codeBlockCopyButtonHeight",
        "Enums.typography.captionCompact",
        "Enums.duration.copyFeedback",
    },
    CHAT_ROOT / "MarkdownView.qml": {
        "Enums.controlSize.chatContentMaxWidth",
        "Enums.spacing.m",
        "Enums.typography.body",
    },
    CHAT_ROOT / "ChatBubble.qml": {"Enums.controlSize.chatContentMaxWidth"},
    CHAT_ROOT / "ChatMessageList.qml": {"Enums.controlSize.chatContentMaxWidth"},
}
COMPACT_CAPTION_CONSUMERS = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "menus" / "Action.qml",
    ROOT / "prismqml" / "PrismQML" / "navigation" / "NavigationBarItem.qml",
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "DataWidgetCore.qml",
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Badge" / "Badge.qml",
    ROOT / "examples" / "pages" / "MenuPage.qml",
)

LEGACY_COLORS = {
    "expectedBackground": QColor("#1E1E1E"),
    "expectedBorder": QColor.fromRgbF(1.0, 1.0, 1.0, 0.08),
    "expectedSecondaryText": QColor("#9CA3AF"),
    "expectedHover": QColor.fromRgbF(1.0, 1.0, 1.0, 0.1),
    "expectedCopySuccess": QColor("#10B981"),
    "expectedForeground": QColor("#E5E7EB"),
    "expectedTransparent": QColor("transparent"),
}
LEGACY_METRICS = {
    "expectedBorderThin": 1,
    "expectedChatContentMaxWidth": 600,
    "expectedCodeBlockDefaultWidth": 400,
    "expectedCodeBlockHeaderHeight": 24,
    "expectedCopyButtonWidth": 50,
    "expectedCopyButtonHeight": 22,
    "expectedCaptionCompact": 11,
    "expectedCaption": 12,
    "expectedBody": 14,
    "expectedCopyFeedback": 1500,
    "expectedSpacingXs": 4,
    "expectedSpacingM": 8,
    "expectedSpacingL": 12,
    "expectedSpacingXl": 16,
    "expectedRadiusSmall": 4,
}

WINDOW_SOURCE = br"""import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property color expectedBackground: Enums.codeBlockColors.background
    readonly property color expectedBorder: Enums.codeBlockColors.border
    readonly property color expectedSecondaryText: Enums.codeBlockColors.secondaryText
    readonly property color expectedHover: Enums.codeBlockColors.hover
    readonly property color expectedCopySuccess: Enums.codeBlockColors.copySuccess
    readonly property color expectedForeground: Enums.codeBlockColors.foreground
    readonly property color expectedTransparent: Enums.transparent
    readonly property int expectedBorderThin: Enums.border.thin
    readonly property int expectedChatContentMaxWidth:
        Enums.controlSize.chatContentMaxWidth
    readonly property int expectedCodeBlockDefaultWidth:
        Enums.controlSize.codeBlockDefaultWidth
    readonly property int expectedCodeBlockHeaderHeight:
        Enums.controlSize.codeBlockHeaderHeight
    readonly property int expectedCopyButtonWidth:
        Enums.controlSize.codeBlockCopyButtonWidth
    readonly property int expectedCopyButtonHeight:
        Enums.controlSize.codeBlockCopyButtonHeight
    readonly property int expectedCaptionCompact: Enums.typography.captionCompact
    readonly property int expectedCaption: Enums.typography.caption
    readonly property int expectedBody: Enums.typography.body
    readonly property int expectedCopyFeedback: Enums.duration.copyFeedback
    readonly property int expectedSpacingXs: Enums.spacing.xs
    readonly property int expectedSpacingM: Enums.spacing.m
    readonly property int expectedSpacingL: Enums.spacing.l
    readonly property int expectedSpacingXl: Enums.spacing.xl
    readonly property int expectedRadiusSmall: Enums.radius.small

    visible: false
    width: 900
    height: 700

    CodeBlock {
        objectName: "directCodeBlock"
        code: "const answer = 42"
        language: "js"
    }

    MarkdownView {
        objectName: "markdownView"
        y: 100
        width: root.expectedChatContentMaxWidth
        markdown: "paragraph\n\n```py\nx = 1\n```"
    }

    ChatBubble {
        objectName: "chatBubble"
        y: 300
        width: 800
    }

    ChatMessageList {
        objectName: "chatMessageList"
        y: 500
        width: 800
        height: 100
    }
}
"""
DETACHED_MARKDOWN_SOURCE = b"""import QtQuick
import PrismQML
MarkdownView {}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create(engine: QQmlApplicationEngine, source: bytes, name: str):
    component = QQmlComponent(engine)
    component.setData(source, QUrl(f"inline:{name}"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _evaluate(instance: QObject, expression_source: str):
    expression = QQmlExpression(
        QQmlEngine.contextForObject(instance), instance, expression_source
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert is_undefined is False
    return result


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _find_text(root: QQuickItem, text: str) -> QQuickItem:
    matches = [
        item
        for item in _walk_visual_tree(root)
        if item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == text
    ]
    assert len(matches) == 1, (
        text,
        [item.metaObject().className() for item in matches],
    )
    return matches[0]


def _find_only_text(root: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _walk_visual_tree(root)
        if item.metaObject().indexOfProperty("text") >= 0
    ]
    assert len(matches) == 1, [
        (item.metaObject().className(), item.property("text")) for item in matches
    ]
    return matches[0]


def _find_code_block(root: QQuickItem, code: str) -> QQuickItem:
    matches = [
        item
        for item in _walk_visual_tree(root)
        if item.metaObject().indexOfProperty("code") >= 0
        and item.property("code") == code
    ]
    assert len(matches) == 1, (
        code,
        [item.metaObject().className() for item in matches],
    )
    return matches[0]


def _find_copy_area(code_block: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _walk_visual_tree(code_block)
        if item.metaObject().indexOfProperty("_copied") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _copy_timer(copy_area: QQuickItem) -> QObject:
    timers = [
        child
        for child in copy_area.findChildren(QObject)
        if child.parent() is copy_area
        and child.metaObject().indexOfProperty("interval") >= 0
    ]
    assert len(timers) == 1
    return timers[0]


def _assert_color(actual: QColor, expected: QColor) -> None:
    actual_channels = (actual.redF(), actual.greenF(), actual.blueF(), actual.alphaF())
    expected_channels = (
        expected.redF(),
        expected.greenF(),
        expected.blueF(),
        expected.alphaF(),
    )
    assert actual_channels == pytest.approx(expected_channels, abs=1 / 65535)


def _assert_legacy_tokens(window: QQuickWindow) -> None:
    for property_name, expected in LEGACY_COLORS.items():
        _assert_color(window.property(property_name), expected)
    for property_name, expected in LEGACY_METRICS.items():
        assert window.property(property_name) == expected


def _code_block_parts(code_block: QQuickItem, language: str, code: str) -> dict:
    copy_area = _find_copy_area(code_block)
    copy_text = _find_only_text(copy_area)
    return {
        "language": _find_text(code_block, language),
        "code": _find_text(code_block, code),
        "copy_area": copy_area,
        "copy_background": copy_text.parentItem(),
        "copy_text": copy_text,
        "header": copy_area.parentItem(),
        "timer": _copy_timer(copy_area),
    }


def _assert_code_block_geometry(
    window: QQuickWindow, code_block: QQuickItem, parts: dict
) -> None:
    assert code_block.implicitWidth() == window.property(
        "expectedCodeBlockDefaultWidth"
    )
    assert code_block.property("radius") == window.property("expectedRadiusSmall")
    assert _evaluate(code_block, "border.width") == window.property(
        "expectedBorderThin"
    )
    assert parts["header"].height() == window.property("expectedCodeBlockHeaderHeight")
    assert _evaluate(parts["header"], "anchors.margins") == window.property(
        "expectedSpacingM"
    )
    assert parts["copy_area"].width() == window.property("expectedCopyButtonWidth")
    assert parts["copy_area"].height() == window.property("expectedCopyButtonHeight")
    assert parts["copy_background"].property("radius") == window.property(
        "expectedRadiusSmall"
    )
    assert parts["language"].property("font").pixelSize() == window.property(
        "expectedCaptionCompact"
    )
    assert parts["copy_text"].property("font").pixelSize() == window.property(
        "expectedCaptionCompact"
    )
    assert parts["code"].property("font").pixelSize() == window.property(
        "expectedCaption"
    )
    assert parts["timer"].property("interval") == window.property(
        "expectedCopyFeedback"
    )


def _assert_code_margins(window: QQuickWindow, code_text: QQuickItem) -> None:
    expected = {
        "anchors.leftMargin": "expectedSpacingL",
        "anchors.rightMargin": "expectedSpacingL",
        "anchors.bottomMargin": "expectedSpacingM",
        "anchors.topMargin": "expectedSpacingXs",
    }
    for expression, property_name in expected.items():
        assert _evaluate(code_text, expression) == window.property(property_name)


def _assert_code_block_palette(
    window: QQuickWindow, code_block: QQuickItem, parts: dict
) -> None:
    _assert_color(code_block.property("color"), window.property("expectedBackground"))
    _assert_color(
        _evaluate(code_block, "border.color"), window.property("expectedBorder")
    )
    _assert_color(
        parts["language"].property("color"),
        window.property("expectedSecondaryText"),
    )
    _assert_color(
        parts["code"].property("color"), window.property("expectedForeground")
    )
    _assert_color(
        parts["copy_text"].property("color"),
        window.property("expectedSecondaryText"),
    )
    _assert_color(
        parts["copy_background"].property("color"),
        window.property("expectedTransparent"),
    )


def _assert_copy_success(window: QQuickWindow, parts: dict) -> None:
    assert parts["copy_area"].setProperty("_copied", True)
    _pump(1)
    assert parts["copy_text"].property("text") == "已复制"
    _assert_color(
        parts["copy_text"].property("color"),
        window.property("expectedCopySuccess"),
    )
    assert parts["copy_area"].setProperty("_copied", False)
    _pump(1)
    assert parts["copy_text"].property("text") == "复制"


def _palette_signature(code_block: QQuickItem, parts: dict) -> tuple:
    colors = [
        code_block.property("color"),
        _evaluate(code_block, "border.color"),
        parts["language"].property("color"),
        parts["code"].property("color"),
        parts["copy_text"].property("color"),
    ]
    return tuple(
        channel
        for color in colors
        for channel in (color.redF(), color.greenF(), color.blueF(), color.alphaF())
    )


def _assert_markdown_runtime(window: QQuickWindow) -> tuple[QQuickItem, dict]:
    markdown = window.findChild(QQuickItem, "markdownView")
    assert markdown is not None
    columns = [
        item
        for item in markdown.childItems()
        if "ColumnLayout" in item.metaObject().className()
    ]
    assert len(columns) == 1
    assert columns[0].property("spacing") == window.property("expectedSpacingM")
    body_text = next(
        item
        for item in _walk_visual_tree(markdown)
        if item.metaObject().indexOfProperty("text") >= 0
        and str(item.property("text")).startswith("paragraph")
    )
    assert body_text.property("font").pixelSize() == window.property("expectedBody")
    code_block = _find_code_block(markdown, "x = 1")
    assert code_block.property("language") == "py"
    return code_block, _code_block_parts(code_block, "py", "x = 1")


def _assert_shared_width_defaults(
    engine: QQmlApplicationEngine, window: QQuickWindow
) -> None:
    expected = window.property("expectedChatContentMaxWidth")
    bubble = window.findChild(QQuickItem, "chatBubble")
    message_list = window.findChild(QQuickItem, "chatMessageList")
    assert bubble is not None and bubble.property("maxBubbleWidth") == expected
    assert message_list is not None
    assert message_list.property("maxBubbleWidth") == expected
    component, markdown = _create(
        engine, DETACHED_MARKDOWN_SOURCE, "p6c-detached-markdown.qml"
    )
    try:
        assert markdown.property("implicitWidth") == expected
    finally:
        markdown.deleteLater()
        del component
        _pump(1)


def _exercise_theme_modes(
    window: QQuickWindow,
    direct_code_block: QQuickItem,
    direct_parts: dict,
    markdown_code_block: QQuickItem,
    markdown_parts: dict,
) -> None:
    baseline = None
    for theme, skin in (
        (Theme.LIGHT, Skin.FLUENT),
        (Theme.DARK, Skin.FLUENT),
        (Theme.LIGHT, Skin.NEOBRUTALISM),
    ):
        setTheme(theme)
        setSkin(skin)
        _pump(5)
        _assert_legacy_tokens(window)
        _assert_code_block_palette(window, direct_code_block, direct_parts)
        _assert_code_block_palette(window, markdown_code_block, markdown_parts)
        _assert_copy_success(window, direct_parts)
        signature = _palette_signature(direct_code_block, direct_parts)
        if baseline is None:
            baseline = signature
        else:
            assert signature == pytest.approx(baseline, abs=1 / 65535)


def test_chat_components_reference_shared_style_tokens():
    for source_path, references in SOURCE_TOKEN_REFERENCES.items():
        source = source_path.read_text(encoding="utf-8")
        missing = sorted(
            reference for reference in references if reference not in source
        )
        assert missing == [], (source_path, missing)


def test_compact_caption_consumers_use_shared_typography_token():
    for source_path in COMPACT_CAPTION_CONSUMERS:
        source = source_path.read_text(encoding="utf-8")
        assert "typography.captionCompact" in source, source_path
        assert "typography.caption - 1" not in source, source_path
        assert "font.pixelSize: 11" not in source, source_path


def test_chat_style_tokens_render_in_hidden_window_and_remain_fixed(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = window = None
    try:
        component, window = _create(engine, WINDOW_SOURCE, "p6c-chat-style-tokens.qml")
        assert isinstance(window, QQuickWindow)
        assert window.isVisible() is False
        _pump(20)
        direct_code_block = window.findChild(QQuickItem, "directCodeBlock")
        assert direct_code_block is not None
        direct_parts = _code_block_parts(
            direct_code_block, "js", "const answer = 42"
        )
        markdown_code_block, markdown_parts = _assert_markdown_runtime(window)
        _assert_code_block_geometry(window, direct_code_block, direct_parts)
        _assert_code_margins(window, direct_parts["code"])
        _assert_shared_width_defaults(engine, window)
        _exercise_theme_modes(
            window,
            direct_code_block,
            direct_parts,
            markdown_code_block,
            markdown_parts,
        )
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        if window is not None:
            window.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)
