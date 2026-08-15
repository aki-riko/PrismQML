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

    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    height: Enums.controlSize.wheelPickerItemHeight
    color: upArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
    visible: wheelControl.showScrollButtons && wheelControl._hovered
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
        parent: wheelControl
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: Enums.controlSize.wheelPickerItemHeight
        color: downArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
        visible: wheelControl.showScrollButtons && wheelControl._hovered
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
