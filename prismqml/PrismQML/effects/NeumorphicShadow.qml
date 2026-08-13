// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// NeumorphicShadow - paired soft light/dark shadows 新拟态双向软阴影
// One reusable primitive provides convex and concave surfaces for all controls.
// 统一提供凸起与凹入表面，避免控件散落手写阴影。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property Item target

    // ==================== Public Props 公开属性 ====================
    property bool inset: false
    property bool pressed: false
    property bool accent: false
    property real offset: Enums.neumorphism.shadowOffset
    property real blur: Enums.neumorphism.shadowBlur
    property color darkColor: Enums.neumorphism.shadowDark
    property color lightColor: Enums.neumorphism.shadowLight

    // ==================== Size 尺寸 ====================
    anchors.fill: target

    // ==================== Content 内容 ====================
    RectangularShadow {
        id: darkShadow
        anchors.fill: parent
        radius: target ? target.radius : 0
        color: root.accent ? Enums.accentColor : root.darkColor
        blur: root.blur
        offset.x: root.inset ? -root.offset : root.offset
        offset.y: root.inset ? -root.offset : root.offset
        spread: root.inset ? -root.offset / 2 : 0
        visible: !root.inset
    }

    RectangularShadow {
        id: lightShadow
        anchors.fill: parent
        radius: target ? target.radius : 0
        color: root.lightColor
        blur: root.blur
        offset.x: root.inset ? root.offset : -root.offset
        offset.y: root.inset ? root.offset : -root.offset
        spread: root.inset ? -root.offset / 2 : 0
        visible: true
    }
}
