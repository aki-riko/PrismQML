// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"

// CycleWheelPickerButtons - Scroll button surfaces 滚轮选择器滚动按钮表面
// Keeps CycleWheelPicker focused on selection state, views and repeat timing.
// 将 CycleWheelPicker 入口限制为选择状态、视图与重复计时编排。
Rectangle {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var wheelControl

    // ==================== Readonly State 只读状态 ====================
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(upArea.containsMouse, upArea.pressed)

    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    height: Enums.controlSize.wheelPickerItemHeight
    color: _touchActive ? Enums.stateColor.controlBgHover : Enums.transparent
    // Hover-revealed scroll affordance: on touch it must stay reachable, so it stays visible
    // 悬停才揭示的滚动按钮: 触摸端必须保持可点, 因此常显
    visible: wheelControl.showScrollButtons && Touch.reveal(wheelControl._hovered)
    z: Enums.zIndex.popup

    Icon {
        anchors.centerIn: parent
        icon: Enums.icon.chevron_up
        iconSize: upArea.pressed ? Enums.iconSize.xs : Enums.iconSize.s
        color: Enums.textColor.secondary
    }

    MouseArea {
        id: upArea

        anchors.fill: parent
        hoverEnabled: true

        onClicked: wheelControl.scrollUp()
        onPressed: wheelControl._startRepeat(-1)
        onReleased: wheelControl._stopRepeat(-1)
        onExited: wheelControl._stopRepeat(-1)
    }

    Rectangle {
        id: downButton

        // ==================== Readonly State 只读状态 ====================
        // Touch has no hover preview: on touch the hover treatment follows the press
        // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
        readonly property bool _touchActive: Touch.feedback(downArea.containsMouse, downArea.pressed)

        parent: wheelControl
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: Enums.controlSize.wheelPickerItemHeight
        color: _touchActive ? Enums.stateColor.controlBgHover : Enums.transparent
        // Hover-revealed scroll affordance: on touch it must stay reachable, so it stays visible
        // 悬停才揭示的滚动按钮: 触摸端必须保持可点, 因此常显
        visible: wheelControl.showScrollButtons && Touch.reveal(wheelControl._hovered)
        z: Enums.zIndex.popup

        Icon {
            anchors.centerIn: parent
            icon: Enums.icon.chevron_down
            iconSize: downArea.pressed ? Enums.iconSize.xs : Enums.iconSize.s
            color: Enums.textColor.secondary
        }

        MouseArea {
            id: downArea

            anchors.fill: parent
            hoverEnabled: true

            onClicked: wheelControl.scrollDown()
            onPressed: wheelControl._startRepeat(1)
            onReleased: wheelControl._stopRepeat(1)
            onExited: wheelControl._stopRepeat(1)
        }
    }
}
