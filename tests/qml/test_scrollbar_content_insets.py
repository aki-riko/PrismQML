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
    readonly property real zeroWidthExpectedInset: Fluent.Enums.spacing.xs
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
    readonly property real defaultAreaBottomInset:
        defaultArea.flickableItem
            ? defaultArea.flickableItem.parent.height - defaultArea.flickableItem.height : -1
    property bool defaultAreaForceOverflow: true
    readonly property real responsiveListInset:
        responsiveList.listView.parent.width - responsiveList.listView.width
    property bool responsiveListForceOverflow: true
    readonly property real tinyCustomListViewportWidth: customList.listView.width
    readonly property real tinyCustomListViewportHeight: customList.listView.height
    readonly property real tinyGridViewportWidth:
        virtualGrid.flickableItem ? virtualGrid.flickableItem.width : -1
    readonly property real tinyGridViewportHeight:
        virtualGrid.flickableItem ? virtualGrid.flickableItem.height : -1
    readonly property real tinyDefaultViewportWidth:
        defaultArea.flickableItem ? defaultArea.flickableItem.width : -1
    readonly property real tinyDefaultViewportHeight:
        defaultArea.flickableItem ? defaultArea.flickableItem.height : -1

    function shrinkLowList() {
        lowList.model = 1
        lowList.itemCount = 1
    }

    function shrinkVirtualGridToFullWidthFit() {
        virtualGrid.model = 9
    }

    function shrinkResponsiveDefaultAreaToFullWidthFit() {
        defaultAreaForceOverflow = false
    }

    function shrinkResponsiveListToFullWidthFit() {
        responsiveList.model = 1
        responsiveList.itemCount = 1
        responsiveListForceOverflow = false
    }

    function growResponsiveViews() {
        responsiveListForceOverflow = true
        responsiveList.model = 5
        responsiveList.itemCount = 5
        defaultAreaForceOverflow = true
        virtualGrid.model = 20
    }

    function makeCoreViewsTiny() {
        customList.width = 6
        customList.height = 6
        virtualGrid.width = 6
        virtualGrid.height = 6
        defaultArea.width = 6
        defaultArea.height = 6
    }

    function restoreCoreViewSizes() {
        customList.width = 180
        customList.height = 120
        virtualGrid.width = 180
        virtualGrid.height = 120
        defaultArea.width = 180
        defaultArea.height = 120
    }

    function setCustomListScrollBarWidth(value) {
        customList.scrollBarWidth = value
    }

    width: 2200
    height: 220

    Component {
        id: rowDelegate
        Rectangle {
            width: ListView.view ? ListView.view.width : 0
            height: 40
        }
    }

    Component {
        id: responsiveRowDelegate
        Rectangle {
            width: ListView.view ? ListView.view.width : 0
            height: root.responsiveListForceOverflow
                ? 200
                : (ListView.view
                    && width >= ListView.view.parent.width - root.expectedInset / 2
                    ? 40 : 200)
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
            width: root.defaultAreaForceOverflow
                ? 145 : (parent ? parent.width : 0)
            height: root.defaultAreaForceOverflow
                ? 400 : (width >= 140 ? 80 : 200)
        }
    }


    Fluent.ListView {
        id: responsiveList
        x: 2000
        width: 180
        height: 120
        model: 5
        itemCount: 5
        delegate: responsiveRowDelegate
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

    function shrinkSpecializedViews() {
        listWidget.model = [{ text: "One" }]
        treeWidget.clear()
        chat.clear()
        timeline.items = []
    }

    function growSpecializedViews() {
        listWidget.model = root.listRows
        for (var treeIndex = 0; treeIndex < 20; ++treeIndex) {
            treeWidget.addTopLevelItem({ text: "Node " + treeIndex })
        }
        timeline.virtualized = false
        timeline.items = root.timelineItems
        timeline.virtualized = true
        chat.clear()
        for (var i = 0; i < 20; ++i) {
            chat.appendMessage(
                "assistant",
                ("Long wrapped message " + i + " ").repeat(12),
                ""
            )
        }
    }

    width: 800
    height: 140

    Fluent.ListWidget {
        id: listWidget
        objectName: "listWidget"
        width: 180
        height: 120
        model: root.listRows
    }

    Fluent.TreeWidget {
        id: treeWidget
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
        id: timeline
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
            "responsiveListInset",
        )
        transitions = []
        for name in inset_names:
            getattr(root, name + "Changed").connect(
                lambda name=name: transitions.append((name, float(root.property(name))))
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
        assert _wait_for(
            lambda: float(root.property("defaultAreaBottomInset")) == expected
        )
        transitions.clear()
        for _ in range(12):
            _pump()
            assert {
                name: float(root.property(name)) for name in inset_names
            } == {name: expected for name in inset_names}
        assert not any(value == 0 for _name, value in transitions), transitions
        assert warnings == []
        assert [
            window
            for window in QGuiApplication.topLevelWindows()
            if window.isVisible()
            and not any(window is existing for existing in windows_before)
        ] == []

        root.shrinkLowList()
        assert _wait_for(lambda: float(root.property("listInset")) == 0)

        root.shrinkResponsiveListToFullWidthFit()
        assert _wait_for(lambda: float(root.property("responsiveListInset")) == 0)

        root.shrinkResponsiveDefaultAreaToFullWidthFit()
        assert _wait_for(lambda: float(root.property("defaultAreaInset")) == 0)

        root.shrinkVirtualGridToFullWidthFit()
        assert _wait_for(lambda: float(root.property("virtualGridInset")) == 0)

        for _ in range(10):
            root.growResponsiveViews()
            root.shrinkResponsiveListToFullWidthFit()
            root.shrinkResponsiveDefaultAreaToFullWidthFit()
            root.shrinkVirtualGridToFullWidthFit()
        assert _wait_for(
            lambda: all(
                float(root.property(name)) == 0
                for name in (
                    "responsiveListInset",
                    "defaultAreaInset",
                    "virtualGridInset",
                )
            )
        )

        root.growResponsiveViews()
        assert _wait_for(
            lambda: all(
                float(root.property(name)) == expected
                for name in (
                    "responsiveListInset",
                    "defaultAreaInset",
                    "virtualGridInset",
                )
            )
        )

        root.setCustomListScrollBarWidth(0)
        assert _wait_for(
            lambda: float(root.property("customListInset"))
            == float(root.property("zeroWidthExpectedInset"))
        )
        root.setCustomListScrollBarWidth(20)
        assert _wait_for(
            lambda: float(root.property("customListInset"))
            == float(root.property("customExpectedInset"))
        )

        root.makeCoreViewsTiny()
        assert _wait_for(
            lambda: all(
                float(root.property(name)) >= 0
                for name in (
                    "tinyCustomListViewportWidth",
                    "tinyCustomListViewportHeight",
                    "tinyGridViewportWidth",
                    "tinyGridViewportHeight",
                    "tinyDefaultViewportWidth",
                    "tinyDefaultViewportHeight",
                )
            )
        )
        root.restoreCoreViewSizes()
        assert _wait_for(
            lambda: float(root.property("customListInset"))
            == float(root.property("customExpectedInset"))
        )
        assert warnings == []
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

        root.shrinkSpecializedViews()
        assert _wait_for(
            lambda: all(value == 0 for value in insets().values())
        ), {"insets": insets(), "warnings": warnings}
        root.growSpecializedViews()
        timeline = root.findChild(QObject, "timelineCore")
        timeline_view = timeline.findChild(QObject, "timelineVirtualViewport")
        assert _wait_for(lambda: timeline_view.property("count") == 21), {
            "count": timeline_view.property("count"),
            "flatGroupCount": timeline.property("_flatGroupCount"),
            "flatRows": len(timeline.property("_flatRows").toVariant()),
            "lastBuildGroupCount": timeline.property("_lastFlatBuildGroupCount"),
            "warnings": warnings,
        }
        assert _wait_for(
            lambda: all(value == expected for value in insets().values())
        ), {"insets": insets(), "warnings": warnings}
        for _ in range(5):
            _pump()
            assert insets() == {name: expected for name in controls}

        timeline = root.findChild(QObject, "timelineCore")
        assert timeline is not None
        timeline.setProperty("virtualized", False)
        assert _wait_for(lambda: insets()["timelineCore"] == 0), insets()
        timeline.setProperty("virtualized", True)
        assert _wait_for(
            lambda: insets()["timelineCore"] == expected
        ), insets()

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


def test_pending_scrollbar_measurement_is_safe_during_destruction(qapp):
    """Queued geometry probes must not warn after teardown. 销毁后排队的几何探测不得告警。"""
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

    root.growResponsiveViews()
    root.shrinkResponsiveListToFullWidthFit()
    root.shrinkResponsiveDefaultAreaToFullWidthFit()
    root.shrinkVirtualGridToFullWidthFit()
    root.makeCoreViewsTiny()
    root.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    for _ in range(5):
        QCoreApplication.processEvents()

    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()

    assert warnings == []
    assert [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ] == []
