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
    assert item.property("_radius") == 8
    assert item.property("_blockBorderWidth") == 1
    assert item.property("_copyRadius") == 6
    assert item.property("_labelFontSize") == 12
    assert item.property("_codeFontSize") == 12
    assert _rgb(item.property("_blockBackground")) == background
    assert _rgb(item.property("_blockBorder")) == border
    assert _rgb(item.property("_mutedText")) == muted
    assert _rgb(item.property("_codeText")) == code
    assert _rgb(item.property("_copyHover")) == hover


def _assert_assistant_bubble(item, background, border, text, link, timestamp):
    assert item.property("_bubbleRadius") == 10
    assert item.property("_bubbleTailRadius") == 6
    assert item.property("_bubbleBorderWidth") == 1
    assert item.property("_assistantShadowBlur") == 4
    assert item.property("_assistantShadowOffset") == 1
    assert _rgb(item.property("_bubbleBackground")) == background
    assert _rgb(item.property("_bubbleBorderColor")) == border
    assert _rgb(item.property("_contentTextColor")) == text
    assert _rgb(item.property("_contentLinkColor")) == link
    assert _rgb(item.property("_timestampColor")) == timestamp


def _assert_user_bubble(item, background, foreground):
    assert item.property("_bubbleRadius") == 10
    assert item.property("_bubbleTailRadius") == 6
    assert item.property("_bubbleBorderWidth") == 0
    assert _rgb(item.property("_bubbleBackground")) == background
    assert _rgb(item.property("_contentTextColor")) == foreground
    assert _rgb(item.property("_contentLinkColor")) == foreground
    assert _rgb(item.property("_timestampColor")) == foreground


def _assert_login_window(item, card, border, error_bg, error):
    assert item.property("_cardRadius") == 12
    assert item.property("_errorRadius") == 6
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
            background=(248, 251, 255),
            border=(217, 227, 236),
            muted=(95, 111, 128),
            code=(23, 32, 42),
            hover=(238, 245, 255),
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
            background=(248, 251, 255),
            border=(217, 227, 236),
            text=(23, 32, 42),
            link=(47, 111, 237),
            timestamp=(131, 146, 164),
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
        _assert_user_bubble(keep[-1][1], background=(47, 111, 237), foreground=(255, 255, 255))

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
            card=(248, 251, 255),
            border=(217, 227, 236),
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
            background=(36, 43, 52),
            border=(48, 58, 70),
            muted=(166, 177, 191),
            code=(238, 243, 248),
            hover=(38, 48, 58),
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
            background=(36, 43, 52),
            border=(48, 58, 70),
            text=(238, 243, 248),
            link=(122, 167, 255),
            timestamp=(118, 131, 148),
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
        _assert_user_bubble(keep[-1][1], background=(122, 167, 255), foreground=(15, 23, 42))

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
            card=(36, 43, 52),
            border=(48, 58, 70),
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
