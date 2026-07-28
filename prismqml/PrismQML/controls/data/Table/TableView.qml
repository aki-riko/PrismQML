// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import ".."
import "../../containers/Separator"

// TableView - General low-level QTableView equivalent 通用低阶 QTableView 等价组件
// Inherits DataWidgetCore in lightweight card mode 继承 DataWidgetCore 的轻量卡片模式
//
// Usage 用法:
//   Fluent.TableView {
//       model: myAbstractListModel
//       columns: [
//           { text: "开关", width: 60 },         // 像素值 (>= 1)
//           { text: "模式", width: 0.2 },        // 比例值 (< 1)
//           { text: "操作", width: 0.4, fillWidth: true }
//       ]
//       delegate: Rectangle { ... }
//   }
//
// Difference from high-level TableWidget 与高阶 TableWidget 的区别：
//   TableView renders QAbstractListModel with a custom row delegate TableView 渲染 QAbstractListModel 与自定义行委托
//   TableWidget owns tableData and convenience APIs TableWidget 自带 tableData 与便捷 API
DataWidgetCore {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var columns: []
    property alias model: root.listModel
    property alias delegate: root.contentDelegate

    // ==================== Internal Props 内部属性 ====================
    readonly property var _safeColumns:
        columns === null || columns === undefined ? []
        : (typeof columns.length === "number" ? columns : [])

    // ==================== Public Methods 公开方法 ====================
    function scrollToTop() { listView.positionViewAtBeginning() }
    function scrollToBottom() { listView.positionViewAtEnd() }

    function columnWidth(index) {
        var safeColumns = _safeColumns || []
        if (index < 0 || index >= safeColumns.length) return 0
        var col = safeColumns[index] || {}
        if (col.fillWidth) {
            var used = 0
            for (var i = 0; i < safeColumns.length; i++) {
                if (i === index) continue
                var other = safeColumns[i] || {}
                if (!other.fillWidth) used += _columnWidth(other, listView.width)
            }
            return Math.max(60, listView.width - used)
        }
        return _columnWidth(col, listView.width)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _columnWidth(col, totalWidth) {
        if (!col) col = {}
        if (col.fillWidth) return -1
        var w = col.width
        if (w === undefined || w === null) return Math.max(60, totalWidth * 0.15)
        if (w < 1) return totalWidth * w
        return w
    }

    // ==================== Size 尺寸 ====================
    // DataWidgetCore overrides DataWidgetCore 覆盖项
    showShadow: true
    shadowLevel: Enums.shadow.level2
    showHeader: true
    showFooter: true
    // The base DataWidgetCore tracks model signals and maintains itemCount. 基类 DataWidgetCore 跟踪模型信号并维护 itemCount。
    implicitWidth: 400
    implicitHeight: 300
    // Apply row spacing after the inherited ListView exists. 继承的 ListView 就绪后应用行间距。
    Component.onCompleted: {
        listView.spacing = 1
        listView.leftMargin = Enums.spacing.xs
        listView.rightMargin = Enums.spacing.xs
    }

    // Header content 表头内容
    headerContent: Component {
        Item {
            Row {
                anchors.fill: parent
                anchors.leftMargin: Enums.spacing.m
                anchors.rightMargin: Enums.spacing.m

                Repeater {
                    model: root._safeColumns || []
                    delegate: Item {
                        readonly property var columnData: modelData || ({})
                        property bool _hovered: _headerCellHover.containsMouse

                        width: {
                            var safeColumns = root._safeColumns || []
                            if (columnData.fillWidth) {
                                var used = 0
                                for (var i = 0; i < safeColumns.length; i++) {
                                    if (i === index) continue
                                    var other = safeColumns[i] || {}
                                    if (!other.fillWidth) {
                                        used += root._columnWidth(other, parent.width)
                                    }
                                }
                                return Math.max(60, parent.width - used)
                            }
                            return root._columnWidth(columnData, parent.width)
                        }
                        height: parent.height

                        MouseArea {
                            id: _headerCellHover
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                        }

                        Separator {
                            type: Enums.separator.vertical
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            lineLength: parent.height * 0.5
                            lineColor: root.borderColor
                            visible: index < (root._safeColumns || []).length - 1
                            opacity: parent._hovered ? 1.0 : 0.4
                            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                        }

                        Label {
                            anchors.centerIn: parent
                            type: Enums.label.type_caption
                            text: columnData.text || ""
                            font.bold: true
                            color: root.secondaryColor
                        }
                    }
                }
            }
        }
    }
}
