// ButtonSurface - Button visual surface and color animation surface 按钮视觉表面与颜色动画表面
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import ".."

// ButtonSurface - Owns shadows, face, and animated surface colors 承载阴影、按钮面与动画颜色
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var buttonControl

    // ==================== Public Props 公开属性 ====================
    property alias background: background
    property alias border: background.border
    property alias bgColorAnimation: bgColorAnimation
    property alias borderColorAnimation: borderColorAnimation

    // ==================== Readonly State 只读状态 ====================
    readonly property real animatedPressShift:
        neoShadowLoader.item ? neoShadowLoader.item.animatedPressShift : 0
    readonly property var pressTransform:
        neoShadowLoader.item ? neoShadowLoader.item.pressTransform : null

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Fluent shadow surface 流畅阴影表面
    RectangularShadow {
        anchors.fill: background
        radius: background.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: !surface.buttonControl.flat && Enums.usesSoftElevation
                 && !Enums.isNeumorphism && !Enums.isNeumorphism
    }

    // Neumorphic shadow surface 新拟态阴影表面
    NeumorphicShadow {
        target: background
        inset: surface.buttonControl.pressed
        pressed: surface.buttonControl.pressed
        visible: !surface.buttonControl.flat && Enums.isNeumorphism
        z: background.z - 1
    }

    // Lazy Neo shadow surface 懒加载 Neo 阴影表面
    Loader {
        id: neoShadowLoader
        active: Enums.isNeobrutalism && !surface.buttonControl.flat
        z: background.z - 1

        sourceComponent: ButtonNeoShadow {
            target: surface.background
            targetPressShift: surface.buttonControl._neoPressTargetShift
        }
    }

    // Background button face 按钮背景面
    Rectangle {
        id: background

        anchors.fill: parent
        radius: surface.buttonControl.radius
        color: surface.buttonControl._animatedBgColor
        border.width: surface.buttonControl.flat ? 0 : Enums.surfaceBorderWidth(
            (surface.buttonControl._styleToggleChecked
             && surface.buttonControl.style === Enums.button.style_primary)
                ? Enums.border.normal : Enums.border.thin)
        border.color: surface.buttonControl._animatedBorderColor
        gradient: surface.buttonControl.style === Enums.button.style_gradient
                  && !Enums.isVintageTicket ? Enums._buttonGradientDef : null
        transform: surface.pressTransform
    }

    // Hover and press color animations 悬浮与按压颜色动画
    ColorAnimation {
        id: bgColorAnimation

        target: surface.buttonControl
        property: "_animatedBgColor"
        to: surface.buttonControl._targetBgColor
        duration: Enums.duration.medium
        easing.type: Easing.InOutCubic
    }

    ColorAnimation {
        id: borderColorAnimation

        target: surface.buttonControl
        property: "_animatedBorderColor"
        to: surface.buttonControl._targetBorderColor
        duration: Enums.duration.medium
    }
}
