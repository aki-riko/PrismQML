// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// ColorCircles - Circle color selection 圆形颜色选择
// Layout: Horizontal row of circle color buttons with double-ring selection
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property color selectedColor: Enums.colorPickerDefaults.defaultColor
    property var colors: Enums.colorPickerDefaults.quickPalette
    property int circleSize: 20
    
    // ==================== Signals 信号 ====================
    signal colorSelected(color value)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: row.implicitWidth
    implicitHeight: circleSize + 8  // Extra space for selection ring 选中环额外空间
    
    // ==================== Content 内容 ====================
    Row {
        id: row
        anchors.centerIn: parent
        spacing: Enums.spacing.l
        
        Repeater {
            model: control.colors
            
            // Container for circle and selection ring 圆形和选中环容器
            Item {
                width: control.circleSize + 8
                height: control.circleSize + 8
                
                property bool selected: control.selectedColor.toString().toUpperCase() === modelData.toString().toUpperCase()
                property bool hovered: circleArea.containsMouse
                
                // Outer selection ring 外部选中环
                Rectangle {
                    anchors.centerIn: parent
                    width: control.circleSize + 6
                    height: control.circleSize + 6
                    radius: width / 2
                    color: Enums.transparent
                    border.width: parent.selected ? 2 : 0
                    border.color: modelData
                    opacity: parent.selected ? 0.6 : 0
                    
                    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                }
                
                // Color circle 颜色圆形
                Rectangle {
                    id: colorCircle
                    anchors.centerIn: parent
                    width: control.circleSize
                    height: control.circleSize
                    radius: width / 2
                    color: modelData
                    
                    // Hover effect 悬停效果
                    opacity: circleArea.containsMouse ? 0.8 : 1.0
                    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                }
                
                MouseArea {
                    id: circleArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: control.enabled
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        control.selectedColor = modelData
                        control.colorSelected(modelData)
                    }
                }
            }
        }
    }
}
