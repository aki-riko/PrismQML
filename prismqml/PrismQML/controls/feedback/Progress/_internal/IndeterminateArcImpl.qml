// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    property int style: Enums.progress.indeterminate_style_pulse
    property real fixedArcSweep: Enums.progressRingMetrics.fixedArcSweep
    property real dotSize: Enums.progressRingMetrics.orbitDotSize
    property real dotRadius: Enums.progressRingMetrics.orbitDotRadius
    property real dotTopMargin: Enums.progressRingMetrics.orbitDotTopMargin
    // Optional track ring (drawn here only for orbit-dot style) 可选底环（仅绕圈圆点模式在此绘制）
    property color trackColor: Enums.transparent
    property bool showTrack: trackColor.a > 0

    // Animation state 动画状态
    // sweepLen: 当前弧长 (角度) current arc length, 呼吸伸缩
    // spinDuration: 旋转/伸缩周期, 越小越快 (可被上层覆盖) spin & pulse period, smaller = faster
    property int spinDuration: Enums.progressRingMetrics.spinDuration
    readonly property real _minSweep: 25    // 最短弧 shortest arc
    readonly property real _maxSweep: 160   // 最长弧 ~44% (不到半圈, 不显冗长) longest arc
    property real sweepLen: _minSweep

    readonly property real _cx: width / 2
    readonly property real _cy: height / 2
    readonly property real _radius: Math.min(_cx, _cy) - strokeWidth / 2
    readonly property bool _isPulseStyle: style === Enums.progress.indeterminate_style_pulse
    readonly property bool _isFixedArcStyle: style === Enums.progress.indeterminate_style_fixed_arc
    readonly property bool _isOrbitDotStyle: style === Enums.progress.indeterminate_style_orbit_dot

    // ==================== Public Methods 公开方法 ====================
    function start() { control.running = true }
    function stop() { control.running = false }

    implicitWidth: Enums.controlSize.indeterminateRingSize
    implicitHeight: Enums.controlSize.indeterminateRingSize

    // ==================== Content 内容 ====================
    Loader {
        id: spinningArcLoader

        anchors.fill: parent
        active: control._isPulseStyle || control._isFixedArcStyle
        sourceComponent: spinningArcComponent
    }

    Loader {
        id: orbitingDotLoader

        anchors.fill: parent
        active: control._isOrbitDotStyle
        sourceComponent: orbitingDotComponent
    }

    Component {
        id: spinningArcComponent

        // Spinning arc 旋转伸缩弧
        Shape {
            id: spinningArc

            objectName: "progressRingSpinningArc"
            preferredRendererType: Shape.CurveRenderer

            // Keep spinning on the render thread while page creation blocks the GUI
            // thread. 页面同步创建阻塞 GUI 线程时仍由渲染线程保持旋转。
            RotationAnimator on rotation {
                running: control.running
                from: 0
                to: 360
                duration: control.spinDuration
                loops: Animation.Infinite
            }

            ShapePath {
                strokeWidth: control.strokeWidth
                strokeColor: control.color
                fillColor: Enums.transparent
                capStyle: ShapePath.RoundCap
                PathAngleArc {
                    centerX: control._cx; centerY: control._cy
                    radiusX: control._radius; radiusY: control._radius
                    // Shrink around the tail anchor. 收缩时保持尾端锚定。
                    startAngle: control._isFixedArcStyle ?
                                    -control.fixedArcSweep :
                                    -(control.sweepLen - control._minSweep)
                    sweepAngle: control._isFixedArcStyle ? control.fixedArcSweep : control.sweepLen
                }
            }
        }
    }

    Component {
        id: orbitingDotComponent

        // Legacy splash orbiting dot, now render-thread driven 原开屏绕圈圆点，现由渲染线程驱动
        Item {
            id: orbitingDot

            objectName: "progressRingOrbitingDot"

            // Legacy splash track 原开屏底环
            Rectangle {
                anchors.fill: parent
                visible: control.showTrack
                radius: width / 2
                color: Enums.transparent
                border.width: control.strokeWidth
                border.color: control.trackColor
            }

            RotationAnimator on rotation {
                running: control.running
                from: 0
                to: 360
                duration: control.spinDuration
                loops: Animation.Infinite
            }

            Rectangle {
                width: control.dotSize
                height: control.dotSize
                radius: control.dotRadius
                color: control.color
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: control.dotTopMargin
            }
        }
    }

    // Pulse animation 呼吸伸缩
    SequentialAnimation on sweepLen {
        running: control.running && control._isPulseStyle
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
