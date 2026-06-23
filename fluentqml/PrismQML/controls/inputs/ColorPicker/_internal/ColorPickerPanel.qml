// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// ColorPickerPanel - Hue/Saturation selection panel 色相/饱和度选择面板
// Layout: Horizontal=Hue(0-360), Vertical=Saturation(top=full, bottom=white)
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property real hue: 0.5           // 0-1, maps to 0-360°
    property real saturation: 1.0    // 0-1, top=1, bottom=0
    property real brightness: 1.0    // For brightness adjustment 亮度调整
    
    // ==================== Signals 信号 ====================
    signal colorChanged(real h, real s)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 260
    implicitHeight: 200
    
    // ==================== Hue/Saturation Canvas 色相/饱和度画布 ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height
            
            // Draw hue gradient horizontally 水平绘制色相渐变
            for (var x = 0; x < w; x++) {
                var hueValue = x / w
                // Vertical gradient: top=saturated color, bottom=white
                var gradient = ctx.createLinearGradient(x, 0, x, h)
                gradient.addColorStop(0, Qt.hsva(hueValue, 1, control.brightness, 1).toString())
                gradient.addColorStop(1, Qt.hsva(hueValue, 0, control.brightness, 1).toString())
                ctx.fillStyle = gradient
                ctx.fillRect(x, 0, 1, h)
            }
        }
        
        Component.onCompleted: requestPaint()
    }
    
    // Repaint when brightness changes 亮度变化时重绘
    onBrightnessChanged: canvas.requestPaint()
    
    // ==================== Selection Circle 选择圆圈 ====================
    Rectangle {
        id: selector
        width: Enums.spacing.xl
        height: Enums.spacing.xl
        radius: width / 2
        color: Enums.transparent
        border.width: Enums.border.normal
        border.color: {
            // Use contrasting border color 使用对比边框色
            var lum = control.brightness * (1 - control.saturation * 0.5)
            return lum > 0.5 ? "black" : "white"
        }
        
        x: Math.max(0, Math.min(parent.width - width, control.hue * parent.width - width / 2))
        y: Math.max(0, Math.min(parent.height - height, (1 - control.saturation) * parent.height - height / 2))
        
        Behavior on x { NumberAnimation { duration: Enums.duration.fast } }
        Behavior on y { NumberAnimation { duration: Enums.duration.fast } }
    }
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        anchors.fill: parent
        enabled: control.enabled
        preventStealing: true
        
        function updateColor(mouse) {
            control.hue = Math.max(0, Math.min(1, mouse.x / width))
            control.saturation = Math.max(0, Math.min(1, 1 - mouse.y / height))
            control.colorChanged(control.hue, control.saturation)
        }
        
        onPressed: (mouse) => updateColor(mouse)
        onPositionChanged: (mouse) => { if (pressed) updateColor(mouse) }
    }
    
    // ==================== Border 边框 ====================
    Rectangle {
        anchors.fill: parent
        color: Enums.transparent
        radius: Enums.radius.large
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
    }
}
