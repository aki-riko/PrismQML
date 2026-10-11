// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// StepperHalo - Breathing halo and activation ripple 呼吸光晕与激活涟漪
// Stacked translucent discs approximate a soft radial falloff: a two-ring halo
// shows visible banding, so the glow is built from five progressively fainter
// discs driven by a single breathing factor. Only the active instance runs its
// loop, keeping the live animation count independent of the step count.
// 多层半透明圆盘近似柔和径向衰减：两层光环会出现可见色带，因此光晕由五层
// 逐级变淡的圆盘构成，并只用一个呼吸因子驱动。只有当前实例运行循环动画，
// 活动动画数量与步骤总数无关。
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

    // ==================== Internal Props 内部属性 ====================
    property real _breath: 0  // Shared breathing factor 共享呼吸因子

    // ==================== Readonly State 只读状态 ====================
    readonly property var _haloScales: [1.0, 1.18, 1.38, 1.6, 1.85]
    readonly property real _haloOpacity: Enums.opacityLevel.faint
    readonly property real _haloFalloff: 0.2
    readonly property real _minBreath: 0.55
    readonly property real _maxBreath: 1.0
    readonly property real _restBreath: Enums.opacityLevel.invisible
    readonly property real _rippleBorderWidth: Enums.border.normal
    readonly property real _rippleStartScale: 1.0
    readonly property real _rippleEndScale: 2.3
    readonly property real _rippleStartOpacity: Enums.opacityLevel.light

    // ==================== Content 内容 ====================
    onActiveChanged: if (root.active && root.animated) rippleAnim.restart()
    Component.onCompleted: if (root.active && root.animated) rippleAnim.restart()

    visible: root.active

    // Layered glow 分层光晕
    Repeater {
        model: root._haloScales

        Rectangle {
            anchors.centerIn: parent
            width: root.diameter * modelData
            height: width
            radius: width / 2
            color: root.haloColor
            opacity: root._haloOpacity * root._breath * (1 - index * root._haloFalloff)
        }
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
        opacity: root._restBreath
    }

    SequentialAnimation {
        id: breatheAnim

        running: root.animated && root.active
        loops: Animation.Infinite
        onStopped: root._breath = root._restBreath

        NumberAnimation { target: root; property: "_breath"; from: root._minBreath; to: root._maxBreath; duration: root.breatheDuration; easing.type: Easing.InOutSine }
        NumberAnimation { target: root; property: "_breath"; from: root._maxBreath; to: root._minBreath; duration: root.breatheDuration; easing.type: Easing.InOutSine }
    }

    ParallelAnimation {
        id: rippleAnim

        NumberAnimation { target: rippleRing; property: "scale"; from: root._rippleStartScale; to: root._rippleEndScale; duration: root.rippleDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: rippleRing; property: "opacity"; from: root._rippleStartOpacity; to: Enums.opacityLevel.invisible; duration: root.rippleDuration; easing.type: Easing.OutCubic }
    }
}
