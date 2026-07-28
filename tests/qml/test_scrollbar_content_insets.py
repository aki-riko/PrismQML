# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Scrollbar content-inset runtime regressions. 滚动条内容避让运行时回归。"""

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


SCENE_URL = QUrl("inline:scrollbar-content-insets.qml")
SCENE_SOURCE = b"""
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    readonly property real expectedInset:
        Fluent.Enums.controlSize.scrollBarWidth + Fluent.Enums.spacing.xs
    readonly property real customExpectedInset: 20 + Fluent.Enums.spacing.xs
    readonly property var tableRows: {
        var rows = []
        for (var i = 0; i < 20; ++i) rows.push({ name: "Row " + i })
        return rows
    }
    readonly property var treeRows: {
        var rows = []
        for (var i = 0; i < 20; ++i) rows.push({ text: "Node " + i })
        return rows
    }

    readonly property real listInset:
        lowList.listView.parent.width - lowList.listView.width
    readonly property real tableViewInset:
        lowTable.listView.parent.width - lowTable.listView.width
    readonly property real tableWidgetInset:
        tableWidget.listView.parent.width - tableWidget.listView.width
    readonly property real treeViewInset:
        lowTree.listView.parent.width - lowTree.listView.width
    readonly property real hiddenListInset:
        hiddenList.listView.parent.width - hiddenList.listView.width
    readonly property real customListInset:
        customList.listView.parent.width - customList.listView.width
    readonly property real overflowTableBottomInset:
        overflowTable.listView.parent.height - overflowTable.listView.height
    readonly property real virtualListInset:
        virtualList.flickableItem
            ? virtualList.flickableItem.parent.width - virtualList.flickableItem.width : -1
    readonly property real virtualGridInset:
        virtualGrid.flickableItem
            ? virtualGrid.flickableItem.parent.width - virtualGrid.flickableItem.width : -1
    readonly property real alwaysVisibleListInset:
        alwaysVisibleList.flickableItem
            ? alwaysVisibleList.flickableItem.parent.width
                - alwaysVisibleList.flickableItem.width : -1
    readonly property real defaultAreaInset:
        defaultArea.flickableItem
            ? defaultArea.flickableItem.parent.width - defaultArea.flickableItem.width : -1

    function shrinkLowList() {
        lowList.model = 1
        lowList.itemCount = 1
    }

    width: 2000
    height: 220

    Component {
        id: rowDelegate
        Rectangle {
            width: ListView.view ? ListView.view.width : 0
            height: 40
        }
    }

    Fluent.ListView {
        id: lowList
        width: 180
        height: 120
        model: 20
        itemCount: 20
        delegate: rowDelegate
    }

    Fluent.TableView {
        id: lowTable
        x: 200
        width: 180
        height: 120
        model: 20
        itemCount: 20
        columns: [{ text: "Name", width: 1.0, fillWidth: true }]
        delegate: rowDelegate
    }

    Fluent.TableWidget {
        id: tableWidget
        x: 400
        width: 180
        height: 120
        columns: [{ text: "Name", role: "name", width: 1.0 }]
        tableData: root.tableRows
    }

    Fluent.TreeView {
        id: lowTree
        x: 600
        width: 180
        height: 120
        model: root.treeRows
    }

    Fluent.ScrollArea {
        id: virtualList
        x: 800
        width: 180
        height: 120
        type: Fluent.Enums.scroll.type_list
        model: 20
        itemHeight: 40
        delegate: rowDelegate
    }

    Fluent.ScrollArea {
        id: virtualGrid
        x: 1000
        width: 180
        height: 120
        type: Fluent.Enums.scroll.type_grid
        model: 20
        cellWidth: 60
        cellHeight: 40
        delegate: Rectangle { width: 60; height: 40 }
    }

    Fluent.ScrollArea {
        id: alwaysVisibleList
        y: 130
        width: 180
        height: 80
        type: Fluent.Enums.scroll.type_list
        alwaysShowScrollBar: true
        model: 1
        itemHeight: 40
        delegate: rowDelegate
    }

    Fluent.ListView {
        id: hiddenList
        x: 1200
        width: 180
        height: 120
        showScrollBar: false
        model: 20
        itemCount: 20
        delegate: rowDelegate
    }

    Fluent.ListView {
        id: customList
        x: 1400
        width: 180
        height: 120
        scrollBarWidth: 20
        model: 20
        itemCount: 20
        delegate: rowDelegate
    }

    Fluent.TableWidget {
        id: overflowTable
        x: 1600
        width: 180
        height: 120
        columns: [
            { text: "Left", role: "name", width: 160 },
            { text: "Right", role: "name", width: 160 }
        ]
        tableData: root.tableRows
    }

    Fluent.ScrollArea {
        id: defaultArea
        x: 1800
        width: 180
        height: 120

        Rectangle {
            width: 140
            height: 400
        }
    }
}
"""

SPECIALIZED_SCENE_URL = QUrl("inline:specialized-scrollbar-content-insets.qml")
SPECIALIZED_SCENE_SOURCE = b"""
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    readonly property real expectedInset:
        Fluent.Enums.controlSize.scrollBarWidth + Fluent.Enums.spacing.xs
    readonly property var listRows: {
        var rows = []
        for (var i = 0; i < 20; ++i) rows.push({ text: "Item " + i })
        return rows
    }
    readonly property var treeRows: {
        var rows = []
        for (var i = 0; i < 20; ++i) rows.push({ text: "Node " + i })
        return rows
    }
    readonly property var timelineItems: {
        var cards = []
        for (var i = 0; i < 20; ++i) {
            cards.push({ text: ("Long wrapped event " + i + " ").repeat(8) })
        }
        return [{ title: "Group", status: "info", cards: cards }]
    }

    width: 800
    height: 140

    Fluent.ListWidget {
        objectName: "listWidget"
        width: 180
        height: 120
        model: root.listRows
    }

    Fluent.TreeWidget {
        objectName: "treeWidget"
        x: 200
        width: 180
        height: 120
        model: root.treeRows
    }

    Fluent.ChatMessageList {
        id: chat
        objectName: "chatMessageList"
        x: 400
        width: 180
        height: 120
    }

    Fluent.TimelineCore {
        objectName: "timelineCore"
        x: 600
        width: 180
        height: 120
        virtualized: true
        items: root.timelineItems
    }

    Component.onCompleted: {
        for (var i = 0; i < 20; ++i) {
            chat.appendMessage(
                "assistant",
                ("Long wrapped message " + i + " ").repeat(12),
                ""
            )
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def test_scrollbar_gutter_is_reserved_across_data_and_virtual_views(qapp):
    """Visible scrollbars must reduce the content viewport. 可见滚动条必须缩小内容视口。"""
    configure_qml_environment()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    try:
        expected = float(root.property("expectedInset"))
        inset_names = (
            "listInset",
            "tableViewInset",
            "tableWidgetInset",
            "treeViewInset",
            "virtualListInset",
            "virtualGridInset",
            "alwaysVisibleListInset",
            "defaultAreaInset",
        )
        ready = _wait_for(
            lambda: all(float(root.property(name)) > 0 for name in inset_names)
        )
        insets = {
            name: float(root.property(name)) for name in inset_names
        }
        assert ready, insets
        assert insets == {name: expected for name in inset_names}
        assert float(root.property("hiddenListInset")) == 0
        assert float(root.property("customListInset")) == float(
            root.property("customExpectedInset")
        )
        assert float(root.property("overflowTableBottomInset")) == expected
        assert warnings == []
        assert [
            window
            for window in QGuiApplication.topLevelWindows()
            if window.isVisible()
            and not any(window is existing for existing in windows_before)
        ] == []

        root.shrinkLowList()
        assert _wait_for(lambda: float(root.property("listInset")) == 0)
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_specialized_virtual_and_widget_views_reserve_scrollbar_gutter(qapp):
    """Specialized virtual views must follow the same gutter contract. 专用虚拟视图须遵循同一避让合同。"""
    configure_qml_environment()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SPECIALIZED_SCENE_SOURCE, SPECIALIZED_SCENE_URL)
    assert _wait_for(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    try:
        expected = float(root.property("expectedInset"))
        controls = {
            "listWidget": "listWidgetViewport",
            "treeWidget": "treeWidgetViewport",
            "chatMessageList": "chatMessageViewport",
            "timelineCore": "timelineVirtualViewport",
        }

        def insets():
            result = {}
            for control_name, viewport_name in controls.items():
                control = root.findChild(QObject, control_name)
                viewport = control.findChild(QObject, viewport_name) if control else None
                result[control_name] = (
                    viewport.parentItem().width() - viewport.width()
                    if viewport is not None else -1
                )
            return result

        assert _wait_for(lambda: all(value > 0 for value in insets().values()))
        assert insets() == {name: expected for name in controls}
        assert warnings == []
        assert [
            window
            for window in QGuiApplication.topLevelWindows()
            if window.isVisible()
            and not any(window is existing for existing in windows_before)
        ] == []

        for control_name in controls:
            control = root.findChild(QObject, control_name)
            assert control is not None
            control.setProperty("showScrollBar", False)
        assert _wait_for(lambda: all(value == 0 for value in insets().values()))
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
