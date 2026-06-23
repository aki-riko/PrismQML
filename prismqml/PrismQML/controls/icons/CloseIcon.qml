// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."  // FluentEnums

// CloseIcon - Reusable close/cancel icon 可复用的关闭/取消图标
// Draw X shape 绘制 X 形状
Canvas {
    id: control
    
    property color color: Enums.textColor.primary
    property real strokeWidth: Enums.border.normal
    
    width: Enums.controlSize.checkIconSize
    height: Enums.controlSize.checkIconSize
    
    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        
        ctx.strokeStyle = color
        ctx.lineWidth = strokeWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.beginPath()
        
        // Draw X shape 绘制X形状
        ctx.moveTo(width * 0.15, height * 0.15)
        ctx.lineTo(width * 0.85, height * 0.85)
        ctx.moveTo(width * 0.85, height * 0.15)
        ctx.lineTo(width * 0.15, height * 0.85)
        ctx.stroke()
    }
    
    onColorChanged: requestPaint()
    Component.onCompleted: requestPaint()
}
