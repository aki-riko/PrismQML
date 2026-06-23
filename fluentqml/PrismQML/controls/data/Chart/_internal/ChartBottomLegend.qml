// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// ChartBottomLegend - Bottom-aligned horizontal legend for all chart types 底部水平图例组件
// Unified legend component with consistent styling across all charts 统一的图例组件，所有图表使用一致的样式

Item {
    id: root
    
    // ==================== Props 属性 ====================
    property var legendData: []              // [{name: "", color: "", label: ""}, ...] name或label作为显示文本
    property int hoveredIndex: -1            // Currently hovered item 当前悬停项
    property var hiddenIndices: []           // Hidden item indices 隐藏项索引
    property string legendStyle: "dot"       // "bar" | "line" | "dot" 图例样式
    property bool clickable: true            // Enable click to toggle 启用点击切换
    property var getColor: null              // Custom color function 自定义颜色函数
    
    // ==================== Signals 信号 ====================
    signal itemHovered(int index)
    signal itemClicked(int index)
    
    // ==================== Helper Functions 辅助函数 ====================
    function getItemColor(index) {
        if (getColor && typeof getColor === "function") return getColor(index)
        var item = legendData[index]
        if (item && item.color) return item.color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function getItemLabel(index) {
        var item = legendData[index]
        if (!item) return ""
        return item.name || item.label || ""
    }
    
    function isHidden(index) {
        return hiddenIndices.indexOf(index) >= 0
    }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: legendRow.width
    implicitHeight: legendRow.height
    
    // ==================== Layout 布局 ====================
    Row {
        id: legendRow
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        Repeater {
            model: root.legendData
            
            Item {
                width: itemRow.width + Enums.spacing.s
                height: itemRow.height + Enums.spacing.xs
                
                property bool hovered: root.hoveredIndex === index
                property bool isItemHidden: root.isHidden(index)
                
                Row {
                    id: itemRow
                    anchors.centerIn: parent
                    spacing: Enums.spacing.s
                    opacity: isItemHidden ? Enums.opacityLevel.medium : 1.0
                    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                    
                    // Legend icon 图例图标
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: root.legendStyle === "dot" ? Enums.spacing.m : Enums.spacing.l
                        height: root.legendStyle === "line" ? Enums.border.medium : Enums.spacing.m
                        radius: root.legendStyle === "dot" ? width / 2 : Enums.radius.micro
                        color: isItemHidden ? Enums.textColor.tertiary : root.getItemColor(index)
                        opacity: root.hoveredIndex === -1 || hovered ? 1.0 : Enums.opacityLevel.medium
                        Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                        
                        // Line style center dot 线条样式中心点
                        Rectangle {
                            anchors.centerIn: parent
                            width: Enums.spacing.s
                            height: Enums.spacing.s
                            radius: width / 2
                            color: parent.color
                            border.width: Enums.border.thin
                            border.color: Enums.cardColor
                            visible: root.legendStyle === "line"
                        }
                    }
                    
                    Label {
                        type: Enums.label.type_caption
                        text: root.getItemLabel(index)
                        font.weight: hovered ? Font.DemiBold : Font.Normal
                        font.strikeout: isItemHidden
                        color: isItemHidden ? Enums.textColor.tertiary 
                               : (hovered ? Enums.textColor.primary : Enums.textColor.secondary)
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: root.clickable ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onEntered: root.itemHovered(index)
                    onExited: root.itemHovered(-1)
                    onClicked: {
                        if (root.clickable) {
                            clickAnim.start()
                            root.itemClicked(index)
                        }
                    }
                }
                
                SequentialAnimation {
                    id: clickAnim
                    PropertyAnimation { target: itemRow; property: "scale"; to: 0.9; duration: Enums.duration.ultraFast; easing.type: Easing.OutQuad }
                    PropertyAnimation { target: itemRow; property: "scale"; to: 1.0; duration: Enums.duration.fast; easing.type: Easing.OutBack }
                }
            }
        }
    }
}
