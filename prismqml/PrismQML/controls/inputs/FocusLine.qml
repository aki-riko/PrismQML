// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// FocusLine - Accent focus line for input controls 输入控件聚焦底线
// Uses a clipped rounded rectangle to expose only its bottom edge 使用裁剪后的圆角矩形，仅露出底边
// The bottom corners follow the parent radius without a custom path 底部两角随父组件圆角自然收口，无需手绘路径
Item {
    id: focusLine
    
    // ==================== Public Props 公开属性 ====================
    property bool showLine: false  // Control visibility 控制显示
    property color lineColor: Enums.accentColor
    property real parentRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small  // Parent corner radius 父组件圆角
    
    // ==================== Size 尺寸 ====================
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    height: Enums.border.normal  // Integer thickness avoids subpixel clipping 整数厚度避免亚像素裁剪不一致
    clip: true  // Clip to only show bottom part 裁剪只显示底部
    
    // Inner rounded rect, clipped by parent to a thin accent line 内部圆角矩形,被父级裁成细线
    Rectangle {
        id: lineRect
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        width: focusLine.showLine ? parent.width : 0
        height: Enums.controlSize.focusLineHeight
        radius: focusLine.parentRadius
        color: focusLine.lineColor
        
        Behavior on width { 
            NumberAnimation { 
                duration: Enums.duration.normal
                easing.type: Easing.OutCubic 
            } 
        }
    }
}
