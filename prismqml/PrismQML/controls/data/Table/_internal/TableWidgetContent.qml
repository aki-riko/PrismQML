// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../../"
import ".."
import QtQuick

// TableWidgetContent - Table visual and lifecycle content 表格视觉与生命周期内容
// Keeps the public TableWidget entry focused on state, data and orchestration.
// 将公开 TableWidget 入口限制为状态、数据与编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var table

    // ==================== Public Props 公开属性 ====================
    property alias paintedRowComponent: paintedRowComponent
    property alias contentDelegate: contentDelegateComponent
    property alias headerContent: headerContentComponent
    property alias defaultTableContextMenuLoader: defaultTableContextMenuLoader

    anchors.fill: parent

    // ==================== Content 内容 ====================
    Component {
        id: paintedRowComponent

        PaintedRow {
            columns: content.table._safeColumns
            rowData: parent ? parent.rowData : null
            rowIndex: parent ? parent.rowIndex : -1
            rowHeight: content.table.rowHeight
            extraDraw: content.table.paintedRowExtra
        }
    }

    Component {
        id: contentDelegateComponent

        TableRowDelegate {
            table: content.table
            radius: Enums.radius.small
        }
    }

    Component {
        id: headerContentComponent

        TableHeader {
            table: content.table
        }
    }

    // Recompute after internal card/layout margins change the actual viewport width.
    // 内部卡片或布局边距改变实际视口宽度后重新计算列宽。
    Connections {
        function onWidthChanged() { content.table._recomputeColumnWidths() }

        target: content.table.listView
    }

    // 仅当 tableData 是真正的 QAbstractListModel/QObject (有 modelReset 等 signal) 才订阅;
    // QVariantList 没这些 signal, 直接绑 target 会被识别成 QObject 报警告
    // "Unable to assign QVariantList to QObject*"
    Connections {
        function onModelReset() {
            content.table.rowCount = content.table._calcRowCount()
            content.table._recomputeColumnWidths()
        }
        function onRowsInserted() {
            content.table.rowCount = content.table._calcRowCount()
            content.table._recomputeColumnWidths()
        }
        function onRowsRemoved() {
            content.table.rowCount = content.table._calcRowCount()
            content.table._recomputeColumnWidths()
        }
        function onLayoutChanged() {
            content.table.rowCount = content.table._calcRowCount()
            content.table._recomputeColumnWidths()
        }
        function onCountChanged() {
            content.table.rowCount = content.table._calcRowCount()
            content.table._recomputeColumnWidths()
        }

        target: (content.table.tableData && typeof content.table.tableData.length !== "number"
                 && typeof content.table.tableData === "object"
                 && (typeof content.table.tableData.rowCount === "function"
                     || content.table.tableData.modelReset !== undefined))
                ? content.table.tableData : null
        ignoreUnknownSignals: true
        // model 数据变化时既要刷新 rowCount 也要重算 autoWidth 列宽
        // (列宽算法采样真实数据, 空 model 时算的宽度毫无意义)
    }

    // Load the built-in menu only when enabled 仅在启用时加载内置菜单
    Loader {
        id: defaultTableContextMenuLoader

        objectName: "defaultTableContextMenuLoader"
        active: content.table.defaultContextMenuEnabled
        sourceComponent: Component {
            TableDefaultContextMenu {
                table: content.table
            }
        }
    }

    // Pagination Component 分页器组件（仅在启用时显示）
    Loader {
        id: paginationLoader
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Enums.spacing.m
        height: item ? item.height : 0
        active: content.table.showPagination
        visible: active

        sourceComponent: Component {
            Paginator {
                anchors.centerIn: parent
                currentPage: content.table.currentPage
                totalPages: content.table.totalPages
                visiblePages: content.table.visiblePages
                accentColor: content.table.checkedColor
                onPageChanged: (page) => {
                    content.table.currentPage = page
                    content.table.pageChanged(page)
                }
            }
        }
    }
}
