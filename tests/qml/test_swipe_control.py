# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SwipeControl contracts. 滑动操作契约回归。"""

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


SCENE_URL = QUrl.fromLocalFile(
    str(Path(__file__).resolve().parent / "swipe-control.qml")
)

SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int expectedActionWidth: Enums.controlSize.swipeActionWidth
    property string lastKey: ""
    property string lastSide: ""
    property int triggerCount: 0
    property var eventLog: []

    width: 480
    height: 260
    visible: true

    function openLeft() { row.open("left") }
    function openRight() { row.open("right") }
    function closeRow() { row.close() }

    SwipeControl {
        id: row
        objectName: "swipeRow"
        x: 20
        y: 20
        width: 400
        height: 56
        leftActions: [
            { key: "flag", text: "Flag", level: Enums.statusLevel.info }
        ]
        rightActions: [
            { key: "archive", text: "Archive", level: Enums.statusLevel.warning },
            { key: "delete", text: "Delete", level: Enums.statusLevel.error }
        ]
        onActionTriggered: (key, side) => {
            root.lastKey = key
            root.lastSide = side
            root.triggerCount++
            root.eventLog = root.eventLog.concat([key + ":" + side])
        }

        Rectangle {
            anchors.fill: parent
            color: Enums.cardColor
        }
    }
}
"""


def _pump(milliseconds: int = 12) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _create_scene(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.show()
    _pump(120)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _row(window: QQuickWindow):
    row = window.findChild(QQuickItem, "swipeRow")
    assert row is not None
    return row


def _action_button(window: QQuickWindow, side: str, index: int):
    """One revealed action button, found through the visual tree.

    通过视觉树定位某个露出的操作按钮。
    """
    parent = window.findChild(
        QQuickItem, "swipeLeftActions" if side == "left" else "swipeRightActions"
    )
    assert parent is not None
    pending = list(parent.childItems())
    while pending:
        item = pending.pop(0)
        pending.extend(item.childItems())
        if (item.metaObject().indexOfProperty("side") >= 0
                and item.metaObject().indexOfProperty("label") >= 0):
            if item.property("side") != side:
                continue
            if index == 0:
                return item
            index -= 1
    raise AssertionError(f"swipe action not found: {side}")


def test_swipe_control_starts_closed_and_opens_either_side(qapp):
    """A closed row sits at zero offset and can reveal each side on demand.

    关闭状态位移为零，两侧都能按需展开。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        row = _row(window)
        action_width = window.property("expectedActionWidth")
        assert row.property("isOpen") is False
        assert row.property("openSide") == ""
        assert row.property("_offset") == 0

        window.openRight()
        assert _wait_for(lambda: row.property("openSide") == "right")
        assert row.property("_offset") == -action_width * 2
        assert row.property("isOpen") is True

        window.openLeft()
        assert _wait_for(lambda: row.property("openSide") == "left")
        assert row.property("_offset") == action_width

        window.closeRow()
        assert _wait_for(lambda: row.property("openSide") == "")
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_swipe_control_action_click_reports_key_and_side(qapp):
    """Tapping a revealed action must report it and close the row.

    点击露出的操作必须上报并收回该行。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        row = _row(window)
        window.openRight()
        assert _wait_for(lambda: row.property("openSide") == "right")

        delete_button = _action_button(window, "right", 1)
        centre = delete_button.mapToItem(
            window.contentItem(),
            QPointF(delete_button.width() / 2, delete_button.height() / 2),
        )
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            QPoint(round(centre.x()), round(centre.y())),
        )
        assert _wait_for(lambda: window.property("triggerCount") == 1), (
            f"no action reported; log={window.property('eventLog')}"
        )
        assert window.property("lastKey") == "delete"
        assert window.property("lastSide") == "right"
        assert _wait_for(lambda: row.property("isOpen") is False)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_swipe_control_real_drag_settles_to_the_revealed_side(qapp):
    """A real horizontal drag past half must settle open.

    真实横向拖拽过半必须在展开位吸附。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        row = _row(window)
        content = window.findChild(QQuickItem, "swipeContent")
        assert content is not None
        start = content.mapToItem(window.contentItem(), QPointF(320, 28))
        # Left-ward drag well past half of the two right actions
        # 向左拖拽, 远超右侧两个操作宽度的一半
        end = content.mapToItem(window.contentItem(), QPointF(180, 28))
        start_point = QPoint(round(start.x()), round(start.y()))
        end_point = QPoint(round(end.x()), round(end.y()))

        QTest.mouseMove(window, start_point)
        QTest.mousePress(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, start_point,
        )
        QTest.mouseMove(window, QPoint(round((start.x() + end.x()) / 2),
                                      start_point.y()), 20)
        QTest.mouseMove(window, end_point, 20)
        assert row.property("_dragging") is True
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, end_point,
        )

        assert _wait_for(lambda: row.property("openSide") == "right"), (
            f"drag did not settle open: offset={row.property('_offset')}"
        )
        assert row.property("_offset") == pytest.approx(
            -window.property("expectedActionWidth") * 2, abs=0.5
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


import pytest  # noqa: E402
