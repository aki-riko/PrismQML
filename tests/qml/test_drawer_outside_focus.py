# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Outside Drawer keyboard-focus acceptance. 外侧抽屉键盘焦点验收。"""

import os

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from tests.qml.test_drawer_conventions import (
    ROOT,
    _create_scene,
    _dispose_scene,
    _drawer_window,
    _new_visible_windows,
    _pump,
    _wait_for,
)


FOCUS_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "drawer-outside-focus.qml")
)
FOCUS_SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    x: 100
    y: 120
    width: 600
    height: 400
    visible: true

    Drawer {
        id: drawer
        objectName: "drawer"
        mode: Enums.drawer.mode_outside
        position: Enums.position.right
        drawerWidth: 220
        drawerHeight: 180
        animationDuration: 0
        modal: false

        TextInput {
            objectName: "outsideTextInput"
            x: 24
            y: 24
            width: 160
            height: 32
            z: 1
            activeFocusOnPress: true
        }
    }
}
"""


def test_outside_drawer_text_input_accepts_focus_and_keyboard_input_on_windows(qapp):
    """真实 Windows 窗口必须把点击和键盘输入交给外侧抽屉内容。"""
    if (
        QGuiApplication.platformName() != "windows"
        or os.environ.get("PRISMQML_ALLOW_VISIBLE_WINDOWS") != "1"
    ):
        pytest.skip("需显式启用 Windows 可视窗口验收")

    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, drawer, _content_item, _panel, warnings = _create_scene(
        FOCUS_SCENE_SOURCE,
        FOCUS_SCENE_URL,
    )
    try:
        window.requestActivate()
        assert _wait_for(window.isActive)
        text_input = drawer.findChild(QQuickItem, "outsideTextInput")
        assert isinstance(text_input, QQuickItem)

        assert QMetaObject.invokeMethod(drawer, "open")
        drawer_window = _drawer_window()
        assert isinstance(drawer_window, QQuickWindow)
        assert _wait_for(drawer_window.isVisible)
        assert _wait_for(text_input.isVisible)

        point = text_input.mapToItem(
            drawer_window.contentItem(),
            QPointF(text_input.width() / 2, text_input.height() / 2),
        ).toPoint()
        QTest.mouseClick(
            drawer_window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            point,
        )
        assert _wait_for(lambda: QGuiApplication.focusWindow() is drawer_window)
        text_input.forceActiveFocus()
        assert _wait_for(lambda: bool(text_input.property("activeFocus")))

        for character in "JELLY":
            QCoreApplication.postEvent(
                drawer_window,
                QKeyEvent(
                    QEvent.Type.KeyPress,
                    Qt.Key(ord(character)),
                    Qt.KeyboardModifier.NoModifier,
                    character,
                ),
            )
        _pump()
        assert _wait_for(lambda: text_input.property("text") == "JELLY")
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
    assert _new_visible_windows(windows_before) == []
