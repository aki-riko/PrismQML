# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design chat and auth skin tests."""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def _alpha(qcolor):
    return round(qcolor.alphaF(), 2)


def _assert_code_block(item, background, border, muted, code, hover):
    assert item.property("_radius") == 14
    assert item.property("_blockBorderWidth") == 1
    assert item.property("_copyRadius") == 10
    assert item.property("_labelFontSize") == 12
    assert item.property("_codeFontSize") == 12
    assert _rgb(item.property("_blockBackground")) == background
    assert _rgb(item.property("_blockBorder")) == border
    assert _rgb(item.property("_mutedText")) == muted
    assert _rgb(item.property("_codeText")) == code
    assert _rgb(item.property("_copyHover")) == hover


def _assert_assistant_bubble(item, background, border, text, link, timestamp):
    assert item.property("_bubbleRadius") == 18
    assert item.property("_bubbleTailRadius") == 10
    assert item.property("_bubbleBorderWidth") == 1
    assert item.property("_assistantShadowBlur") == 4
    assert item.property("_assistantShadowOffset") == 1
    assert _rgb(item.property("_bubbleBackground")) == background
    assert _rgb(item.property("_bubbleBorderColor")) == border
    assert _rgb(item.property("_contentTextColor")) == text
    assert _rgb(item.property("_contentLinkColor")) == link
    assert _rgb(item.property("_timestampColor")) == timestamp


def _assert_user_bubble(item, background, foreground):
    assert item.property("_bubbleRadius") == 18
    assert item.property("_bubbleTailRadius") == 10
    assert item.property("_bubbleBorderWidth") == 0
    assert _rgb(item.property("_bubbleBackground")) == background
    assert _rgb(item.property("_contentTextColor")) == foreground
    assert _rgb(item.property("_contentLinkColor")) == foreground
    assert _rgb(item.property("_timestampColor")) == foreground


def _assert_markdown_view(item, text, link):
    assert item.property("blockCount") == 2
    assert _rgb(item.property("textColor")) == text
    assert _rgb(item.property("linkColor")) == link


def _assert_chat_message_list(item):
    assert item.property("messageCount") == 2
    assert item.property("maxBubbleWidth") == 360
    assert item.property("assistantAvatarText") == "P"
    assert item.property("showAssistantAvatar") is True


def _assert_login_window(item, card, border, error_bg, error):
    assert item.property("_cardRadius") == 24
    assert item.property("_errorRadius") == 10
    assert item.property("_cardBorderWidth") == 1
    assert item.property("_errorBorderWidth") == 1
    assert _rgb(item.property("_cardColor")) == card
    assert _rgb(item.property("_cardBorderColor")) == border
    assert _rgb(item.property("_errorBackgroundColor")) == error_bg
    assert _rgb(item.property("_errorBorderColor")) == error
    assert _rgb(item.property("_errorTextColor")) == error
    assert _alpha(item.property("_cardBackgroundColor")) == 0.92


def test_prism_design_chat_and_auth_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
CodeBlock {
    code: "print('prism')"
    language: "python"
}
"""))
        _assert_code_block(
            keep[-1][1],
            background=(247, 252, 254),
            border=(185, 204, 209),
            muted=(82, 105, 112),
            code=(18, 34, 38),
            hover=(234, 244, 247),
        )

        keep.append(_build(engine, b"""
import PrismQML
ChatBubble {
    width: 420
    role: "assistant"
    content: "Hello Prism"
    timestamp: "10:24"
}
"""))
        _assert_assistant_bubble(
            keep[-1][1],
            background=(247, 252, 254),
            border=(185, 204, 209),
            text=(18, 34, 38),
            link=(11, 127, 137),
            timestamp=(118, 138, 145),
        )

        keep.append(_build(engine, b"""
import PrismQML
ChatBubble {
    width: 420
    role: "user"
    content: "Ship it"
    timestamp: "10:25"
}
"""))
        _assert_user_bubble(keep[-1][1], background=(11, 127, 137), foreground=(255, 255, 255))

        keep.append(_build(engine, b"""
import PrismQML
MarkdownView {
    width: 420
    markdown: "Hello **Prism**\\n```qml\\nButton {}\\n```"
    property int blockCount: _blocks.length
}
"""))
        _assert_markdown_view(
            keep[-1][1],
            text=(18, 34, 38),
            link=(11, 127, 137),
        )

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
ChatMessageList {
    width: 420
    height: 240
    maxBubbleWidth: 360
    assistantAvatarText: "P"
    Component.onCompleted: {
        appendMessage("assistant", "Hello Prism", "10:24")
        appendMessage("user", "Ship it", "10:25")
        appendToLast(" now")
    }
}
"""))
        qapp.processEvents()
        _assert_chat_message_list(keep[-1][1])

        keep.append(_build(engine, b"""
import PrismQML
LoginWindow {
    width: 640
    height: 520
    matrixEnabled: false
    errorMessage: "Invalid credentials"
}
"""))
        _assert_login_window(
            keep[-1][1],
            card=(247, 252, 254),
            border=(185, 204, 209),
            error_bg=(253, 231, 233),
            error=(196, 43, 28),
        )

        setTheme(Theme.DARK)

        keep.append(_build(engine, b"""
import PrismQML
CodeBlock {
    code: "print('prism')"
    language: "python"
}
"""))
        _assert_code_block(
            keep[-1][1],
            background=(34, 48, 54),
            border=(50, 72, 79),
            muted=(168, 186, 191),
            code=(238, 247, 248),
            hover=(33, 49, 54),
        )

        keep.append(_build(engine, b"""
import PrismQML
ChatBubble {
    width: 420
    role: "assistant"
    content: "Hello Prism"
    timestamp: "10:24"
}
"""))
        _assert_assistant_bubble(
            keep[-1][1],
            background=(34, 48, 54),
            border=(50, 72, 79),
            text=(238, 247, 248),
            link=(109, 235, 242),
            timestamp=(115, 138, 145),
        )

        keep.append(_build(engine, b"""
import PrismQML
ChatBubble {
    width: 420
    role: "user"
    content: "Ship it"
    timestamp: "10:25"
}
"""))
        _assert_user_bubble(keep[-1][1], background=(109, 235, 242), foreground=(4, 23, 25))

        keep.append(_build(engine, b"""
import PrismQML
MarkdownView {
    width: 420
    markdown: "Hello **Prism**\\n```qml\\nButton {}\\n```"
    property int blockCount: _blocks.length
}
"""))
        _assert_markdown_view(
            keep[-1][1],
            text=(238, 247, 248),
            link=(109, 235, 242),
        )

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
ChatMessageList {
    width: 420
    height: 240
    maxBubbleWidth: 360
    assistantAvatarText: "P"
    Component.onCompleted: {
        appendMessage("assistant", "Hello Prism", "10:24")
        appendMessage("user", "Ship it", "10:25")
        appendToLast(" now")
    }
}
"""))
        qapp.processEvents()
        _assert_chat_message_list(keep[-1][1])

        keep.append(_build(engine, b"""
import PrismQML
LoginWindow {
    width: 640
    height: 520
    matrixEnabled: false
    errorMessage: "Invalid credentials"
}
"""))
        _assert_login_window(
            keep[-1][1],
            card=(34, 48, 54),
            border=(50, 72, 79),
            error_bg=(64, 38, 41),
            error=(255, 153, 164),
        )
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
