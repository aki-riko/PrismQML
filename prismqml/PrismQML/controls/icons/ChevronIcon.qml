// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."

// ChevronIcon - Reusable arrow icon with optional animation 可复用箭头图标
// Replaces both ChevronIcon and DropDownIndicator 合并原ChevronIcon和DropDownIndicator
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property color color: "black"
    property real strokeWidth: 1.5
    property string direction: "down"  // down, up, left, right
    
    // Animation support (formerly DropDownIndicator) 动画支持
    property bool animated: false                    // Enable animation 启用动画
    property bool isOpen: false                      // Open state (for animated) 展开状态
    property int animationDuration: Enums.duration.normal
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.checkIconSize
    implicitHeight: Enums.controlSize.checkIconSize
    
    // ==================== Arrow Canvas 箭头画布 ====================
    Canvas {
        id: canvas
        anchors.centerIn: parent
        width: Enums.controlSize.chevronIconSize
        height: Enums.comboBoxMetrics.scrollBarWidth
        rotation: control.animated && control.isOpen ? 180 : 0
        
        Behavior on rotation {
            enabled: control.animated
            NumberAnimation { 
                duration: control.animationDuration
                easing.type: Easing.OutCubic 
            }
        }
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            ctx.strokeStyle = control.color
            ctx.lineWidth = control.strokeWidth
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.beginPath()
            
            if (control.direction === "up") {
                ctx.moveTo(1, height - 1)
                ctx.lineTo(width / 2, 1)
                ctx.lineTo(width - 1, height - 1)
            } else if (control.direction === "left") {
                ctx.moveTo(width - 1, 1)
                ctx.lineTo(1, height / 2)
                ctx.lineTo(width - 1, height - 1)
            } else if (control.direction === "right") {
                ctx.moveTo(1, 1)
                ctx.lineTo(width - 1, height / 2)
                ctx.lineTo(1, height - 1)
            } else {
                // down (default)
                ctx.moveTo(1, 1)
                ctx.lineTo(width / 2, height - 1)
                ctx.lineTo(width - 1, 1)
            }
            ctx.stroke()
        }
    }
    
    onColorChanged: canvas.requestPaint()
    onDirectionChanged: canvas.requestPaint()
    Component.onCompleted: canvas.requestPaint()
}
