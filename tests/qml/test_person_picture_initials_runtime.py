# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PersonPicture initials, badge overlay and group runtime contracts.

PersonPicture 首字母、徽章叠加与群组语义运行时合同。
"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "person-picture-initials.qml")
)

AVATAR_SIZE = 40

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 480
    height: 320
    visible: false

    readonly property real singleScale: Enums.badge.personPictureInitialsScale
    readonly property real multiScale: Enums.badge.personPictureMultiInitialsScale
    readonly property int initialsLength: Enums.badge.personPictureInitialsLength

    Avatar {
        objectName: "avatarText"
        x: 20
        y: 20
        size: 40
        text: "alice"
    }

    Avatar {
        objectName: "avatarInitials"
        x: 80
        y: 20
        size: 40
        text: "alice"
        initials: "AB"
    }

    Avatar {
        objectName: "avatarInitialsLong"
        x: 140
        y: 20
        size: 40
        initials: "ABCDE"
    }

    Avatar {
        objectName: "avatarInitialsOnly"
        x: 340
        y: 20
        size: 40
        initials: "AB"
    }

    Avatar {
        objectName: "avatarPlain"
        x: 200
        y: 20
        size: 40
    }

    Avatar {
        objectName: "avatarGroup"
        x: 260
        y: 20
        size: 40
        isGroup: true
    }

    Avatar {
        objectName: "avatarBadgeNumber"
        x: 20
        y: 100
        size: 40
        initials: "AB"
        badgeNumber: 7
    }

    Avatar {
        objectName: "avatarBadgeGlyph"
        x: 80
        y: 100
        size: 40
        badgeGlyph: "Star"
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(60)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _avatar(window, name) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _part(avatar: QQuickItem, name) -> QQuickItem:
    item = avatar.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _initials(avatar: QQuickItem) -> QQuickItem:
    return _part(avatar, "avatarInitials")


def _placeholder(avatar: QQuickItem) -> QQuickItem:
    return _part(avatar, "avatarPlaceholder")


def _badge_loader(avatar: QQuickItem) -> QQuickItem:
    return _part(avatar, "avatarBadgeLoader")


def _badge(avatar: QQuickItem) -> QQuickItem:
    return _part(avatar, "avatarBadge")


def test_empty_initials_keep_the_single_character_fallback(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarText")
        label = _initials(avatar)
        assert label.property("visible") is True
        assert label.property("text") == "A"
        assert label.property("font").pixelSize() == round(
            AVATAR_SIZE * window.property("singleScale")
        )
        assert _placeholder(avatar).property("visible") is False
        assert avatar.width() == AVATAR_SIZE
        assert avatar.height() == AVATAR_SIZE
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_explicit_multi_character_initials_are_rendered(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarInitials")
        label = _initials(avatar)
        assert label.property("visible") is True
        assert label.property("text") == "AB"
        multi_scale = window.property("multiScale")
        single_scale = window.property("singleScale")
        assert multi_scale < single_scale
        assert abs(
            label.property("font").pixelSize() - AVATAR_SIZE * multi_scale
        ) <= 1
        assert _placeholder(avatar).property("visible") is False
        assert avatar.width() == AVATAR_SIZE
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_initials_are_truncated_to_the_token_length(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarInitialsLong")
        label = _initials(avatar)
        assert label.property("visible") is True
        assert label.property("text") == "ABCDE"[: window.property("initialsLength")]
        assert label.property("text") == "AB"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_initials_only_avatar_suppresses_the_placeholder_image(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarInitialsOnly")
        label = _initials(avatar)
        assert label.property("visible") is True
        assert label.property("text") == "AB"

        placeholder = _placeholder(avatar)
        assert placeholder.property("icon") == ""
        assert placeholder.property("visible") is True

        # Without initials the placeholder image comes back 没有首字母时占位图恢复
        avatar.setProperty("initials", "")
        _pump(60)
        assert label.property("visible") is False
        assert label.property("text") == ""
        assert placeholder.property("icon") == "Person"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_placeholder_and_group_icons(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        plain = _avatar(window, "avatarPlain")
        plain_icon = _placeholder(plain)
        assert plain_icon.property("visible") is True
        assert plain_icon.property("icon") == "Person"
        assert _initials(plain).property("visible") is False

        group = _avatar(window, "avatarGroup")
        group_icon = _placeholder(group)
        assert group_icon.property("visible") is True
        assert group_icon.property("icon") == "People"
        assert group_icon.property("icon") != plain_icon.property("icon")
        assert group.width() == AVATAR_SIZE
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_badge_number_overlay(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarBadgeNumber")
        loader = _badge_loader(avatar)
        assert loader.property("active") is True
        badge = _badge(avatar)
        assert badge.property("visible") is True
        assert badge.property("count") == 7
        assert badge.property("target") is None
        # The overlay never grows the avatar 叠加徽章不会撑大头像
        assert avatar.width() == AVATAR_SIZE
        assert avatar.height() == AVATAR_SIZE
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_badge_glyph_overlay_and_hidden_default(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarBadgeGlyph")
        assert _badge_loader(avatar).property("active") is True
        badge = _badge(avatar)
        assert badge.property("visible") is True
        assert badge.property("icon") == "Star"

        plain = _avatar(window, "avatarPlain")
        plain_loader = _badge_loader(plain)
        assert plain_loader.property("active") is False
        # An unbadged avatar creates no extra renderer at all 无徽章头像不创建额外渲染器
        assert plain.findChild(QQuickItem, "avatarBadge") is None
        assert plain.width() == AVATAR_SIZE
        assert plain.height() == AVATAR_SIZE
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_badge_overlay_appears_after_a_runtime_request(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        avatar = _avatar(window, "avatarPlain")
        assert _badge_loader(avatar).property("active") is False

        avatar.setProperty("badgeNumber", 3)
        _pump(60)
        assert _badge_loader(avatar).property("active") is True
        badge = _badge(avatar)
        assert badge.property("count") == 3
        assert badge.property("visible") is True

        avatar.setProperty("badgeNumber", 0)
        _pump(60)
        assert _badge_loader(avatar).property("active") is False
        assert avatar.findChild(QQuickItem, "avatarBadge") is None
        assert avatar.width() == AVATAR_SIZE
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
