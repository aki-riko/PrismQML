// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// ContentFrame - Reusable content area with rounded corner and border 可复用的圆角边框内容区域
// Used by Window and compact-nav window 用于 Window 和 compact-nav window
Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property color backgroundColor
    required property int cornerRadius
    
    // ==================== Content Slot 内容插槽 ====================
    default property alias content: contentItem.data
    
    // ==================== Background 背景 ====================
    Rectangle {
        id: background
        anchors.fill: parent
        color: root.backgroundColor
        radius: root.cornerRadius
        
        // Bottom-left corner fill 左下角填充
        Rectangle {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: root.cornerRadius
            height: root.cornerRadius
            color: parent.color
        }
        
        // Top-right corner fill 右上角填充
        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            width: root.cornerRadius
            height: root.cornerRadius
            color: parent.color
        }
    }
    
    // ==================== Border Canvas 边框画布 ====================
    Canvas {
        id: borderCanvas
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = root.cornerRadius
            ctx.clearRect(0, 0, w, h)
            // neo: 粗黑边; Fluent: 细 contentBorder
            var neo = Enums.isNeobrutalism
            ctx.strokeStyle = (neo ? Enums.neo.borderColor : Enums.stateColor.contentBorder).toString()
            ctx.lineWidth = neo ? Enums.neo.borderWidth : Enums.border.thin
            var off = ctx.lineWidth / 2  // 描边中心偏移, 对齐像素
            // Top border 顶部边框
            ctx.beginPath()
            ctx.moveTo(r, off)
            ctx.lineTo(w, off)
            ctx.stroke()
            // Left border 左侧边框
            ctx.beginPath()
            ctx.moveTo(off, r)
            ctx.lineTo(off, h)
            ctx.stroke()
            // Top-left arc 左上角圆弧
            ctx.beginPath()
            ctx.arc(r, r, r - off, Math.PI, Math.PI * 1.5)
            ctx.stroke()
        }
        
        Component.onCompleted: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    
    // ==================== Theme Connection 主题连接 ====================
    Connections {
        target: ThemeManager
        function onThemeChanged() { borderCanvas.requestPaint() }
        function onSkinChanged() { borderCanvas.requestPaint() }
    }
    
    // ==================== Content Container 内容容器 ====================
    Item {
        id: contentItem
        anchors.fill: parent
        anchors.topMargin: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
        anchors.leftMargin: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
        clip: true

        // 点击空白区域时清除输入焦点（z:-1 确保在页面内容之下）
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: contentItem.forceActiveFocus()
        }
    }
}
