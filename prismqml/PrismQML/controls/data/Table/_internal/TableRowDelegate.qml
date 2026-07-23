// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../../"
import "../../../containers/Separator"
import "../../../data"
import "../../../inputs/LineEdit/"
import ".."
import QtQuick

// TableRowDelegate - Row renderer for TableWidget 表格行渲染器
Rectangle {
    id: rowDelegate

    // ==================== Required Props 必需属性 ====================
    required property var table
    required property int index
    required property var modelData
    readonly property var columnData: modelData || ({})

    // ==================== Readonly State 只读状态 ====================
    readonly property var effectiveData: {
        if (modelData !== undefined && modelData !== null) return modelData
        var m = table.tableData
        if (m && typeof m.getRow === 'function') {
            return m.getRow(index)
        }
        return {}
    }

    // ==================== Internal Props 内部属性 ====================
    property bool recycling: false
    property bool hovered: false
    property int editColumnIndex: -1

    width: table._hasHorizontalScroll ? table._effectiveContentWidth - 10
                                      : table.listView.width - 10
    height: table.rowHeight
    radius: Enums.radius.small
    scale: mouseArea.pressed ? 0.98 : 1.0
    transformOrigin: Item.Center
    color: {
        var base = (rowDelegate.index % 2 === 1 && table.alternatingRowColors)
            ? table.alternateColor : table.cardColor
        var selected = table._isRowSelected(rowDelegate.index)
        if (selected) {
            return rowDelegate.hovered ? Enums.stateColor.selectedHover
                                       : Enums.stateColor.selected
        }
        if (mouseArea.pressed) return Qt.tint(base, Enums.stateColor.listItemPressed)
        if (rowDelegate.hovered) return Qt.tint(base, Enums.stateColor.listItemHover)
        return base
    }

    ListView.onPooled: {
        rowDelegate.recycling = true
        rowDelegate.hovered = false
    }
    ListView.onReused: {
        rowDelegate.recycling = false
        rowDelegate.hovered = false
    }

    Behavior on scale {
        enabled: !rowDelegate.recycling
        NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
    }
    Behavior on color {
        enabled: !rowDelegate.recycling
        ColorAnimation { duration: Enums.duration.fast }
    }

    Rectangle {
        id: selectionIndicator

        readonly property bool active: table._isRowSelected(rowDelegate.index)

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.border.thick
        height: mouseArea.pressed ? parent.height * Enums.listIndicator.pressedRatio
                                  : parent.height * Enums.listIndicator.normalRatio
        radius: Enums.radius.micro
        color: table.checkedColor
        opacity: active ? 1 : 0
        scale: active ? 1 : 0
        transformOrigin: Item.Center

        Behavior on height { NumberAnimation { duration: Enums.duration.fast } }
        Behavior on opacity {
            enabled: !rowDelegate.recycling
            NumberAnimation {
                duration: selectionIndicator.active ? Enums.duration.medium : Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
        Behavior on scale {
            enabled: !rowDelegate.recycling
            NumberAnimation { duration: Enums.duration.spring; easing.type: Easing.OutBack }
        }
    }

    Separator {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: Enums.spacing.s
        anchors.rightMargin: Enums.spacing.s
        lineColor: table.borderColor
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onEntered: rowDelegate.hovered = true
        onExited: rowDelegate.hovered = false
        onClicked: (mouse) => {
            table._selectRow(rowDelegate.index)
            if (mouse.button === Qt.LeftButton) {
                table.rowClicked(rowDelegate.index, rowDelegate.effectiveData)
            } else if (mouse.button === Qt.RightButton) {
                if (table.selectOnRightClick) {
                    table._selectRow(rowDelegate.index)
                }

                if (table.contextMenuEnabled) {
                    var rootPos = mouseArea.mapToItem(table, mouse.x, mouse.y)
                    table.customContextMenuRequested(Qt.point(rootPos.x, rootPos.y))
                } else if (table.defaultContextMenuEnabled) {
                    var globalPos = mouseArea.mapToItem(null, mouse.x, mouse.y)
                    table._showDefaultContextMenu(rowDelegate.index, globalPos.x, globalPos.y)
                }
            }
        }
        onDoubleClicked: (mouse) => {
            table.rowDoubleClicked(rowDelegate.index, rowDelegate.effectiveData)

            if (table.editable) {
                var clickX = mouse.x
                var accumulatedX = 0
                for (var i = 0; i < table._safeColumns.length; i++) {
                    var actualWidth = table._columnPixelWidths[i] || 0
                    if (clickX >= accumulatedX && clickX < accumulatedX + actualWidth) {
                        table.cellDoubleClicked(rowDelegate.index, i)
                        if (!table.cellWidgets[rowDelegate.index + "_" + i]) {
                            rowDelegate.editColumnIndex = i
                        }
                        break
                    }
                    accumulatedX += actualWidth
                }
            }
        }
        onWheel: (event) => event.accepted = false
    }

    Loader {
        anchors.fill: parent
        active: table.paintedRowMode
        sourceComponent: paintedRowComponent
    }

    Component {
        id: paintedRowComponent

        PaintedRow {
            columns: table._safeColumns
            rowData: rowDelegate.effectiveData
            rowIndex: rowDelegate.index
            rowHeight: table.rowHeight
            extraDraw: table.paintedRowExtra
        }
    }

    Row {
        anchors.fill: parent
        visible: !table.paintedRowMode

        Repeater {
            model: table.paintedRowMode ? 0 : table._safeColumns

            Item {
                id: cellItem

                property var cellWidgetItem: table.cellWidgets[rowDelegate.index + "_" + index] || null

                width: table._columnPixelWidths[index] || 60
                height: rowDelegate.height
                clip: true

                Loader {
                    id: customCellLoader

                    anchors.fill: parent
                    active: !!rowDelegate.columnData.cellComponent
                            && !cellItem.cellWidgetItem
                            && rowDelegate.editColumnIndex !== index
                    visible: active
                    sourceComponent: rowDelegate.columnData.cellComponent || null
                    asynchronous: true
                    opacity: status === Loader.Ready ? 1 : 0

                    Behavior on opacity {
                        enabled: !rowDelegate.recycling
                        NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
                    }

                    onLoaded: {
                        if (item) {
                            if ('colKey' in item) item.colKey = rowDelegate.columnData.role
                            if ('role' in item) item.role = rowDelegate.columnData.role
                            if ('rowIndex' in item) item.rowIndex = rowDelegate.index
                        }
                    }
                }

                Binding {
                    target: customCellLoader.item || null
                    property: "value"
                    when: customCellLoader.item && ('value' in customCellLoader.item)
                    value: rowDelegate.effectiveData ? rowDelegate.effectiveData[rowDelegate.columnData.role] : null
                    restoreMode: Binding.RestoreNone
                }
                Binding {
                    target: customCellLoader.item || null
                    property: "rowData"
                    when: customCellLoader.item && ('rowData' in customCellLoader.item)
                    value: rowDelegate.effectiveData
                    restoreMode: Binding.RestoreNone
                }
                Binding {
                    target: customCellLoader.item || null
                    property: "rowIndex"
                    when: customCellLoader.item && ('rowIndex' in customCellLoader.item)
                    value: rowDelegate.index
                    restoreMode: Binding.RestoreNone
                }

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_caption
                    text: rowDelegate.effectiveData
                        ? String(rowDelegate.effectiveData[rowDelegate.columnData.role] ?? "") : ""
                    color: table.textColor
                    elide: Text.ElideRight
                    visible: !cellItem.cellWidgetItem
                             && !rowDelegate.columnData.cellComponent
                             && rowDelegate.editColumnIndex !== index
                }

                Loader {
                    anchors.fill: parent
                    anchors.margins: Enums.spacing.xs
                    active: rowDelegate.editColumnIndex === index
                    visible: active
                    sourceComponent: Component {
                        LineEditNormal {
                            id: inlineEditor
                            inputType: Enums.input.type_normal
                            placeholderText: ""
                            text: rowDelegate.effectiveData
                                ? String(rowDelegate.effectiveData[rowDelegate.columnData.role] ?? "") : ""

                            Component.onCompleted: {
                                forceActiveFocus()
                                selectAll()
                            }

                            onEditingFinished: {
                                var currentText = rowDelegate.effectiveData
                                    ? String(rowDelegate.effectiveData[rowDelegate.columnData.role] ?? "") : ""
                                if (rowDelegate.editColumnIndex === index && text !== currentText) {
                                    table.setItem(rowDelegate.index, index, text)
                                }
                                rowDelegate.editColumnIndex = -1
                            }
                        }
                    }
                }

                Item {
                    id: widgetContainer

                    function _reparentWidget() {
                        if (cellItem.cellWidgetItem && visible) {
                            cellItem.cellWidgetItem.parent = widgetContainer
                            _centerWidget()
                        }
                    }

                    function _centerWidget() {
                        if (cellItem.cellWidgetItem && cellItem.cellWidgetItem.parent === widgetContainer) {
                            var widget = cellItem.cellWidgetItem
                            widget.x = Qt.binding(function() {
                                return (widgetContainer.width - widget.width) / 2
                            })
                            widget.y = Qt.binding(function() {
                                return (widgetContainer.height - widget.height) / 2
                            })
                        }
                    }

                    anchors.fill: parent
                    visible: !!cellItem.cellWidgetItem

                    onVisibleChanged: _reparentWidget()
                    Component.onCompleted: _reparentWidget()
                    onWidthChanged: _centerWidget()
                    onHeightChanged: _centerWidget()
                }
            }
        }
    }
}
