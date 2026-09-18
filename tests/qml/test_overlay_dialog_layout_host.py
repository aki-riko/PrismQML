# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Overlay dialogs declared inside a layout. 声明在布局内的覆盖式对话框。"""

from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from prismqml import register_types


_SCENE = '''
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 480
    visible: true

    ColumnLayout {
        anchors.fill: parent

        // 声明在布局里的对话框：根对象不得使用 anchors
        ConfirmDialog {
            id: dialog
            objectName: "layoutDialog"
            title: "提示"
            message: "布局内的对话框"
        }

        Item { Layout.fillWidth: true; Layout.fillHeight: true }
    }

    Component.onCompleted: dialog.open()
}
'''.encode("utf-8")

_ANCHOR_WARNING = "Detected anchors on an item that is managed by a layout"


def test_overlay_dialog_inside_layout_has_no_anchor_warning(qapp):
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    register_types(engine)
    window = None
    try:
        engine.loadData(_SCENE, QUrl("inline"))
        roots = engine.rootObjects()
        assert roots, "overlay dialog layout scene failed to load"
        QTest.qWait(200)
        window = roots[0]
        dialog = window.findChild(QQuickItem, "layoutDialog")
        assert dialog is not None
        warnings = [
            message
            for mode, message in messages
            if mode != QtMsgType.QtDebugMsg and _ANCHOR_WARNING in message
        ]
        assert warnings == []
        # 打开后仍然铺满窗口覆盖宿主
        assert dialog.property("isOpen") is True
        content_item = window.contentItem()
        assert dialog.width() == content_item.width()
        assert dialog.height() == content_item.height()
    finally:
        if window is not None:
            window.close()
        engine.deleteLater()
        qapp.processEvents()
        qInstallMessageHandler(previous_handler)
