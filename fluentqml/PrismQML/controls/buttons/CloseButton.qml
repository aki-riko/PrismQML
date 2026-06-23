// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"

// CloseButton - Simple close/dismiss icon button 简单的关闭图标按钮（轻量重写，避免ButtonCore污染）
Item {
    id: control

    // ==================== Props 属性 ====================
    property int size: Enums.controlSize.closeButtonSize
    property int iconSizeValue: Enums.iconSize.s
    property color normalIconColor: Enums.textColor.secondary
    property color hoverIconColor: Enums.textColor.primary
    property color hoverBgColor: Enums.stateColor.transparentHover  // Hover background 悬浮背景色
    property color pressedBgColor: Enums.stateColor.transparentPressed  // Pressed background 按下背景色
    
    // Button compatibility compatibility 按钮兼容性属性
    property alias icon: iconItem.icon
    
    // ==================== State 状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed

    // ==================== Signals 信号 ====================
    signal clicked()
    // 不能命名为 pressed, 会与上方 `property bool pressed` 同名被遮蔽; 外部用 onButtonPressed
    signal buttonPressed()
    signal released()

    // ==================== Size 尺寸 ====================
    width: size
    height: size

    // ==================== Background 背景 ====================
    Rectangle {
        anchors.fill: parent
        radius: control.width / 2
        color: control.pressed ? control.pressedBgColor : (control.hovered ? control.hoverBgColor : Enums.stateColor.controlBgTransparent)
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    }

    // ==================== Icon 图标 ====================
    Icon {
        id: iconItem
        anchors.centerIn: parent
        icon: Enums.icon.dismiss
        iconSize: control.iconSizeValue
        color: control.hovered ? control.hoverIconColor : control.normalIconColor
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    }

    // ==================== Interaction 交互 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: control.clicked()
        onPressed: control.buttonPressed()
        onReleased: control.released()
    }
}
