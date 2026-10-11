// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// StepperTrack - Showcase connector for the stepper 步骤进度条炫技连接线
// A rounded rail whose thickness matches the indicator scale, a solid progress
// rail, a narrow highlight that sweeps along it and a short-dash trail flowing
// towards the pending end. The sweep is deliberately only a few rail widths long:
// a wide band on a thin rail reads as a smeared wedge instead of light.
// 圆角轨道，粗细与指示器尺度匹配；实色进度轨、沿轨扫过的窄流光，以及流向未完成端的短光条。
// 流光刻意只做几个轨宽长：细轨上的宽光带会读成抹开的楔形色块，而不是光。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property real lineStartX
    required property real lineWidth
    required property real thickness
    required property real progress
    required property color railColor
    required property color progressColor
    required property color highlightColor
    required property bool animated
    required property int growDuration
    required property int sweepDuration
    required property int flowDuration

    // ==================== Readonly State 只读状态 ====================
    readonly property real _activeWidth: Math.max(0, Math.min(1, progress)) * lineWidth
    readonly property real _pendingWidth: Math.max(0, lineWidth - _activeWidth)
    readonly property real _radius: thickness / 2
    readonly property real _sweepWidth: thickness * 4
    // Small, closely spaced dashes read as a flowing dotted rule; a few long bars
    // look like stray capsules stranded on the rail.
    // 细小而密集的短条读作流动的点线；几根长条会像搁在轨道上的孤立胶囊。
    readonly property real _dashWidth: thickness * 1.6
    readonly property real _dashGap: thickness * 5
    readonly property int _dashCount: 4
    readonly property real _dashOpacity: Enums.opacityLevel.secondary

    // ==================== Content 内容 ====================
    // Base rail 底轨
    Rectangle {
        id: rail

        x: root.lineStartX
        y: 0
        width: root.lineWidth
        height: root.thickness
        radius: root._radius
        color: root.railColor
        visible: root.lineWidth > 0
    }

    // Progress rail 进度轨
    Rectangle {
        id: progressRail

        // Elastic overshoot shared by the growth behaviour. Kept small: a larger
        // overshoot runs the rail past the next indicator and reads as a glitch.
        // 生长动画共用的弹性过冲。保持小值：过冲过大会让进度轨越过下一个指示器，读起来像故障。
        readonly property real _growOvershoot: 1.05

        x: root.lineStartX
        y: 0
        width: root._activeWidth
        height: root.thickness
        radius: root._radius
        color: root.progressColor
        visible: root.lineWidth > 0

        Behavior on width {
            NumberAnimation {
                duration: root.growDuration
                easing.type: Easing.OutBack
                easing.overshoot: progressRail._growOvershoot
            }
        }
    }

    // Highlight sweeping along the progress rail 沿进度轨扫过的流光
    Item {
        id: sweepClip

        x: root.lineStartX
        y: 0
        width: root._activeWidth
        height: root.thickness
        visible: root.animated && root._activeWidth > root._sweepWidth
        clip: true

        Rectangle {
            id: sweep

            y: 0
            width: root._sweepWidth
            height: sweepClip.height
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Enums.transparent }
                GradientStop { position: 0.5; color: root.highlightColor }
                GradientStop { position: 1.0; color: Enums.transparent }
            }

            NumberAnimation on x {
                running: sweepClip.visible
                loops: Animation.Infinite
                from: -sweep.width
                to: sweepClip.width
                duration: root.sweepDuration
                easing.type: Easing.InOutSine
            }
        }
    }

    // Short dashes flowing towards the pending end 流向未完成端的短光条
    Item {
        id: flowClip

        x: root.lineStartX + root._activeWidth
        y: 0
        width: root._pendingWidth
        height: root.thickness
        visible: root.animated && root._pendingWidth > root._dashGap
        clip: true

        Item {
            id: flowTrail

            width: root._dashGap * root._dashCount
            height: flowClip.height

            NumberAnimation on x {
                running: flowClip.visible
                loops: Animation.Infinite
                from: -root._dashGap
                to: 0
                duration: root.flowDuration
                easing.type: Easing.Linear
            }

            Repeater {
                model: root._dashCount

                Rectangle {
                    x: index * root._dashGap
                    y: 0
                    width: root._dashWidth
                    height: root.thickness
                    radius: root._radius
                    color: root.progressColor
                    opacity: root._dashOpacity
                }
            }
        }
    }
}
