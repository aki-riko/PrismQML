// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// IndeterminateBarImpl - Fluent 单块加速穿梭的不确定进度条(自研)
// 一个宽约 40% 的亮块从左进入 -> ease-in-out 加速穿过 -> 从右滑出, 循环。
// 纯 Rectangle + 动画, 替代 Material ProgressBar indeterminate。
// 只负责亮块 + clip; 底轨(track)由上层绘制(上层多已有 track Rectangle)。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property color color: Enums.accentColor
    property bool running: true
    property real radius: height / 2
    // 亮块宽度占比 indicator width ratio
    property real indicatorRatio: 0.4
    // 可选底轨 (默认不画) optional track
    property color trackColor: Enums.transparent
    property bool showTrack: trackColor.a > 0

    implicitWidth: Enums.controlSize.inputDefaultWidth
    implicitHeight: Enums.controlSize.progressBarHeight
    clip: true

    // ==================== Track 底轨 (可选) ====================
    Rectangle {
        anchors.fill: parent
        radius: control.radius
        color: control.trackColor
        visible: control.showTrack
    }

    // ==================== Moving Indicator 穿梭亮块 ====================
    Rectangle {
        id: indicator
        width: parent.width * control.indicatorRatio
        height: parent.height
        radius: control.radius
        color: control.color
        // x: -width(完全在左侧外) -> parent.width(完全滑出右侧)
        x: -width

        SequentialAnimation on x {
            running: control.running
            loops: Animation.Infinite
            NumberAnimation {
                from: -indicator.width
                to: control.width
                duration: Enums.duration.progressLoop  // 2000ms 单次穿梭
                easing.type: Easing.InOutQuad  // 首尾缓动, 中段最快
            }
        }
    }
}
