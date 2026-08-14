// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."

// NeumorphicOuterShadow - Lazily loaded convex shadow pair 按需加载的新拟态凸起双阴影
Item {
    id: layer

    // ==================== Readonly State 只读状态 ====================
    readonly property Item control: parent
    readonly property Item target: control ? control.target : null

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    RectangularShadow {
        objectName: "_neumorphicDarkOuterShadow"
        anchors.fill: parent
        radius: layer.target && layer.target.radius !== undefined
                ? layer.target.radius : 0
        color: layer.control && layer.control.accent
               ? Enums.accentColor : (layer.control ? layer.control.darkColor : Enums.transparent)
        blur: layer.control ? layer.control.blur : 0
        offset.x: layer.control ? layer.control.offset : 0
        offset.y: layer.control ? layer.control.offset : 0
        spread: layer.control ? layer.control.spread : 0
    }

    RectangularShadow {
        objectName: "_neumorphicLightOuterShadow"
        anchors.fill: parent
        radius: layer.target && layer.target.radius !== undefined
                ? layer.target.radius : 0
        color: layer.control ? layer.control.lightColor : Enums.transparent
        blur: layer.control ? layer.control.blur : 0
        offset.x: layer.control ? -layer.control.offset : 0
        offset.y: layer.control ? -layer.control.offset : 0
        spread: layer.control ? layer.control.spread : 0
    }
}
