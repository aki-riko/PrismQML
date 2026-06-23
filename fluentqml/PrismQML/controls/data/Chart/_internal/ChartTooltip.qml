// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../data"

// ChartTooltip - Tooltip component for chart widgets 图表提示框组件
// Fluent Design style: clean card with subtle shadow
// Fluent Design 风格：简洁卡片+微妙阴影

Item {
    id: root
    
    // ==================== Props 属性 ====================
    property string label: ""
    property var value: 0
    property bool isValueString: false   // If true, value is displayed as string 如果为true，value作为字符串显示
    // Value formatter callback 自定义数值格式化器
    // function(value) -> string;若提供则覆盖 toString(),用于多级单位等场景
    property var valueFormatter: null
    property bool showColorDot: false    // Show color indicator dot 显示颜色指示点
    property color dotColor: "transparent"
    property bool showPointer: false     // Show triangle pointer 显示三角形指针
    property int pointerDirection: 0     // 0=down, 1=up, 2=left, 3=right 指针方向
    
    // ==================== Size 尺寸 ====================
    width: tooltipRect.width
    height: tooltipRect.height + (showPointer ? pointer.height : 0)
    
    z: Enums.zIndex.tooltip
    
    // Fluent Design: smooth fade animation 平滑淡入动画
    opacity: visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
    
    // ==================== Tooltip Body 提示框主体 ====================
    Rectangle {
        id: tooltipRect
        width: tooltipContent.width + Enums.spacing.l
        height: tooltipContent.height + Enums.spacing.m
        
        radius: Enums.radius.small
        color: Enums.gray.tooltip
        
        // Shadow 阴影
        layer.enabled: root.visible
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: Enums.shadow.level2.color
            shadowBlur: Enums.shadow.level2.blurNormalized
            shadowVerticalOffset: Enums.shadow.level2.offset
        }
        
        // ==================== Content 内容 ====================
        Column {
            id: tooltipContent
            anchors.centerIn: parent
            spacing: Enums.spacing.xxs
            
            // Label row with optional color dot 带可选颜色点的标签行
            Row {
                spacing: Enums.spacing.s
                visible: root.label !== "" || root.showColorDot
                
                Rectangle {
                    width: Enums.spacing.m
                    height: Enums.spacing.m
                    radius: root.showColorDot ? Enums.radius.micro : Enums.radius.large
                    color: root.dotColor
                    anchors.verticalCenter: parent.verticalCenter
                    visible: root.showColorDot
                }
                
                Label {
                    type: Enums.label.type_caption
                    text: root.label
                    color: Enums.stateColor.chartTooltipText
                    visible: root.label !== ""
                }
            }
            
            // Value 数值
            Label {
                type: Enums.label.type_body_strong
                text: {
                    if (root.isValueString) return root.value
                    if (root.value === undefined || root.value === "") return ""
                    if (root.valueFormatter && typeof root.valueFormatter === "function") {
                        return root.valueFormatter(root.value)
                    }
                    return root.value
                }
                color: "white"
                visible: root.value !== "" && root.value !== undefined
            }
        }
    }
    
    // ==================== Triangle Pointer 三角形指针 ====================
    Canvas {
        id: pointer
        visible: root.showPointer
        width: 10
        height: 6
        anchors.horizontalCenter: tooltipRect.horizontalCenter
        anchors.top: tooltipRect.bottom
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.fillStyle = Enums.gray.tooltip
            ctx.beginPath()
            ctx.moveTo(0, 0)
            ctx.lineTo(width, 0)
            ctx.lineTo(width / 2, height)
            ctx.closePath()
            ctx.fill()
        }
        
        Component.onCompleted: requestPaint()
    }
}
