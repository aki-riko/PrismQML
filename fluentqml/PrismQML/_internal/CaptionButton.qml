// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."

// CaptionButton - Windows 11 style caption button 标题栏按钮
// Extracted from WindowsCore for modularity 从WindowsCore提取以模块化
Rectangle {
    id: captionBtn
    
    // ==================== Required Props 必需属性 ====================
    required property var targetWindow  // Parent window 父窗口
    
    // ==================== Props 属性 ====================
    property string iconType: "minimize"  // minimize, maximize, restore, close
    property bool isClose: iconType === "close"
    property int buttonWidth: Enums.window.captionButtonWidth
    property int buttonHeight: Enums.window.captionButtonHeight
    
    signal clicked()
    
    width: buttonWidth
    height: buttonHeight
    
    color: {
        if (area.pressed) {
            return isClose 
                ? Enums.windowButtonColors.closePressed 
                : (Enums.isDark ? Enums.windowButtonColors.normalPressedDark : Enums.windowButtonColors.normalPressedLight)
        }
        if (area.containsMouse) {
            return isClose 
                ? Enums.windowButtonColors.closeHover 
                : (Enums.isDark ? Enums.windowButtonColors.normalHoverDark : Enums.windowButtonColors.normalHoverLight)
        }
        return Enums.transparent
    }
    
    // Draw icon with Canvas 用Canvas绘制图标
    Canvas {
        anchors.centerIn: parent
        width: Enums.window.captionIconSize
        height: Enums.window.captionIconSize
        
        readonly property color iconColor: area.containsMouse && captionBtn.isClose 
            ? Enums.windowButtonColors.iconLight 
            : (Enums.isDark ? Enums.windowButtonColors.iconLight : Enums.windowButtonColors.iconDark)
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.strokeStyle = iconColor
            ctx.lineWidth = 1
            
            if (captionBtn.iconType === "minimize") {
                // Horizontal line 横线
                ctx.beginPath()
                ctx.moveTo(0, 5)
                ctx.lineTo(width, 5)
                ctx.stroke()
            } else if (captionBtn.iconType === "maximize") {
                // Square frame 方框
                ctx.strokeRect(0.5, 0.5, width - 1, height - 1)
            } else if (captionBtn.iconType === "restore") {
                // Two overlapping squares 两个重叠方框
                ctx.strokeRect(2.5, 0.5, width - 3, height - 3)
                ctx.strokeRect(0.5, 2.5, width - 3, height - 3)
                ctx.clearRect(2.5, 2.5, width - 5, height - 5)
                ctx.strokeRect(2.5, 2.5, width - 5, height - 5)
            } else if (captionBtn.iconType === "close") {
                // X
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(width, height)
                ctx.moveTo(width, 0)
                ctx.lineTo(0, height)
                ctx.stroke()
            }
        }
        
        onIconColorChanged: requestPaint()
        Component.onCompleted: requestPaint()
    }
    
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            captionBtn.clicked()
        }
    }
}
