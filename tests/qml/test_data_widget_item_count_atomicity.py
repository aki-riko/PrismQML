# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DataWidget item-count atomicity regressions. 数据组件计数原子性回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QUrl,
    Signal,
    QTimer,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
DATA_WIDGET_CORE = ROOT / "prismqml/PrismQML/controls/data/DataWidgetCore.qml"
SCENE_URL = QUrl("inline:data-widget-item-count-atomicity.qml")
SCENE_SOURCE = b"""
import QtQuick
import PrismQML as Fluent

Item {
    width: 720
    height: 480

    Fluent.ListView {
        objectName: "messageList"
        anchors.fill: parent
        animated: false
        model: reportedMessageModel

        delegate: Item {
            required property string text
            width: ListView.view ? ListView.view.width : 0
            height: 24
        }
    }
}
"""
ARRAY_SCENE_URL = QUrl("inline:data-widget-array-item-count.qml")
ARRAY_SCENE_SOURCE = b"""
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    property var rows: []

    width: 720
    height: 480

    Fluent.ListView {
        objectName: "arrayList"
        anchors.fill: parent
        animated: false
        visible: root.rows.length > 0
        model: root.rows

        delegate: Item {
            required property var modelData
            width: ListView.view ? ListView.view.width : 0
            height: 24
        }
    }
}
"""
REPORTED_MESSAGES = ["hi", "有人咩", "Hello", "111", "测试", "嘿嘿"]


def test_delayed_reconciliation_rechecks_the_explicit_model_count():
    """Queued reconciliation must preserve a reliable model count.

    延迟收敛不得用过期视图状态覆盖可靠模型计数。
    """
    source = DATA_WIDGET_CORE.read_text(encoding="utf-8")

    assert "Qt.callLater(function() { root._autoItemCount = root._immediateModelItemCount() })" in source
    assert "Qt.callLater(function() { root._autoItemCount = listView.count })" not in source


def _pump(milliseconds: int = 10) -> None:
    """Process one bounded event-loop slice. 处理一段有界事件循环。"""
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_list_view_keeps_delayed_javascript_array_count(qapp):
    """A delayed JavaScript array must stay visible after queued reconciliation. 延迟数组模型在排队收敛后仍须可见。"""
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(ARRAY_SCENE_SOURCE, ARRAY_SCENE_URL)
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    try:
        qapp.processEvents()
        array_list = root.findChild(QObject, "arrayList")
        assert array_list is not None
        assert array_list.property("count") == 0

        rows = [{"text": text} for text in REPORTED_MESSAGES[:4]]
        assert root.setProperty("rows", rows)

        assert array_list.property("count") == len(rows)
        _pump()
        assert array_list.property("count") == len(rows)
        assert array_list.property("visible") is True
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()


class ResettableMessageModel(QAbstractListModel):
    """Expose the synchronous count used by real chat models. 暴露真实聊天模型使用的同步计数。"""

    TextRole = Qt.ItemDataRole.UserRole + 1
    countChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._messages: list[str] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        """Return the current message count. 返回当前消息数量。"""
        return 0 if parent.isValid() else len(self._messages)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Return a message role value. 返回消息角色值。"""
        if not index.isValid() or not 0 <= index.row() < len(self._messages):
            return None
        if role == self.TextRole:
            return self._messages[index.row()]
        return None

    def roleNames(self) -> dict[int, bytes]:
        """Expose the text role to QML. 向 QML 暴露文本角色。"""
        return {self.TextRole: b"text"}

    @Property(int, notify=countChanged)
    def count(self) -> int:
        """Return the synchronous public count. 返回同步公开计数。"""
        return len(self._messages)

    def replace(self, messages: list[str]) -> None:
        """Replace all messages with one model reset. 通过一次模型重置替换全部消息。"""
        self.beginResetModel()
        self._messages = list(messages)
        self.endResetModel()
        self.countChanged.emit()


def test_list_view_publishes_explicit_model_count_in_the_same_turn(qapp):
    """Model reset must not expose the previous count for one event turn. 模型重置不得多暴露一轮旧计数。"""
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    register_types(engine)
    model = ResettableMessageModel()
    engine.rootContext().setContextProperty("reportedMessageModel", model)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    try:
        qapp.processEvents()
        message_list = root.findChild(QObject, "messageList")
        assert message_list is not None
        assert message_list.property("count") == 0

        model.replace(REPORTED_MESSAGES)

        assert model.count == len(REPORTED_MESSAGES)
        assert message_list.property("count") == len(REPORTED_MESSAGES)

        _pump()

        assert message_list.property("count") == len(REPORTED_MESSAGES)

        model.replace([])

        assert model.count == 0
        assert message_list.property("count") == 0

        _pump()

        assert message_list.property("count") == 0
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
