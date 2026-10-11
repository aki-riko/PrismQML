// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// StepperTrack - Showcase connector for the stepper 步骤进度条炫技连接线
// Draws the faded base rail, the growing progress rail, a looping highlight band
// and a dot trail flowing towards the pending end. Every layer animates plain
// geometry or colour properties, so the render thread owns the motion and the
// main thread only rebuilds the scene when the step actually changes.
// 绘制两端淡出的底轨、生长的进度轨、循环流光带与流向未完成端的点阵。
// 所有图层只动几何与颜色属性，动画由渲染线程驱动，主线程仅在步骤真正变化时更新场景。
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
    // Fade both rail ends so the connector reads as light instead of a hard rule
    // 两端淡出，让连接线读起来是光而不是硬直线
    readonly property real _railEdgeStop: 0.04
    readonly property real _sweepWidth: Math.max(thickness * 6, lineWidth * 0.18)
    readonly property real _sweepBandHeight: Math.max(thickness * 3, Enums.spacing.xs)
    readonly property real _flowDotSize: Math.max(thickness * 2.5, Enums.spacing.xs)
    readonly property real _flowGap: _flowDotSize * 4
    readonly property int _flowDotCount: 4

    // ==================== Content 内容 ====================
    // Base rail 底轨
    Rectangle {
        id: rail

        x: root.lineStartX
        y: (root.height - root.thickness) / 2
        width: root.lineWidth
        height: root.thickness
        visible: root.lineWidth > 0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Enums.transparent }
            GradientStop { position: root._railEdgeStop; color: root.railColor }
            GradientStop { position: 1.0 - root._railEdgeStop; color: root.railColor }
            GradientStop { position: 1.0; color: Enums.transparent }
        }
    }

    // Progress rail 进度轨
    Rectangle {
        id: progressRail

        // Elastic overshoot shared by the growth behaviour. Kept small: a larger
        // overshoot runs the rail past the next indicator and reads as a glitch.
        // 生长动画共用的弹性过冲。保持小值：过冲过大会让进度轨越过下一个指示器，读起来像故障。
        readonly property real _growOvershoot: 1.08

        x: root.lineStartX
        y: (root.height - root.thickness) / 2
        width: root._activeWidth
        height: root.thickness
        visible: root.lineWidth > 0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: root.progressColor }
            GradientStop { position: 1.0; color: root.highlightColor }
        }

        Behavior on width {
            NumberAnimation {
                duration: root.growDuration
                easing.type: Easing.OutBack
                easing.overshoot: progressRail._growOvershoot
            }
        }
    }

    // Highlight sweep inside the progress rail 进度轨内的流光带
    Item {
        id: sweepClip

        x: root.lineStartX
        y: (root.height - root._sweepBandHeight) / 2
        width: root._activeWidth
        height: root._sweepBandHeight
        visible: root.animated && root._activeWidth > 0
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

    // Dot trail flowing towards the pending end 流向未完成端的点阵
    Item {
        id: flowClip

        x: root.lineStartX + root._activeWidth
        y: (root.height - root._flowDotSize) / 2
        width: root._pendingWidth
        height: root._flowDotSize
        visible: root.animated && root._pendingWidth > root._flowGap
        clip: true

        Item {
            id: flowTrail

            width: root._flowGap * root._flowDotCount
            height: flowClip.height

            NumberAnimation on x {
                running: flowClip.visible
                loops: Animation.Infinite
                from: -root._flowGap
                to: 0
                duration: root.flowDuration
                easing.type: Easing.Linear
            }

            Repeater {
                model: root._flowDotCount

                Rectangle {
                    x: index * root._flowGap
                    y: 0
                    width: root._flowDotSize
                    height: root._flowDotSize
                    radius: width / 2
                    color: root.progressColor
                    opacity: Enums.opacityLevel.light
                }
            }
        }
    }
}
