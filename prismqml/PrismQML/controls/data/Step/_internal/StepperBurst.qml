// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// StepperBurst - Completion burst ring and particles 完成迸发光环与粒子
// Pre-built ring and particle pool. Nothing is created at runtime and the whole
// subtree stays hidden until burst() runs, so an idle stepper pays no render cost
// for the celebration layer.
// 预建的光环与粒子池。运行期不创建任何对象，未触发时整棵子树隐藏，
// 因此空闲的步骤条不为庆祝层付出渲染成本。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property real diameter
    required property color ringColor
    required property color particleColor
    required property bool animated
    required property int duration

    // ==================== Public Props 公开属性 ====================
    property int particleCount: 6  // Burst particle count 迸发粒子数量

    // ==================== Internal Props 内部属性 ====================
    property bool _bursting: false  // Burst window state 迸发窗口状态

    // ==================== Readonly State 只读状态 ====================
    readonly property real _particleSize: Math.max(Enums.spacing.xxs,
        diameter * Enums.stepper.particleSizeRatio)
    readonly property real _particleDistance: diameter * Enums.stepper.particleDistanceRatio
    readonly property real _originX: (diameter - _particleSize) / 2
    readonly property real _originY: (diameter - _particleSize) / 2
    readonly property real _ringBorderWidth: Enums.border.normal
    readonly property real _ringStartScale: Enums.stepper.ringStartScale
    readonly property real _ringEndScale: Enums.stepper.ringEndScale
    readonly property real _ringStartOpacity: Enums.opacityLevel.heavy
    readonly property real _particleOpacity: Enums.opacityLevel.strong
    readonly property real _particleEndScale: Enums.stepper.particleEndScale

    // ==================== Public Methods 公开方法 ====================
    // Play one completion burst 播放一次完成迸发
    // The window animation restarts first: its stop handler clears _bursting, so
    // the flag has to be raised after the restart, never before it.
    // 先重启窗口动画：其停止处理会清空 _bursting，因此标志必须在重启之后再置位。
    function burst() {
        if (!root.animated) return
        ringAnim.restart()
        burstWindow.restart()
        root._bursting = true
        for (var slot = 0; slot < particles.count; ++slot) {
            var particle = particles.itemAt(slot)
            if (particle) particle.launch(slot)
        }
    }

    // ==================== Size 尺寸 ====================
    visible: root._bursting
    implicitWidth: root.diameter
    implicitHeight: root.diameter

    // ==================== Content 内容 ====================
    // Expanding ring 扩散光环
    Rectangle {
        id: burstRing

        anchors.centerIn: parent
        width: root.diameter
        height: width
        radius: width / 2
        color: Enums.transparent
        border.width: root._ringBorderWidth
        border.color: root.ringColor
        opacity: Enums.opacityLevel.invisible
        scale: root._ringStartScale
    }

    ParallelAnimation {
        id: ringAnim

        NumberAnimation { target: burstRing; property: "scale"; from: root._ringStartScale; to: root._ringEndScale; duration: root.duration; easing.type: Easing.OutCubic }
        NumberAnimation { target: burstRing; property: "opacity"; from: root._ringStartOpacity; to: Enums.opacityLevel.invisible; duration: root.duration; easing.type: Easing.OutCubic }
    }

    // Particle pool 粒子池
    Repeater {
        id: particles

        model: root.particleCount

        Item {
            id: particleSlot

            // Fly this slot along its own radial direction 让本槽位沿自身径向飞出
            function launch(slot) {
                var angle = Math.PI * 2 / root.particleCount * slot - Math.PI / 2
                flyX.from = 0
                flyX.to = Math.cos(angle) * root._particleDistance
                flyY.from = 0
                flyY.to = Math.sin(angle) * root._particleDistance
                flyAnim.restart()
            }

            x: root._originX
            y: root._originY
            width: root._particleSize
            height: width

            Rectangle {
                id: particleDot

                width: parent.width
                height: parent.height
                radius: width / 2
                color: root.particleColor
                opacity: Enums.opacityLevel.invisible
                visible: opacity > Enums.opacityLevel.invisible

                ParallelAnimation {
                    id: flyAnim

                    NumberAnimation { id: flyX; target: particleDot; property: "x"; duration: root.duration; easing.type: Easing.OutCubic }
                    NumberAnimation { id: flyY; target: particleDot; property: "y"; duration: root.duration; easing.type: Easing.OutCubic }
                    NumberAnimation { target: particleDot; property: "opacity"; from: root._particleOpacity; to: Enums.opacityLevel.invisible; duration: root.duration; easing.type: Easing.OutCubic }
                    NumberAnimation { target: particleDot; property: "scale"; from: Enums.stepper.baseScale; to: root._particleEndScale; duration: root.duration; easing.type: Easing.OutCubic }
                }
            }
        }
    }

    // Burst window: hides the whole subtree again once the celebration ends
    // 迸发窗口：庆祝结束后重新隐藏整棵子树
    SequentialAnimation {
        id: burstWindow

        onStopped: root._bursting = false

        PauseAnimation { duration: root.duration }
    }
}
