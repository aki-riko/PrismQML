// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../SkinResolver.js" as SkinResolver
import "../effects"

// ContentFrame - Reusable content area with rounded corner and border 可复用的圆角边框内容区域
// Used by Window and compact-nav window 用于 Window 和 compact-nav window
Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property color backgroundColor
    required property int cornerRadius
    
    // ==================== Public Props 公开属性 ====================
    property bool ticketPaperEnabled: true
    property real paperOriginX: 0
    property real paperOriginY: 0
    // Explicit context is used by a window surface that has been reparented.
    // 普通内容自动继承最近范围；窗口表面重挂后可显式传入上下文。
    property var skinContext: null
    default property alias content: contentItem.data

    // ==================== Readonly State 只读状态 ====================
    readonly property var effectiveSkinContext:
        skinContext || _nearestSkinContext || Enums
    readonly property var _skin: effectiveSkinContext
    // Automatic scope lookup stays local to descendants; only an explicit
    // bridge must short-circuit their own ancestor walk.
    // 后代的自动范围查找保持独立；只有显式桥接才需要截断其自身祖先查找。
    readonly property var _prismSkinScopeContext: skinContext || null
    readonly property int _effectiveRadius: _skin.surfaceRadius(cornerRadius)
    readonly property real _effectiveBorderWidth: _skin.surfaceBorderWidth(_skin.border.thin)

    // ==================== Internal Props 内部属性 ====================
    property var _nearestSkinContext: null

    // ==================== Internal Methods 内部方法 ====================
    function _resolveSkinContext() {
        if (skinContext) {
            _nearestSkinContext = null
            return
        }
        _nearestSkinContext = SkinResolver.nearestContext(parent)
    }

    onParentChanged: _resolveSkinContext()
    onSkinContextChanged: _resolveSkinContext()
    onEffectiveSkinContextChanged: borderCanvas.requestPaint()
    Component.onCompleted: _resolveSkinContext()

    // ==================== Content 内容 ====================
    // Background. 背景。
    Rectangle {
        id: background
        anchors.fill: parent
        color: root.backgroundColor
        radius: root._effectiveRadius

        TicketPaper {
            anchors.fill: parent
            skinContext: root.effectiveSkinContext
            patternOriginX: root.paperOriginX
            patternOriginY: root.paperOriginY
            visible: root.ticketPaperEnabled && root._skin.isVintageTicket
        }
        
        // Bottom-left corner fill. 左下角填充。
        Rectangle {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: root._effectiveRadius
            height: root._effectiveRadius
            color: parent.color
        }
        
        // Top-right corner fill. 右上角填充。
        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            width: root._effectiveRadius
            height: root._effectiveRadius
            color: parent.color
        }
    }
    
    // Border canvas. 边框画布。
    Canvas {
        id: borderCanvas
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = root._effectiveRadius
            ctx.clearRect(0, 0, w, h)
            // Outlined skins use their ink border; Fluent keeps the content border.
            // 描边皮肤使用自身油墨边框；Fluent 保持内容边框。
            ctx.strokeStyle = (root._skin.hasOutlinedSurfaces
                ? root._skin.borderColor : root._skin.stateColor.contentBorder).toString()
            ctx.lineWidth = root._effectiveBorderWidth
            var off = ctx.lineWidth / 2  // Center the stroke on pixels. 将描边中心与像素对齐。
            if (r <= off) {
                // Join square top and left strokes at one physical-pixel center.
                // 方角顶边与左边在同一个物理像素中心连续转折。
                ctx.beginPath()
                ctx.moveTo(w, off)
                ctx.lineTo(off, off)
                ctx.lineTo(off, h)
                ctx.stroke()
            } else {
                // Top border. 顶部边框。
                ctx.beginPath()
                ctx.moveTo(r, off)
                ctx.lineTo(w, off)
                ctx.stroke()
                // Left border. 左侧边框。
                ctx.beginPath()
                ctx.moveTo(off, r)
                ctx.lineTo(off, h)
                ctx.stroke()
                // Top-left arc. 左上角圆弧。
                ctx.beginPath()
                ctx.arc(r, r, r - off, Math.PI, Math.PI * 1.5)
                ctx.stroke()
            }
        }
        
        Component.onCompleted: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    
    // Theme repaint connection. 主题重绘连接。
    Connections {
        function onIsDarkChanged() { borderCanvas.requestPaint() }
        function onSkinChanged() { borderCanvas.requestPaint() }
        target: root.effectiveSkinContext
    }
    
    // Content container. 内容容器。
    Item {
        id: contentItem
        anchors.fill: parent
        anchors.topMargin: root._effectiveBorderWidth
        anchors.leftMargin: root._effectiveBorderWidth
        clip: true

        // Clear input focus from blank space; keep this below page content. 点击空白处清除输入焦点，并保持在页面内容下方。
        MouseArea {
            anchors.fill: parent
            z: root._skin.zIndex.background
            onClicked: contentItem.forceActiveFocus()
        }
    }

}
