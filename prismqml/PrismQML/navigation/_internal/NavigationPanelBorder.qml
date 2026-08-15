// NavigationPanelBorder - Navigation panel right border 导航面板右侧边框
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../.."

// Keeps border painting independent from panel orchestration 将边框绘制与面板编排分离
Item {
    id: borderLayer

    // ==================== Required Props 必需属性 ====================
    required property var panel

    // ==================== Internal Props 内部属性 ====================
    readonly property var control: panel

    anchors.fill: parent
    z: 0

    // Right border with rounded corners 带圆角的右侧边框
    Canvas {
        id: rightBorderCanvas

        readonly property real _paintRadius: control._cornerRadius

        function _scheduleBorderRepaint() {
            Qt.callLater(rightBorderCanvas.requestPaint)
        }

        anchors.fill: parent
        visible: control.borderEnabled && (control.backgroundColor.a > 0 || control.acrylicEnabled)  // Show when border enabled and bg visible 边框启用且背景可见时显示
        z: 0  // Above acrylic layer 在亚克力层之上

        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = control._cornerRadius
            var topOffset = control.titleBarHeight
            var borderWidth = Enums.border.normal
            ctx.clearRect(0, 0, w, h)

            // Draw right border with rounded corners 绘制带圆角的右侧边框
            ctx.strokeStyle = Enums.stateColor.navDivider.toString()
            ctx.lineWidth = borderWidth

            var offset = borderWidth / 2
            ctx.beginPath()
            if (r <= offset) {
                // Square ticket edge avoids a negative Canvas arc radius.
                // 票据直角边避免向 Canvas 传入负圆弧半径。
                ctx.moveTo(w - offset, topOffset + offset)
                ctx.lineTo(w - offset, h - offset)
            } else {
                // Top-right corner (below title bar) 右上圆角（标题栏下方）
                ctx.moveTo(w - r, topOffset + offset)
                ctx.arcTo(w - offset, topOffset + offset, w - offset, topOffset + r, r - offset)
                // Right edge 右侧边
                ctx.lineTo(w - offset, h - r)
                // Bottom-right corner 右下圆角
                ctx.arcTo(w - offset, h - offset, w - r, h - offset, r - offset)
            }
            ctx.stroke()
        }

        // Repaint right border on size change (debounced via Qt.callLater)
        // 尺寸变化时防抖重绘右边框 — 跟随事件循环节拍, 不绑 60fps
        onWidthChanged: _scheduleBorderRepaint()
        onHeightChanged: _scheduleBorderRepaint()
        on_PaintRadiusChanged: requestPaint()

        Connections {
            function onNavDividerChanged() { rightBorderCanvas.requestPaint() }
            target: Enums.stateColor
        }
    }


}
