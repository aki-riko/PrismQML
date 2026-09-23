# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Qt Quick wheel-handler propagation probe. Qt Quick 滚轮处理器传播探针。"""

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPoint, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow


SOURCE = b"""
import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 400
    height: 240
    visible: true
    property int parentCount: 0
    property int childCount: 0
    property bool childAccepts: true

    Item {
        id: host
        objectName: "host"
        x: 10
        y: 10
        width: 360
        height: 200

        WheelHandler {
            id: parentHandler
            parent: host
            blocking: false
            onWheel: function(event) {
                root.parentCount += 1
                event.accepted = true
            }
        }

        Rectangle {
            id: child
            objectName: "child"
            x: 50
            y: 30
            width: 120
            height: 100
            color: "red"

            WheelHandler {
                blocking: false
                onWheel: function(event) {
                    root.childCount += 1
                    event.accepted = root.childAccepts
                }
            }
        }
    }
}
"""


def _pump(milliseconds=30):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wheel(window, item, delta):
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    event = QWheelEvent(
        point,
        QPointF(window.x() + point.x(), window.y() + point.y()),
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    _pump(50)


def test_nonblocking_handlers_both_observe_unaccepted_wheel(qapp):
    engine = QQmlApplicationEngine()
    component = QQmlComponent(engine)
    component.setData(SOURCE, QUrl("wheel-handler-propagation.qml"))
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [error.toString() for error in component.errors()]
    child = window.findChild(QQuickItem, "child")
    assert child is not None
    try:
        _wheel(window, child, -120)
        assert window.property("childCount") == 1
        assert window.property("parentCount") == 1

        window.setProperty("childAccepts", False)
        _wheel(window, child, -120)
        assert window.property("childCount") == 2
        assert window.property("parentCount") == 2
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
