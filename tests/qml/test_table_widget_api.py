# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TableWidget public API regressions. TableWidget 公开 API 回归。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


_ROOT = Path(__file__).resolve().parents[2]
_SCENE = b"""
import QtQuick
import PrismQML

TableWidget {
    id: table

    property var betaWidget: null
    property var alphaWidget: null

    width: 360
    height: 240

    function seedItems() {
        columns = [
            { text: "Name", role: "name", width: 160 },
            { text: "Quantity", role: "quantity", width: 100 }
        ]
        tableData = [
            { name: "Beta", quantity: 0 },
            { name: "Alpha", quantity: 1 },
            { name: "Gamma", quantity: 2 }
        ]
    }

    function installCellWidgets() {
        betaWidget = cellWidgetComponent.createObject(table)
        alphaWidget = cellWidgetComponent.createObject(table)
        setCellWidget(0, 0, betaWidget)
        setCellWidget(1, 0, alphaWidget)
    }

    function selectBetaAndGamma() {
        currentRow = 0
        currentColumn = 0
        selectedRows = [0, 2]
    }

    function betaWidgetRow() {
        for (var row = 0; row < rowCount; row++) {
            if (cellWidget(row, 0) === betaWidget) return row
        }
        return -1
    }

    function alphaWidgetRow() {
        for (var row = 0; row < rowCount; row++) {
            if (cellWidget(row, 0) === alphaWidget) return row
        }
        return -1
    }

    Component {
        id: cellWidgetComponent
        Item { width: 20; height: 10 }
    }
}
"""
_WIDTH_SCENE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property bool fittedHasHorizontalScroll: fittedTable._hasHorizontalScroll
    readonly property real fittedContentWidth: fittedTable.contentTotalWidth
    readonly property real fittedViewportWidth: fittedTable.listView.width
    readonly property var fittedColumnWidths: fittedTable._columnPixelWidths
    readonly property bool ratioOverflowHasHorizontalScroll: ratioOverflowTable._hasHorizontalScroll
    readonly property bool absoluteOverflowHasHorizontalScroll: absoluteOverflowTable._hasHorizontalScroll

    function resizeFittedTable(tableWidth) { fittedTable.width = tableWidth }

    width: 1120
    height: 240

    TableWidget {
        id: fittedTable

        width: 360
        height: 220
        columns: [
            { text: "Item", role: "item", width: 0.29 },
            { text: "Time", role: "time", width: 0.25 },
            { text: "Price", role: "price", width: 0.31 },
            { text: "Quantity", role: "quantity", width: 0.15 }
        ]
        tableData: [{ item: "A", time: "Now", price: 1, quantity: 1 }]
    }

    TableWidget {
        id: ratioOverflowTable

        x: 380
        width: 360
        height: 220
        columns: [
            { text: "Left", role: "left", width: 0.7 },
            { text: "Right", role: "right", width: 0.7 }
        ]
        tableData: [{ left: "A", right: "B" }]
    }

    TableWidget {
        id: absoluteOverflowTable

        x: 760
        width: 360
        height: 220
        columns: [
            { text: "Left", role: "left", width: 240 },
            { text: "Right", role: "right", width: 240 }
        ]
        tableData: [{ left: "A", right: "B" }]
    }
}
"""
_QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def test_table_widget_sort_remove_and_falsy_values_preserve_rows(qapp):
    """Sorting and removal must preserve row identity and falsy values. 排序与删除须保持行身份和假值。"""
    configure_qml_environment()
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    component = None
    table = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            _SCENE,
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/table-widget-api.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        table = component.create(engine.rootContext())
        assert table is not None, [error.toString() for error in component.errors()]
        _pump()
        messages.clear()

        table.seedItems()
        table.installCellWidgets()
        table.selectBetaAndGamma()
        _pump()

        assert _variant(table.item(0, 1))["text"] == 0
        assert table.betaWidgetRow() == 0
        assert table.alphaWidgetRow() == 1

        table.sortItems(0, 0)
        assert [
            _variant(table.getRow(row))["name"] for row in range(3)
        ] == ["Alpha", "Beta", "Gamma"]
        assert table.property("currentRow") == 1
        assert _variant(table.property("selectedRows")) == [1, 2]
        assert table.betaWidgetRow() == 1
        assert table.alphaWidgetRow() == 0

        table.removeRow(0)
        assert [
            _variant(table.getRow(row))["name"] for row in range(2)
        ] == ["Beta", "Gamma"]
        assert table.property("currentRow") == 0
        assert _variant(table.property("selectedRows")) == [0, 1]
        assert table.betaWidgetRow() == 0
        assert table.alphaWidgetRow() == -1

        table.setRowCount(1)
        assert table.property("currentRow") == 0
        assert _variant(table.property("selectedRows")) == [0]
        assert table.betaWidgetRow() == 0

        table.setRowCount(0)
        assert table.property("currentRow") == -1
        assert table.property("currentColumn") == -1
        assert _variant(table.property("selectedRows")) == []
        assert table.hasCellWidget(0, 0) is False

        table.setRowCount(-2)
        assert table.property("rowCount") == 0
    finally:
        _release(qapp, table, component, engine)
        qInstallMessageHandler(previous_handler)

    failures = [
        message for mode, message in messages if mode in _QT_FAILURE_TYPES
    ]
    assert failures == []


def test_table_widget_fractional_columns_use_inner_viewport_width(qapp):
    """Fractional columns must fit the inner viewport without masking real overflow.

    比例列须贴合内部视口且保留真实超宽。
    """
    configure_qml_environment()
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    component = None
    root = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            _WIDTH_SCENE,
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/table-widget-widths.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]
        _pump(50)
        messages.clear()

        viewport_width = float(root.property("fittedViewportWidth"))
        content_width = float(root.property("fittedContentWidth"))
        column_widths = _variant(root.property("fittedColumnWidths"))

        assert viewport_width > 0
        assert sum(column_widths) == content_width
        assert content_width == viewport_width
        assert root.property("fittedHasHorizontalScroll") is False
        assert root.property("ratioOverflowHasHorizontalScroll") is True
        assert root.property("absoluteOverflowHasHorizontalScroll") is True

        root.resizeFittedTable(480)
        _pump(50)

        resized_viewport_width = float(root.property("fittedViewportWidth"))
        resized_content_width = float(root.property("fittedContentWidth"))
        resized_column_widths = _variant(root.property("fittedColumnWidths"))
        assert resized_viewport_width > viewport_width
        assert sum(resized_column_widths) == resized_content_width
        assert resized_content_width == resized_viewport_width
        assert root.property("fittedHasHorizontalScroll") is False
    finally:
        _release(qapp, root, component, engine)
        qInstallMessageHandler(previous_handler)

    failures = [
        message for mode, message in messages if mode in _QT_FAILURE_TYPES
    ]
    assert failures == []
