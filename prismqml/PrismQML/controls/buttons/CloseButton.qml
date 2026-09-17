// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"

// CloseButton - Simple close/dismiss icon button 简单的关闭图标按钮（轻量重写，避免ButtonCore污染）
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int size: Enums.controlSize.closeButtonSize
    property int iconSizeValue: Enums.iconSize.s
    property color normalIconColor: Enums.textColor.secondary
    property color hoverIconColor: Enums.textColor.primary
    property color hoverBgColor: Enums.stateColor.transparentHover  // Hover background 悬浮背景色
    property color pressedBgColor: Enums.stateColor.transparentPressed  // Pressed background 按下背景色
    
    // Button compatibility properties 按钮兼容属性
    property alias icon: iconItem.icon
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)

    // ==================== Signals 信号 ====================
    signal clicked()
    // "pressed" would collide with the readonly property; consumers use onButtonPressed “pressed” 会与只读属性冲突，外部使用 onButtonPressed
    signal buttonPressed()
    signal released()

    // ==================== Size 尺寸 ====================
    width: size
    height: size

    // ==================== Content 内容 ====================
    // Background 背景
    Rectangle {
        anchors.fill: parent
        radius: control.width / 2
        color: control.pressed ? control.pressedBgColor : (control._touchActive ? control.hoverBgColor : Enums.stateColor.controlBgTransparent)
        HoverBehavior on color {
            active: control._touchActive && !control.pressed
            enterDuration: Enums.duration.fast
        }
    }

    // Icon 图标
    Icon {
        id: iconItem
        anchors.centerIn: parent
        icon: Enums.icon.dismiss
        iconSize: control.iconSizeValue
        color: control._touchActive ? control.hoverIconColor : control.normalIconColor
        HoverBehavior on color {
            active: control._touchActive
            enterDuration: Enums.duration.fast
        }
    }

    // Interaction 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: control.clicked()
        onPressed: control.buttonPressed()
        onReleased: control.released()
    }
}
