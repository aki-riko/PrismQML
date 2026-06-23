// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// ShadowedRectangle - High performance shadowed rectangle 高性能阴影矩形
// Uses Qt 6.9+ RectangularShadow (SDF-based, no layer.effect overhead) 使用 Qt 6.9+ RectangularShadow（基于 SDF，无离屏渲染开销）

// Usage 用法:
// ShadowedRectangle {
//     width: 200; height: 100
//     color: "white"
//     radius: Enums.radius.large
//     shadowLevel: Enums.shadow.level4
// }

Item {
    id: root
    
    // ==================== Rectangle Props 矩形属性 ====================
    property alias color: content.color
    property alias radius: content.radius
    property alias border: content.border
    
    // ==================== Shadow Props 阴影属性 ====================
    // Use shadow level from Enums 使用FluentEnums的阴影等级
    property var shadowLevel: Enums.shadow.level4
    
    // Shadow visibility control 阴影显隐控制
    property bool shadowVisible: true
    
    // Or set individual props 或单独设置属性
    // blur 现在直接是像素值，无需转换
    property real shadowBlur: shadowLevel ? shadowLevel.blur : (Enums.shadow && Enums.shadow.level4 ? Enums.shadow.level4.blur : 16)
    property color shadowColor: shadowLevel ? shadowLevel.color : (Enums.shadow && Enums.shadow.level4 ? Enums.shadow.level4.color : "#1A000000")
    property real shadowOffsetX: 0
    property real shadowOffsetY: shadowLevel ? shadowLevel.offset : (Enums.shadow && Enums.shadow.level4 ? Enums.shadow.level4.offset : 4)
    property real shadowSpread: 0
    
    // ==================== Content Access 内容访问 ====================
    default property alias contentData: content.data
    property alias contentItem: content
    
    // ==================== Shadow Access 阴影访问 ====================
    // Expose shadow for animation binding 暴露阴影供动画绑定
    property alias shadowItem: shadow
    
    // ==================== Size 尺寸 ====================
    implicitWidth: content.implicitWidth
    implicitHeight: content.implicitHeight
    
    // ==================== Shadow Layer 阴影层 ====================
    RectangularShadow {
        id: shadow
        anchors.fill: content
        radius: content.radius
        color: root.shadowColor
        blur: root.shadowBlur
        spread: root.shadowSpread
        offset.x: root.shadowOffsetX
        offset.y: root.shadowOffsetY
        visible: root.shadowVisible
    }
    
    // ==================== Content Layer 内容层 ====================
    Rectangle {
        id: content
        anchors.fill: parent
        color: Enums.cardColor
        radius: Enums.radius.large
    }
}
