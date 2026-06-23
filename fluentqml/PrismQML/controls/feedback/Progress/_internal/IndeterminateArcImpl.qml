// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Shapes
import "../../../.."

// IndeterminateArcImpl - Fluent 伸缩弧脉动 spinner 不确定进度环(自研)
// 整段弧持续顺时针旋转, 同时弧长在 minSweep <-> maxSweep 间呼吸式伸缩。
// 基于 QtQuick.Shapes (GPU 加速 + 抗锯齿), 替代 Material BusyIndicator。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property color color: Enums.accentColor
    property int strokeWidth: Enums.border.normal
    property bool running: true
    // 可选底环 track (默认不画, 由上层决定) Optional track ring
    property color trackColor: Enums.transparent
    property bool showTrack: trackColor.a > 0

    implicitWidth: Enums.controlSize.indeterminateRingSize
    implicitHeight: Enums.controlSize.indeterminateRingSize

    // ==================== Animation State 动画状态 ====================
    // baseRotation: 整体旋转角 (0->360 匀速循环) overall spin
    // sweepLen: 当前弧长 (角度) current arc length, 呼吸伸缩
    // spinDuration: 旋转/伸缩周期, 越小越快 (可被上层覆盖) spin & pulse period, smaller = faster
    property int spinDuration: 800
    readonly property real _minSweep: 25    // 最短弧 shortest arc
    readonly property real _maxSweep: 160   // 最长弧 ~44% (不到半圈, 不显冗长) longest arc
    property real baseRotation: 0
    property real sweepLen: _minSweep

    readonly property real _cx: width / 2
    readonly property real _cy: height / 2
    readonly property real _radius: Math.min(_cx, _cy) - strokeWidth / 2

    // ==================== Public Methods 公共方法 ====================
    function start() { control.running = true }
    function stop() { control.running = false }

    // ==================== Track Ring 底环 (可选) ====================
    Shape {
        anchors.fill: parent
        visible: control.showTrack
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: control.strokeWidth
            strokeColor: control.trackColor
            fillColor: Enums.transparent
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: control._cx; centerY: control._cy
                radiusX: control._radius; radiusY: control._radius
                startAngle: 0; sweepAngle: 360
            }
        }
    }

    // ==================== Spinning Arc 旋转伸缩弧 ====================
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: control.strokeWidth
            strokeColor: control.color
            fillColor: Enums.transparent
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: control._cx; centerY: control._cy
                radiusX: control._radius; radiusY: control._radius
                // 收缩锚定尾端: 头部随 sweepLen 增减前后探动, 避免突跳
                // anchor tail; head leads forward as arc grows
                startAngle: control.baseRotation - (control.sweepLen - control._minSweep)
                sweepAngle: control.sweepLen
            }
        }
    }

    // ==================== Spin Animation 匀速旋转 ====================
    NumberAnimation on baseRotation {
        running: control.running
        from: 0; to: 360
        duration: control.spinDuration
        loops: Animation.Infinite
    }

    // ==================== Pulse Animation 呼吸伸缩 ====================
    SequentialAnimation on sweepLen {
        running: control.running
        loops: Animation.Infinite
        NumberAnimation {
            from: control._minSweep; to: control._maxSweep
            duration: control.spinDuration  // 伸长
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            from: control._maxSweep; to: control._minSweep
            duration: control.spinDuration  // 收缩
            easing.type: Easing.InOutSine
        }
    }
}
