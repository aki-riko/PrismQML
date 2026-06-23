// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import ".."
import "../../icons"
import "../../data/Label"

// BeforeAfterSlider - Image comparison component 图片对比滑块
// Image comparison slider with Fluent Design styling 图像对比滑块（Fluent Design 风格）
Item {
    id: control
    
    property url leftImage: ""
    property url rightImage: ""
    property real position: 0.5  // 0-1
    property int radius: Enums.radius.large  // Corner radius 圆角
    
    signal positionModified(real newPosition)
    
    implicitWidth: 300
    implicitHeight: 200
    clip: true  // Clip handle overflow 裁剪手柄溢出
    
    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: parent
        radius: control.radius
        color: Enums.shadow.level8.color
        blur: Enums.shadow.level8.blur
        offset: Qt.vector2d(0, Enums.shadow.level8.offset)
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: control
        visible: Enums.isNeobrutalism
        radius: control.radius
        z: -1
    }
    
    // Canvas for rounded corner images 使用Canvas实现圆角图片
    Canvas {
        id: imageCanvas
        anchors.fill: parent
        antialiasing: true
        renderStrategy: Canvas.Threaded
        renderTarget: Canvas.FramebufferObject
        
        property var leftImg: null
        property var rightImg: null
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            var w = width
            var h = height
            var r = control.radius
            var pos = control.position
            
            // Draw rounded rect clip path 绘制圆角矩形裁剪路径
            ctx.beginPath()
            ctx.moveTo(r, 0)
            ctx.lineTo(w - r, 0)
            ctx.arcTo(w, 0, w, r, r)
            ctx.lineTo(w, h - r)
            ctx.arcTo(w, h, w - r, h, r)
            ctx.lineTo(r, h)
            ctx.arcTo(0, h, 0, h - r, r)
            ctx.lineTo(0, r)
            ctx.arcTo(0, 0, r, 0, r)
            ctx.closePath()
            ctx.clip()
            
            // Draw right image (full) 绘制右侧图片（完整）
            if (rightImg && rightImg.status === Image.Ready) {
                drawImageCrop(ctx, rightImg, 0, 0, w, h)
            }
            
            // Draw left image (clipped by position) 绘制左侧图片（按位置裁剪）
            if (leftImg && leftImg.status === Image.Ready) {
                ctx.save()
                ctx.beginPath()
                ctx.rect(0, 0, w * pos, h)
                ctx.clip()
                drawImageCrop(ctx, leftImg, 0, 0, w, h)
                ctx.restore()
            }
        }
        
        function drawImageCrop(ctx, img, x, y, w, h) {
            var imgW = img.sourceSize.width
            var imgH = img.sourceSize.height
            if (imgW <= 0 || imgH <= 0) return
            
            var scale = Math.max(w / imgW, h / imgH)
            var drawW = imgW * scale
            var drawH = imgH * scale
            var dx = x + (w - drawW) / 2
            var dy = y + (h - drawH) / 2
            
            ctx.drawImage(img, dx, dy, drawW, drawH)
        }
        
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    
    // Image sources: now using Image directly (custom Image renamed to ImageWidget) 图片源：现在直接使用 Image，因为自定义 Image 已重命名为 ImageWidget

    Image {
        id: leftSource
        source: control.leftImage
        visible: false
        asynchronous: true
        onStatusChanged: {
            if (status === Image.Ready) {
                imageCanvas.leftImg = leftSource
                imageCanvas.requestPaint()
            }
        }
    }
    
    Image {
        id: rightSource
        source: control.rightImage
        visible: false
        asynchronous: true
        onStatusChanged: {
            if (status === Image.Ready) {
                imageCanvas.rightImg = rightSource
                imageCanvas.requestPaint()
            }
        }
    }
    
    // Repaint when position changes 位置变化时重绘
    onPositionChanged: imageCanvas.requestPaint()
    
    // Divider line 分割线
    Rectangle {
        id: dividerLine
        x: parent.width * control.position - width / 2
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: Enums.border.normal
        color: "white"
        
        // Line shadow 线条阴影
        Rectangle {
            anchors.fill: parent
            anchors.margins: -1
            color: Enums.stateColor.maskLight
            z: Enums.zIndex.background
        }
    }
    
    // Handle 手柄
    Rectangle {
        id: handle
        x: parent.width * control.position - width / 2
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.spacing.xxl
        height: Enums.spacing.xxl
        radius: width / 2
        color: "white"
        
        // Handle shadow 手柄阴影
        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            radius: width / 2
            color: Enums.stateColor.maskSubtle
            z: Enums.zIndex.background
        }
        
        // Double arrow icon 双箭头图标
        Label {
            type: Enums.label.type_body
            anchors.centerIn: parent
            text: "⇌"
            font.bold: true
            color: Enums.gray.text
            rotation: 90
        }
        
        scale: dragArea.pressed ? 0.95 : (dragArea.containsMouse ? 1.08 : 1.0)
        Behavior on scale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutBack } }
    }
    
    MouseArea {
        id: dragArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        cursorShape: Qt.SizeHorCursor
        
        onPositionChanged: if (pressed) updatePosition(mouseX)
        onPressed: updatePosition(mouseX)
        
        function updatePosition(mx) {
            // Clamp position with handle margin 限制位置范围，预留手柄边距
            var margin = handle.width / 2 / width  // Convert to 0-1 range 转换为0-1范围
            var newPos = Math.max(margin, Math.min(1 - margin, mx / width))
            control.position = newPos
            control.positionModified(newPos)
        }
    }
}
