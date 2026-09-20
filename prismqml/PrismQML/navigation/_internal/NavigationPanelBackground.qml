// NavigationPanelBackground - Navigation panel visual background 导航面板视觉背景
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import QtQuick.Effects
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
        visible: Enums.usesSoftElevation && control.acrylicEnabled
                 && control.acrylicImageSource !== ""
                 && GraphicsInfo.api !== GraphicsInfo.Unknown
        z: 1  // Below all content 在所有内容下方
        radius: control._cornerRadius
        // Item.clip only clips a rectangle. Mask the capture and tint together,
        // with the visible top-right corner below the off-window title offset.
        // Item.clip 只按矩形裁剪。截图和着色必须一起遮罩，右上圆角从窗口外的
        // 标题栏偏移之后开始，才能与面板边框的可见轮廓一致。
        clip: true
        color: Enums.transparent
        // Software has no shader effects; keep its existing image rendering.
        // 软件后端不执行着色器效果，保留其原有图片绘制。
        layer.enabled: acrylicLayer.visible
                       && GraphicsInfo.api !== GraphicsInfo.Software
                       && GraphicsInfo.api !== GraphicsInfo.Unknown
                       && GraphicsInfo.api !== GraphicsInfo.Null
        layer.smooth: true
        layer.effect: MultiEffect {
            maskEnabled: true
            // A zero threshold with full spread passes transparent mask pixels.
            // 零阈值配合完整扩散会放行透明像素；中点阈值才保留真实 alpha 裁剪。
            maskThresholdMin: Enums.mask.thresholdMin
            maskSpreadAtMin: Enums.mask.spreadFull
            maskSource: ShaderEffectSource {
                hideSource: true
                live: true
                smooth: true
                sourceItem: Item {
                    width: acrylicLayer.width
                    height: acrylicLayer.height

                    Rectangle {
                        width: parent.width
                        height: control.titleBarHeight
                        color: Enums.textColor.primary
                    }

                    Rectangle {
                        y: control.titleBarHeight
                        width: parent.width
                        height: Math.max(0, parent.height - y)
                        topLeftRadius: Enums.radius.none
                        bottomLeftRadius: Enums.radius.none
                        topRightRadius: control._cornerRadius
                        bottomRightRadius: control._cornerRadius
                        antialiasing: true
                        color: Enums.textColor.primary
                    }
                }
            }
        }

        // Blurred background image 模糊背景图片
        // The capture covers the panel inside the window, while this layer
        // starts one title bar higher: anchor the image to that offset and keep
        // the capture's own height. Filling the whole layer instead stretched
        // the blur by height/height-titleBarHeight and lifted it by one title
        // bar, so the acrylic ghosted a second, offset copy of the panel behind
        // the real content. 截图取的是窗口内的面板区域, 而本层比窗口高出一个标题栏:
        // 图像必须按该偏移下移并使用截图自身高度。铺满整层会把模糊图纵向拉伸
        // height/(height-titleBarHeight) 倍并整体上移一个标题栏, 于是在真实内容
        // 后面多出一层错位的亚克力重影。
        Image {
            id: acrylicImage

            anchors.left: parent.left
            anchors.right: parent.right
            y: control.titleBarHeight
            height: Math.max(0, parent.height - control.titleBarHeight)
            source: control.acrylicImageSource
            fillMode: Image.PreserveAspectCrop
            cache: false  // Disable cache for dynamic updates 禁用缓存以支持动态更新
        }

        // Tint overlay (pure white/dark gray to preserve Mica tone) 着色叠加层（纯白/深灰保留云母色调）
        Rectangle {
            anchors.fill: parent
            color: acrylicLayer.acrylicTintColor
        }
    }


}
