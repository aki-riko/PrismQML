// NavigationPanelBackground - Navigation panel visual background 导航面板视觉背景
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../.."

// Keeps background layers below navigation content 将背景层保持在导航内容下方
Item {
    id: backgroundLayer

    // ==================== Required Props 必需属性 ====================
    required property var panel

    // ==================== Internal Props 内部属性 ====================
    readonly property var control: panel

    anchors.fill: parent
    z: -2

    // Layer A: opaque background with right-side rounded corners 层A：右侧圆角不透明背景
    Canvas {
        id: bgCanvas

        readonly property color _backgroundColor: control.backgroundColor
        readonly property real _paintRadius: control._cornerRadius

        function _scheduleBgRepaint() {
            Qt.callLater(bgCanvas.requestPaint)
        }

        anchors.fill: parent
        z: 0  // Lowest layer within the background surface 背景层内部的最低层

        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = control._cornerRadius
            var topOffset = control.titleBarHeight  // Top-right corner starts below title bar 右上圆角从标题栏下方开始
            ctx.clearRect(0, 0, w, h)

            // Fill background 填充背景
            ctx.fillStyle = _backgroundColor.toString()
            ctx.beginPath()
            ctx.moveTo(0, 0)
            ctx.lineTo(w, 0)  // Top edge (no corner, extends into title bar) 顶边（无圆角，延伸到标题栏）
            ctx.lineTo(w, topOffset)  // Right edge above title bar 标题栏上方的右边
            ctx.lineTo(w - r, topOffset)  // Move to top-right corner start 移动到右上圆角起点
            ctx.arcTo(w, topOffset, w, topOffset + r, r)  // Top-right corner below title bar 标题栏下方的右上圆角
            ctx.lineTo(w, h - r)
            ctx.arcTo(w, h, w - r, h, r)  // Bottom-right corner 右下圆角
            ctx.lineTo(0, h)
            ctx.closePath()
            ctx.fill()
        }

        // Repaint when size or color changes (debounced via Qt.callLater)
        // 尺寸或颜色变化时防抖重绘 — Qt.callLater 自动合并同一事件循环中的多次调用,
        // 不绑死 60fps 帧时长, 跟随事件循环节拍刷新一次
        onWidthChanged: _scheduleBgRepaint()
        onHeightChanged: _scheduleBgRepaint()
        on_BackgroundColorChanged: requestPaint()
        on_PaintRadiusChanged: requestPaint()
    }

    TicketPaper {
        anchors.fill: parent
        patternOriginX: control.paperOriginX
        patternOriginY: control.paperOriginY
        visible: control.ticketPaperEnabled && Enums.isVintageTicket
        z: 1
    }

    // Layer B: Acrylic blurred background 层B：亚克力模糊背景
    Rectangle {
        id: acrylicLayer

        // Acrylic tint color: pure white/dark gray; keeps Mica tint 亚克力着色：纯白/深灰，保留云母色调
        readonly property color acrylicTintColor: Enums.stateColor.acrylicTintColor

        anchors.fill: parent
        visible: Enums.usesSoftElevation && control.acrylicEnabled && control.acrylicImageSource !== ""
        z: 1  // Below all content 在所有内容下方
        radius: control._cornerRadius
        clip: true
        color: Enums.transparent

        // Blurred background image 模糊背景图片
        Image {
            id: acrylicImage
            anchors.fill: parent
            source: control.acrylicImageSource
            fillMode: Image.PreserveAspectCrop
            cache: false  // Disable cache for dynamic updates 禁用缓存以支持动态更新
        }

        // Tint overlay (pure white/dark gray to preserve Mica tone) 着色叠加层（纯白/深灰保留云母色调）
        Rectangle {
            anchors.fill: parent
            color: acrylicLayer.acrylicTintColor
        }

        // Fill top-left corner (no radius) 填充左上角（无圆角）
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            width: parent.radius
            height: control.titleBarHeight + parent.radius
            color: Enums.transparent
            clip: true

            Image {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                width: acrylicImage.width
                height: acrylicImage.height
                source: control.acrylicImageSource
                fillMode: Image.PreserveAspectCrop
                cache: false
            }
            Rectangle {
                anchors.fill: parent
                color: acrylicLayer.acrylicTintColor
            }
        }

        // Fill bottom-left corner (no radius) 填充左下角（无圆角）
        Rectangle {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: parent.radius
            height: parent.radius
            color: Enums.transparent
            clip: true

            Image {
                anchors.right: parent.right
                anchors.top: parent.top
                width: acrylicImage.width
                height: acrylicImage.height
                source: control.acrylicImageSource
                fillMode: Image.PreserveAspectCrop
                cache: false
            }
            Rectangle {
                anchors.fill: parent
                color: acrylicLayer.acrylicTintColor
            }
        }
    }


}
