// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// StepperHalo - Breathing halo and activation ripple 呼吸光晕与激活涟漪
// Two stacked translucent discs breathe behind the active step, and a single ring
// expands once when the step becomes current. Only the active instance runs its
// loop, so the number of live animations stays constant no matter how many steps
// the stepper holds.
// 两层半透明圆盘在当前步骤背后呼吸，步骤变为当前时另有一圈环扩散一次。
// 只有当前实例运行循环动画，因此活动动画数量与步骤总数无关。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property real diameter
    required property color haloColor
    required property bool animated
    required property int breatheDuration
    required property int rippleDuration

    // ==================== Public Props 公开属性 ====================
    property bool active: false  // Whether this step is the current one 是否为当前步骤

    // ==================== Readonly State 只读状态 ====================
    readonly property real _outerDiameter: diameter * 1.8
    readonly property real _innerDiameter: diameter * 1.35
    readonly property real _outerMinOpacity: Enums.opacityLevel.faint
    readonly property real _outerMaxOpacity: Enums.opacityLevel.faint * 2.2
    readonly property real _innerMinOpacity: Enums.opacityLevel.faint * 1.6
    readonly property real _innerMaxOpacity: Enums.opacityLevel.faint * 3.4
    readonly property real _restOpacity: Enums.opacityLevel.invisible
    readonly property real _rippleBorderWidth: Enums.border.normal
    readonly property real _rippleStartScale: 1.0
    readonly property real _rippleEndScale: 2.1
    readonly property real _rippleStartOpacity: Enums.opacityLevel.medium

    // ==================== Content 内容 ====================
    onActiveChanged: if (root.active && root.animated) rippleAnim.restart()
    Component.onCompleted: if (root.active && root.animated) rippleAnim.restart()

    visible: root.active

    // Outer breathing disc 外层呼吸圆盘
    Rectangle {
        id: glowOuter

        anchors.centerIn: parent
        width: root._outerDiameter
        height: width
        radius: width / 2
        color: root.haloColor
        opacity: root._restOpacity
    }

    // Inner breathing disc 内层呼吸圆盘
    Rectangle {
        id: glowInner

        anchors.centerIn: parent
        width: root._innerDiameter
        height: width
        radius: width / 2
        color: root.haloColor
        opacity: root._restOpacity
    }

    // Activation ripple ring 激活涟漪环
    Rectangle {
        id: rippleRing

        anchors.centerIn: parent
        width: root.diameter
        height: width
        radius: width / 2
        color: Enums.transparent
        border.width: root._rippleBorderWidth
        border.color: root.haloColor
        opacity: root._restOpacity
    }

    SequentialAnimation {
        id: breatheAnim

        running: root.animated && root.active
        loops: Animation.Infinite
        onStopped: {
            glowOuter.opacity = root._restOpacity
            glowInner.opacity = root._restOpacity
        }

        ParallelAnimation {
            NumberAnimation { target: glowOuter; property: "opacity"; from: root._outerMinOpacity; to: root._outerMaxOpacity; duration: root.breatheDuration; easing.type: Easing.InOutSine }
            NumberAnimation { target: glowInner; property: "opacity"; from: root._innerMinOpacity; to: root._innerMaxOpacity; duration: root.breatheDuration; easing.type: Easing.InOutSine }
        }

        ParallelAnimation {
            NumberAnimation { target: glowOuter; property: "opacity"; from: root._outerMaxOpacity; to: root._outerMinOpacity; duration: root.breatheDuration; easing.type: Easing.InOutSine }
            NumberAnimation { target: glowInner; property: "opacity"; from: root._innerMaxOpacity; to: root._innerMinOpacity; duration: root.breatheDuration; easing.type: Easing.InOutSine }
        }
    }

    ParallelAnimation {
        id: rippleAnim

        NumberAnimation { target: rippleRing; property: "scale"; from: root._rippleStartScale; to: root._rippleEndScale; duration: root.rippleDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: rippleRing; property: "opacity"; from: root._rippleStartOpacity; to: Enums.opacityLevel.invisible; duration: root.rippleDuration; easing.type: Easing.OutCubic }
    }
}
