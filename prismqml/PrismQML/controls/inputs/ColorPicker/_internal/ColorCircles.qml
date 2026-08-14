// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ColorCircles - Circle color selection 圆形颜色选择
// Layout: Horizontal row of circle color buttons with double-ring selection
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property color selectedColor: Enums.colorPickerDefaults.defaultColor
    property var colors: Enums.colorPickerDefaults.quickPalette
    property int circleSize: Enums.spacing.xxl

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeColors:
        colors === null || colors === undefined ? []
        : (typeof colors.length === "number" ? colors : [])
    
    // ==================== Signals 信号 ====================
    signal colorSelected(color value)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: row.implicitWidth
    implicitHeight: circleSize + Enums.spacing.m  // Extra space for selection ring 选中环额外空间
    
    // ==================== Content 内容 ====================
    Row {
        id: row
        anchors.centerIn: parent
        spacing: Enums.spacing.l
        
        Repeater {
            model: control._safeColors
            
            // Container for circle and selection ring 圆形和选中环容器
            Item {
                id: circleItem
                property bool selected: control.selectedColor.toString().toUpperCase() === _colorText.toUpperCase()
                property bool hovered: circleArea.containsMouse
                readonly property string _colorText:
                    modelData === null || modelData === undefined ? "" : String(modelData)

                width: control.circleSize + Enums.spacing.m
                height: control.circleSize + Enums.spacing.m
                
                // Outer selection ring 外部选中环
                Rectangle {
                    anchors.centerIn: parent
                    width: control.circleSize + Enums.spacing.s
                    height: control.circleSize + Enums.spacing.s
                    radius: width / 2
                    color: Enums.transparent
                    border.width: parent.selected ? Enums.border.normal : Enums.border.none
                    border.color: circleItem._colorText || Enums.transparent
                    opacity: parent.selected ? Enums.opacityLevel.secondary : Enums.opacityLevel.invisible
                    
                    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                }
                
                // Color circle 颜色圆形
                Rectangle {
                    id: colorCircle
                    anchors.centerIn: parent
                    width: control.circleSize
                    height: control.circleSize
                    radius: width / 2
                    color: circleItem._colorText || Enums.transparent
                    
                    // Hover effect 悬停效果
                    opacity: circleArea.containsMouse ? Enums.colorPickerMetrics.circleHoverOpacity : Enums.opacityLevel.visible
                    HoverBehavior on opacity {
                        active: circleArea.containsMouse
                        enterDuration: Enums.duration.fast
                    }
                }
                
                MouseArea {
                    id: circleArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: control.enabled
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (!circleItem._colorText) return
                        control.selectedColor = circleItem._colorText
                        control.colorSelected(circleItem._colorText)
                    }
                }
            }
        }
    }
}
