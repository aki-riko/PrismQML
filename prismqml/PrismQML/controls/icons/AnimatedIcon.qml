// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as IconsInternal

// AnimatedIcon - State driven animated icon 状态驱动动效图标
// Fluent parity: the visual reacts to a State change instead of staying static.
// Fluent 对齐：视觉随 State 变化做过渡，而不是停留在静态字形。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string icon: ""                    // Base icon name / text / image path 基础图标名/文本/图片路径
    property string fallbackIcon: ""            // Used when the state icon is empty 状态图标为空时的回退图标
    property var stateIcons: ({})               // Per-state icon overrides keyed by Enums.media.animated_state_* 各状态图标覆盖表
    property int state: Enums.media.animated_state_normal   // Current visual state 当前视觉状态
    property bool playing: true                 // Animate state transitions 状态切换是否播放动画
    property int duration: Enums.duration.medium    // State transition duration 状态过渡时长
    property int iconSize: Enums.iconSize.xxl   // Rendered icon size 渲染图标尺寸
    property alias size: control.iconSize
    property color color: Enums.textColor.primary   // Tinted icon color 图标着色
    property bool themeAware: true              // Tint artwork with color 是否用 color 着色

    // ==================== Readonly State 只读状态 ====================
    readonly property string currentIcon: _resolveStateIcon(state)
    readonly property bool transitioning: renderer.transitioning
    readonly property real stateScale: _scaleForState(state)
    readonly property real stateOpacity: _opacityForState(state)
    readonly property bool hasVisual: currentIcon !== "" || fallbackIcon !== ""
    // ==================== Signals 信号 ====================
    signal transitionFinished()

    // ==================== Public Methods 公开方法 ====================
    // Switch the visual state 切换视觉状态
    function setState(value) {
        if (value === state) {
            return
        }
        state = value
    }

    // Enable animated transitions 启用状态过渡动画
    function play() {
        playing = true
    }

    // Freeze transitions at the current frame 冻结状态过渡动画
    function stop() {
        playing = false
        renderer.finishTransition()
    }

    // Return to the initial state 回到初始状态
    function reset() {
        setState(Enums.media.animated_state_normal)
    }

    // Resolve the icon bound to one state 解析某个状态绑定的图标
    function stateIconFor(value) {
        return _resolveStateIcon(value)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Per-state icon resolution with base icon fallback 状态图标解析（回退到基础图标）
    function _resolveStateIcon(value) {
        if (stateIcons && typeof stateIcons === "object") {
            var mapped = stateIcons[value]
            if (mapped !== undefined && mapped !== null && mapped !== "") {
                return mapped
            }
        }
        if (icon !== "") {
            return icon
        }
        return fallbackIcon
    }

    // Per-state scale token 状态缩放 token
    function _scaleForState(value) {
        switch (value) {
        case Enums.media.animated_state_pointer_over:
            return Enums.media.animated_scale_pointer_over
        case Enums.media.animated_state_pressed:
            return Enums.media.animated_scale_pressed
        case Enums.media.animated_state_disabled:
            return Enums.media.animated_scale_disabled
        default:
            return Enums.media.animated_scale_normal
        }
    }

    // Per-state opacity token 状态透明度 token
    function _opacityForState(value) {
        return value === Enums.media.animated_state_disabled
            ? Enums.opacityLevel.disabled
            : Enums.opacityLevel.visible
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: iconSize
    implicitHeight: iconSize
    width: iconSize
    height: iconSize

    // ==================== Content 内容 ====================
    // Renderer owns the visual tree and the transition animations 渲染器持有视觉树与过渡动画
    IconsInternal.AnimatedIconRenderer {
        id: renderer
        visible: control.hasVisual
        host: control
    }

    Connections {
        function onTransitionFinished() { control.transitionFinished() }

        target: renderer
    }
}
