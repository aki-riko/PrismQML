// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import ".."
import "../../containers/Separator"

// TableView - 通用 TableView (QTableView 等价物) 低阶 View 级组件
// 继承 DataWidgetCore,轻量模式(shadow level2 + 卡片边框)
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
// 与 TableWidget (高阶) 区别 vs TableWidget:
//   TableView = QTableView 等价物,只渲染,适合 QAbstractListModel + 自定义行 delegate
//   TableWidget     = QTableWidget 等价物,自带 tableData (JS array) + addRow/setItem 等便利 API
DataWidgetCore {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var columns: []
    property alias model: root.listModel
    property alias delegate: root.contentDelegate

    // ==================== DataWidgetCore overrides ====================
    showShadow: true
    shadowLevel: Enums.shadow.level2
    showHeader: true
    showFooter: true
    // itemCount 由基类 DataWidgetCore 自维护(Connections 跟踪 model 信号)

    implicitWidth: 400
    implicitHeight: 300

    // Row spacing for visual breathing room 行间距
    Component.onCompleted: {
        listView.spacing = 1
        listView.leftMargin = Enums.spacing.xs
        listView.rightMargin = Enums.spacing.xs
    }

    // ==================== Helper 计算列宽 ====================
    function _columnWidth(col, totalWidth) {
        if (col.fillWidth) return -1
        var w = col.width
        if (w === undefined || w === null) return Math.max(60, totalWidth * 0.15)
        if (w < 1) return totalWidth * w
        return w
    }

    // ==================== Public API 公共 API ====================
    function scrollToTop() { listView.positionViewAtBeginning() }
    function scrollToBottom() { listView.positionViewAtEnd() }

    function columnWidth(index) {
        if (index < 0 || index >= columns.length) return 0
        var col = columns[index]
        if (col.fillWidth) {
            var used = 0
            for (var i = 0; i < columns.length; i++) {
                if (i === index) continue
                if (!columns[i].fillWidth) used += _columnWidth(columns[i], listView.width)
            }
            return Math.max(60, listView.width - used)
        }
        return _columnWidth(col, listView.width)
    }

    // ==================== Header content 表头内容 ====================
    headerContent: Component {
        Item {
            Row {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8

                Repeater {
                    model: root.columns
                    delegate: Item {
                        width: {
                            if (modelData.fillWidth) {
                                var used = 0
                                for (var i = 0; i < root.columns.length; i++) {
                                    if (i === index) continue
                                    if (!root.columns[i].fillWidth) {
                                        used += root._columnWidth(root.columns[i], parent.width)
                                    }
                                }
                                return Math.max(60, parent.width - used)
                            }
                            return root._columnWidth(modelData, parent.width)
                        }
                        height: parent.height

                        property bool _hovered: _headerCellHover.containsMouse

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
                            visible: index < root.columns.length - 1
                            opacity: parent._hovered ? 1.0 : 0.4
                            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                        }

                        Label {
                            anchors.centerIn: parent
                            type: Enums.label.type_caption
                            text: modelData.text || ""
                            font.bold: true
                            color: root.secondaryColor
                        }
                    }
                }
            }
        }
    }

    // ==================== ListView rightMargin for scrollbar ====================
    Binding {
        target: listView
        property: "rightMargin"
        value: listView.contentHeight > listView.height ? Enums.controlSize.scrollBarWidth + Enums.spacing.xs : 0
    }
}
