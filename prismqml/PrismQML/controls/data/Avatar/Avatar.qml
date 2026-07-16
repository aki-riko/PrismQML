// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../Label"
import "../../icons"

// Avatar - Avatar component 头像组件
// Props: source(图片路径), text(文字), size(尺寸)
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string source: ""
    property string text: ""
    property int size: 40

    // ==================== Readonly State 只读状态 ====================
    readonly property color _avatarBackground: source !== "" ? Enums.transparent : Enums.accentColor
    readonly property int _avatarBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : (Enums.isPrismDesign ? Enums.prismDesign.borderWidth : 0)
    readonly property color _avatarBorderColor: Enums.isNeobrutalism ? Enums.stateColor.border : (Enums.isPrismDesign ? Enums.borderStrongColor : Enums.transparent)
    readonly property color _avatarContentColor: Enums.accentForeground

    // ==================== Public Methods 公开方法 ====================
    // Set avatar size 设置头像尺寸
    function setRadius(r) {
        size = r * 2
    }

    width: size
    height: size
    radius: size / 2
    color: control._avatarBackground
    antialiasing: true
    // Avatar boundary for non-Fluent skins 非 Fluent 皮肤头像边界
    border.width: control._avatarBorderWidth
    border.color: control._avatarBorderColor
    
    // Text avatar 文字头像
    Label {
        type: Enums.label.type_body
        anchors.centerIn: parent
        text: control.text.length > 0 ? control.text.charAt(0).toUpperCase() : ""
        font.pixelSize: size * 0.4
        font.bold: true
        color: control._avatarContentColor
        visible: source === "" && text !== ""
    }
    
    // Image avatar with Canvas clipping Canvas裁剪图片头像
    Canvas {
        id: avatarCanvas
        property var img: null

        anchors.fill: parent
        visible: control.source !== ""
        antialiasing: true
        renderStrategy: Canvas.Threaded
        renderTarget: Canvas.FramebufferObject

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            if (!img || img.status !== Image.Ready) return
            
            var w = width
            var h = height
            var r = Math.min(w, h) / 2
            
            // Draw circular clip path 绘制圆形裁剪路径
            ctx.beginPath()
            ctx.arc(w / 2, h / 2, r, 0, Math.PI * 2)
            ctx.closePath()
            ctx.clip()
            
            // Draw image centered and cropped 居中裁剪绘制图片
            var imgW = img.sourceSize.width
            var imgH = img.sourceSize.height
            var scale = Math.max(w / imgW, h / imgH)
            var drawW = imgW * scale
            var drawH = imgH * scale
            var dx = (w - drawW) / 2
            var dy = (h - drawH) / 2
            
            ctx.drawImage(img, dx, dy, drawW, drawH)
        }
        
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    
    // Image source - now using Image directly since custom Image renamed to ImageWidget 图片源 - 现在直接使用 Image，因为自定义 Image 已重命名为 ImageWidget
    Image {
        id: sourceImage
        source: control.source
        visible: false
        asynchronous: true
        onStatusChanged: {
            if (status === Image.Ready) {
                avatarCanvas.img = sourceImage
                avatarCanvas.requestPaint()
            }
        }
    }
    
    // Placeholder when no content 无内容时的占位符
    Icon {
        anchors.centerIn: parent
        icon: Enums.icon.person
        iconSize: size * 0.5
        color: control._avatarContentColor
        visible: control.source === "" && control.text === ""
    }
}
