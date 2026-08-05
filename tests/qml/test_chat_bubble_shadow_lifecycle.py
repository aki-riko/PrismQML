# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ChatBubble shadow lifecycle regressions. 聊天气泡阴影生命周期回归。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    width: 760
    height: 420
    visible: true
    color: Enums.backgroundColor

    Column {
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        spacing: Enums.spacing.s

        ChatBubble {
            objectName: "assistantBubble"
            width: parent.width
            role: "assistant"
            content: "Assistant message"
            avatarText: "A"
        }

        ChatBubble {
            objectName: "userBubble"
            width: parent.width
            role: "user"
            content: "User message"
        }

        ChatBubble {
            objectName: "systemBubble"
            width: parent.width
            role: "system"
            content: "System message"
        }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    """Process Qt events for a bounded interval. 在限定时间内处理 Qt 事件。"""
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_200) -> bool:
    """Wait for a QML lifecycle predicate. 等待 QML 生命周期条件。"""
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _rectangular_shadows(bubble: QObject) -> list[QObject]:
    """Return owned RectangularShadow instances. 返回气泡拥有的模糊阴影实例。"""
    return [
        child
        for child in bubble.findChildren(QObject)
        if "RectangularShadow" in child.metaObject().className()
    ]


def _neo_shadows(bubble: QObject) -> list[QObject]:
    """Return owned NeoShadow instances. 返回气泡拥有的 Neo 阴影实例。"""
    return [
        child
        for child in bubble.findChildren(QObject)
        if child.metaObject().className().startswith("NeoShadow_QMLTYPE_")
    ]


def _stable_window_image(window: QQuickWindow) -> QImage:
    """Capture a stable correctness snapshot. 捕获稳定的正确性快照。"""
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise AssertionError("ChatBubble frame did not stabilize within 800 ms")


def _visible(items: list[QObject]) -> list[bool]:
    """Read item visibility in declaration order. 按声明顺序读取可见性。"""
    return [bool(item.property("visible")) for item in items]


def _dispose_scene(engine, component, window) -> None:
    """Release the scene and flush deferred deletes. 释放场景并清空延迟删除。"""
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_chat_bubble_shadow_instances_and_skin_roundtrip(qapp):
    """Freeze current shadow counts, visibility, pixels, warnings, and cleanup.

    固化当前阴影数量、可见性、像素、警告与清理行为。
    """
    previous_skin = getSkin()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setSkin(Skin.FLUENT)
    engine = QQmlEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE,
        QUrl.fromLocalFile(
            str(ROOT / "tests/qml/chat-bubble-shadow-lifecycle.qml")
        ),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create()
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    bubbles = [
        window.findChild(QObject, name)
        for name in ("assistantBubble", "userBubble", "systemBubble")
    ]
    assert all(bubbles)
    try:
        assert _wait_for(window.isExposed)

        rectangular = [_rectangular_shadows(bubble) for bubble in bubbles]
        neo = [_neo_shadows(bubble) for bubble in bubbles]
        assert [len(items) for items in rectangular] == [1, 1, 1]
        assert [len(items) for items in neo] == [1, 1, 1]
        assert [_visible(items) for items in rectangular] == [[True], [False], [False]]
        assert [_visible(items) for items in neo] == [[False], [False], [False]]
        fluent_image = _stable_window_image(window)

        setSkin(Skin.NEOBRUTALISM)
        assert _wait_for(
            lambda: [_visible(items) for items in neo]
            == [[True], [False], [False]]
        )
        assert [_visible(items) for items in rectangular] == [
            [False],
            [False],
            [False],
        ]
        neo_image = _stable_window_image(window)
        assert neo_image != fluent_image

        setSkin(Skin.FLUENT)
        assert _wait_for(
            lambda: [_visible(items) for items in rectangular]
            == [[True], [False], [False]]
        )
        assert [_visible(items) for items in neo] == [[False], [False], [False]]
        assert _stable_window_image(window) == fluent_image

        setSkin(Skin.NEOBRUTALISM)
        assert _wait_for(
            lambda: [_visible(items) for items in neo]
            == [[True], [False], [False]]
        )
        assert _stable_window_image(window) == neo_image
        assert warnings == []
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible()
            and item is not window
            and not any(item is existing for existing in windows_before)
        ] == []
    finally:
        setSkin(previous_skin)
        _dispose_scene(engine, component, window)

    assert tuple(QGuiApplication.topLevelWindows()) == windows_before
