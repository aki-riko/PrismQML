# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MessageBox content rendering regression tests. MessageBox 正文渲染回归测试。"""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


def _build_message_box(engine):
    component = QQmlComponent(engine)
    qml = '''
import QtQuick
import PrismQML
MessageBox {
    readonly property color expectedSelectionColor: Enums.accentColor
    readonly property color expectedSelectedTextColor: Enums.accentForeground

    title: "提示"
    content: "这是一条消息"
}
'''.encode("utf-8")
    component.setData(
        qml,
        QUrl("inline"),
    )
    assert not component.isError(), [error.toString() for error in component.errors()]
    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def test_messagebox_uses_native_text_edit_for_content(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, message_box = _build_message_box(engine)

    try:
        content = message_box.findChild(QQuickItem, "messageContentLabel")
        assert content is not None
        assert content.metaObject().className() == "QQuickTextEdit"
        assert content.metaObject().indexOfProperty("transparentBackground") == -1
        assert content.property("text") == "这是一条消息"
        assert content.property("readOnly") is True
        assert content.property("selectByMouse") is False
        assert content.property("selectionColor") == message_box.property(
            "expectedSelectionColor"
        )
        assert content.property("selectedTextColor") == message_box.property(
            "expectedSelectedTextColor"
        )
        assert content.height() == content.property("implicitHeight")
        assert content.height() < 100

        message_box.setProperty("contentCopyable", True)
        assert content.property("selectByMouse") is True
    finally:
        message_box.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
