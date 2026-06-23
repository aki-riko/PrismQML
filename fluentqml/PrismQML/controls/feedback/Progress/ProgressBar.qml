// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: Enums.isNeobrutalism ? Enums.neo.muted : trackColor
        // neo: 轨道加黑边显形
        border.width: Enums.isNeobrutalism ? Enums.border.medium : 0
        border.color: Enums.isNeobrutalism ? Enums.stateColor.border : Enums.transparent
    }
    
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width * position
        radius: height / 2
        color: progressColor
        visible: !indeterminate
        Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
    }
    
    // Indeterminate progress 不确定进度(单块加速穿梭)
    IndeterminateBarImpl {
        anchors.fill: parent
        visible: control.indeterminate
        color: control.progressColor
        radius: height / 2
        running: control.indeterminate && control.visible
    }
}
