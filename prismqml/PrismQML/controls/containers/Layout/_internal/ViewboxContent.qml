// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ViewboxContent - Viewbox visual layer Viewbox 视觉层
// Owns the natural size measurement, the axis scales and the scaled content host
// 承载自然尺寸测量、双轴缩放比与缩放后的内容宿主
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Public Props 公开属性 ====================
    default property alias content: contentHost.data

    // ==================== Readonly State 只读状态 ====================
    readonly property real naturalWidth: contentHost.childrenRect.width
    readonly property real naturalHeight: contentHost.childrenRect.height
    readonly property real scaleX: _axisScale(true)
    readonly property real scaleY: _axisScale(false)

    // ==================== Internal Methods 内部方法 ====================
    // Axis scale for the requested stretch mode 请求拉伸模式下的单轴缩放比
    function _axisScale(horizontal) {
        var natural = horizontal ? naturalWidth : naturalHeight
        var extent = horizontal ? content.width : content.height
        if (natural <= 0 || extent <= 0) return 1
        if (host.stretch === Image.Pad) return 1
        if (host.stretch === Image.Stretch) return extent / natural
        var fitScale = Math.min(
            content.width / naturalWidth, content.height / naturalHeight
        )
        if (host.stretch === Image.PreserveAspectFit) return fitScale
        if (host.stretch === Image.PreserveAspectCrop) {
            return Math.max(
                content.width / naturalWidth, content.height / naturalHeight
            )
        }
        return 1
    }

    // ==================== Size 尺寸 ====================
    clip: host.clipContent

    // ==================== Content 内容 ====================
    // Scaled content host 缩放内容宿主
    Item {
        id: contentHost
        objectName: "viewboxContentHost"
        implicitWidth: childrenRect.width
        implicitHeight: childrenRect.height
        width: implicitWidth
        height: implicitHeight
        x: (content.width - naturalWidth * content.scaleX) / 2
        y: (content.height - naturalHeight * content.scaleY) / 2

        transform: Scale {
            origin.x: 0
            origin.y: 0
            xScale: content.scaleX
            yScale: content.scaleY
        }
    }
}
