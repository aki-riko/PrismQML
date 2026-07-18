# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Dialog drag boundary regression tests. 对话框拖拽边界回归测试。"""

from PySide6.QtCore import QPoint, QUrl, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from prismqml import register_types


_SCENE = '''
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 480
    visible: true

    MessageBox {
        id: dialog
        objectName: "dragDialog"
        draggable: true
        title: "提示"
        content: "拖拽边界测试"
        Component.onCompleted: dialog.open()
    }
}
'''.encode("utf-8")


def _build_scene(engine):
    engine.loadData(_SCENE, QUrl("inline"))
    roots = engine.rootObjects()
    assert roots, "dialog drag scene failed to load"
    QTest.qWait(200)
    window = roots[0]
    dialog = window.findChild(QQuickItem, "dragDialog")
    assert dialog is not None
    container = next(
        item
        for item in dialog.childItems()
        if item.metaObject().className() == "QQuickItem" and item.width() > 0
    )
    return window, container


def _drag(window, container, end):
    start = QPoint(round(container.x() + 24), round(container.y() + 24))
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
    QTest.mouseMove(window, end, 20)
    QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
    QTest.qWait(50)


def test_messagebox_drag_stays_inside_overlay(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    window, container = _build_scene(engine)

    try:
        _drag(window, container, QPoint(840, 680))
        assert container.x() == window.width() - container.width()
        assert container.y() == window.height() - container.height()

        _drag(window, container, QPoint(-200, -200))
        assert container.x() == 0
        assert container.y() == 0
    finally:
        window.close()
        engine.deleteLater()
        qapp.processEvents()
