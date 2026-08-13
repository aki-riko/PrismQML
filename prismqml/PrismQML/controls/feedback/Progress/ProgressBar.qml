// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"

// ProgressBar - Based on ProgressCore 进度条基于ProgressCore
ProgressCore {
    id: control
    
    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget via ProgressCore) 内容尺寸（通过ProgressCore继承自Widget）
    contentWidth: Enums.controlSize.inputDefaultWidth
    contentHeight: Enums.controlSize.progressBarHeight
    clip: true

    NeumorphicShadow {
        target: control
        inset: true
        visible: Enums.isNeumorphism
    }
    
    Rectangle {
        anchors.fill: parent
        radius: Enums.isVintageTicket ? Enums.ticket.radius : height / 2
        color: trackColor
        // neo: 轨道加黑边显形
        border.width: Enums.hasOutlinedSurfaces ? Enums.surfaceBorderWidth(Enums.border.thin) : 0
        border.color: Enums.hasOutlinedSurfaces ? Enums.stateColor.border : Enums.transparent
    }
    
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width * position
        radius: Enums.isVintageTicket ? Enums.ticket.radius : height / 2
        color: progressColor
        visible: !indeterminate
        Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
    }
    
    // Indeterminate progress 不确定进度(单块加速穿梭)
    Loader {
        anchors.fill: parent
        active: control.indeterminate
        sourceComponent: IndeterminateBarImpl {
            color: control.progressColor
            radius: Enums.isVintageTicket ? Enums.ticket.radius : height / 2
            running: control.indeterminate && control.visible
        }
    }
}
