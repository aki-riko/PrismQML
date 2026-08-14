// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NeumorphicInsetLayer - Rounded SDF inset shadow 圆角距离场内阴影层
Item {
    id: layer

    // ==================== Readonly State 只读状态 ====================
    readonly property Item control: parent
    readonly property Item target: control ? control.target : null
    readonly property real edgeSize: control ? control._edgeSize : 0
    readonly property color _darkColor: control ? control.darkColor : Enums.transparent
    readonly property color _lightColor: control ? control.lightColor : Enums.transparent

    // ==================== Size 尺寸 ====================
    objectName: "_neumorphicInsetLayer"
    anchors.fill: parent

    // ==================== Content 内容 ====================
    ShaderEffect {
        id: insetShader

        // ==================== Internal Props 内部属性 ====================
        property real itemWidth: width
        property real itemHeight: height
        property real cornerRadius: layer.target && layer.target.radius !== undefined
                                    ? layer.target.radius : 0
        property real shadowDepth: layer.edgeSize
        property real shadowSoftness: layer.control
                                      ? Math.min(Enums.neumorphism.insetSoftness,
                                                 layer.control.blur)
                                      : Enums.neumorphism.insetSoftness
        property real darkR: layer._darkColor.r
        property real darkG: layer._darkColor.g
        property real darkB: layer._darkColor.b
        property real darkOpacity: layer.control
                                   ? layer.control.insetDarkOpacity
                                   : Enums.opacityLevel.invisible
        property real lightR: layer._lightColor.r
        property real lightG: layer._lightColor.g
        property real lightB: layer._lightColor.b
        property real lightOpacity: layer.control
                                    ? layer.control.insetLightOpacity
                                    : Enums.opacityLevel.invisible

        objectName: "_neumorphicInsetShader"
        parent: layer.target ? layer.target : layer
        anchors.fill: parent
        z: Enums.zIndex.controlsAbove
        blending: true
        fragmentShader: Qt.resolvedUrl("../../shaders/neumorphic_inset.frag.qsb")
    }
}
