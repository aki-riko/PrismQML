# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Released-row regressions for the shared data view. 共享数据视图的已释放行回归。"""

from PySide6.QtCore import QEventLoop, QObject, QPointF, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


SCENE_URL = QUrl("inline:data-view-released-rows.qml")
SCENE_SOURCE = b"""
import QtQuick
import PrismQML as Fluent

Window {
    id: window
    width: 720
    height: 460
    visible: true
    color: "white"

    ListModel { id: listModel }
    ListModel { id: tableModel }

    function seed() {
        for (var index = 0; index < 10; ++index) {
            listModel.append({ "text": "Row " + index })
            tableModel.append({ "name": "Cell " + index })
        }
    }

    function setCounts(target) {
        while (listModel.count > target) listModel.remove(listModel.count - 1, 1)
        while (listModel.count < target) listModel.append({ "text": "Row " + listModel.count })
        while (tableModel.count > target) tableModel.remove(tableModel.count - 1, 1)
        while (tableModel.count < target) tableModel.append({ "name": "Cell " + tableModel.count })
    }

    Component.onCompleted: seed()

    Fluent.ListView {
        id: listView
        objectName: "listView"
        x: 10
        y: 10
        width: 300
        height: 420
        model: listModel
        delegate: Rectangle {
            required property int index
            required property string text

            property string itemText: text
            width: ListView.view ? ListView.view.width : 0
            height: 30
            color: "transparent"
        }
    }

    Fluent.TableView {
        id: tableView
        objectName: "tableView"
        x: 330
        y: 10
        width: 320
        height: 420
        model: tableModel
        columns: [{ text: "Name", width: 1.0, role: "name" }]
        delegate: Rectangle {
            required property int index
            required property var modelData

            property string itemText: modelData.name || ""
            width: ListView.view ? ListView.view.width : 0
            height: 30
            color: "transparent"
        }
    }
}
"""


def _pump(milliseconds: int = 40) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _rendered_rows(control: QQuickItem) -> list[tuple]:
    """Visible rows inside the viewport. 视口内可见的行。

    A row released while its exit transition was cancelled keeps rendering at a partial
    opacity; it shows up here with index -1.
    退场过渡被取消时被释放的行会以半透明状态继续渲染，在这里表现为 index 为 -1。
    """
    origin = control.mapToScene(QPointF(0.0, 0.0))
    top = origin.y()
    bottom = top + control.height()
    rows = []
    for item in _descendants(control):
        meta = item.metaObject()
        if meta.indexOfProperty("index") < 0 or meta.indexOfProperty("itemText") < 0:
            continue
        if not item.isVisible() or item.opacity() <= 0.05:
            continue
        item_top = item.mapToScene(QPointF(0.0, 0.0)).y()
        if item_top + item.height() <= top or item_top >= bottom:
            continue
        rows.append((int(item.property("index")), item.property("itemText")))
    rows.sort()
    return rows


def _create_scene(engine):
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(200):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    for _ in range(50):
        if window.isVisible():
            break
        _pump()
    _pump(300)
    list_view = window.findChild(QObject, "listView")
    table_view = window.findChild(QObject, "tableView")
    assert list_view is not None and table_view is not None
    return component, window, list_view, table_view


def test_released_rows_are_hidden_for_shared_data_views(qapp):
    """Rows released by an interrupted exit transition must stop rendering.

    退场过渡被中断时释放的行必须停止渲染（ListView / TableView 共用同一视图容器）。
    """
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, window, list_view, table_view = _create_scene(engine)
    try:
        assert [index for index, _ in _rendered_rows(list_view)] == list(range(10))
        assert [index for index, _ in _rendered_rows(table_view)] == list(range(10))

        # Rapid grow/shrink so every exit transition is cancelled by the next change.
        # 快速增删，使每次退场过渡都被下一次变化取消。
        for target in (16, 8, 13, 5, 11, 3):
            window.setCounts(target)
            _pump(50)
        _pump(1500)

        assert list_view.property("itemCount") == 3
        assert table_view.property("itemCount") == 3
        assert [index for index, _ in _rendered_rows(list_view)] == [0, 1, 2]
        assert [index for index, _ in _rendered_rows(table_view)] == [0, 1, 2]

        for target in (14, 2, 9, 1):
            window.setCounts(target)
            _pump(30)
        _pump(1500)

        assert list_view.property("itemCount") == 1
        assert table_view.property("itemCount") == 1
        assert [index for index, _ in _rendered_rows(list_view)] == [0]
        assert [index for index, _ in _rendered_rows(table_view)] == [0]
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)
