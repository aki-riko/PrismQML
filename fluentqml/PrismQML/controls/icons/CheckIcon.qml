// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."  // FluentEnums

// CheckIcon - 可复用的勾选标记图标
// state: 0=无, 1=部分选中(横线), 2=完全选中(勾)
Canvas {
    id: control
    
    property color color: Enums.accentColor
    property real strokeWidth: Enums.border.normal
    property int state: 2  // 0=无, 1=部分选中, 2=完全选中
    property bool checked: state === 2  // Legacy compat 兼容旧接口
    
    width: Enums.controlSize.checkIconSize
    height: Enums.controlSize.checkIconSize
    
    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        if (state === 0) return
        
        ctx.strokeStyle = color
        ctx.lineWidth = strokeWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.beginPath()
        
        if (state === 2) {
            // Fully checked: draw checkmark 完全选中绘制勾
            ctx.moveTo(width * 0.15, height * 0.5)
            ctx.lineTo(width * 0.4, height * 0.75)
            ctx.lineTo(width * 0.85, height * 0.25)
        } else if (state === 1) {
            // Partial: draw horizontal line 部分选中绘制横线
            ctx.moveTo(width * 0.15, height * 0.5)
            ctx.lineTo(width * 0.85, height * 0.5)
        }
        ctx.stroke()
    }
    
    onColorChanged: requestPaint()
    onStateChanged: requestPaint()
    Component.onCompleted: requestPaint()
}
