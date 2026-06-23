// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."

// FocusLine - Accent focus line for input controls 输入控件聚焦底线
// 实现:用一个圆角矩形作为内容,外层 Item 限高 2px 并 clip,只露出矩形底边
//      这样底部两角随父组件圆角自然收口,无需手动绘制路径
Item {
    id: focusLine
    
    // ==================== Props 属性 ====================
    property bool showLine: false  // Control visibility 控制显示
    property color lineColor: Enums.accentColor
    property real parentRadius: Enums.radius.small  // Parent corner radius 父组件圆角
    
    // ==================== Layout 布局 ====================
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    height: Enums.border.normal  // 2px 整数避免亚像素裁剪不一致
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
