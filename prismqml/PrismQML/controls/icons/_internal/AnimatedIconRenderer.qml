// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// AnimatedIconRenderer - State transition visual tree 状态过渡视觉树
// Owns the cross fade layers and the state driven transform so the public entry
// stays declarative. 持有交叉淡入层与状态驱动变换，使公开入口保持声明式。
Item {
    id: renderer

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Readonly State 只读状态 ====================
    readonly property bool transitioning: fadeIn.running

    // ==================== Internal Props 内部属性 ====================
    property string _lastIcon: ""

    // ==================== Signals 信号 ====================
    signal transitionFinished()

    // ==================== Public Methods 公开方法 ====================
    // Snap a running transition to its end state 立即结束正在播放的过渡
    function finishTransition() {
        fadeIn.stop()
        fadeOut.stop()
        incomingIcon.opacity = Enums.opacityLevel.visible
        outgoingIcon.opacity = Enums.opacityLevel.invisible
    }

    // ==================== Internal Methods 内部方法 ====================
    // Cross fade whenever the resolved artwork changes 图形变化时执行交叉淡入
    function _applyIconChange() {
        var nextIcon = host.currentIcon
        if (nextIcon === _lastIcon) {
            return
        }
        outgoingIcon.icon = _lastIcon
        incomingIcon.icon = nextIcon
        _lastIcon = nextIcon
        if (!host.playing || host.duration <= Enums.duration.none) {
            finishTransition()
            return
        }
        incomingIcon.opacity = Enums.opacityLevel.invisible
        outgoingIcon.opacity = Enums.opacityLevel.visible
        fadeIn.restart()
        fadeOut.restart()
    }

    // ==================== Size 尺寸 ====================
    anchors.fill: parent
    scale: host.stateScale
    opacity: host.stateOpacity

    Component.onCompleted: {
        incomingIcon.icon = host.currentIcon
        _lastIcon = host.currentIcon
    }

    Behavior on scale {
        enabled: renderer.host.playing
        NumberAnimation { duration: renderer.host.duration; easing.type: Easing.OutCubic }
    }

    Behavior on opacity {
        enabled: renderer.host.playing
        NumberAnimation { duration: renderer.host.duration; easing.type: Easing.OutCubic }
    }

    // ==================== Content 内容 ====================
    // Outgoing layer keeps the previous artwork while fading out 出场层保留上一图形并淡出
    Icon {
        id: outgoingIcon
        anchors.fill: parent
        iconSize: renderer.host.iconSize
        color: renderer.host.color
        themeAware: renderer.host.themeAware
        opacity: Enums.opacityLevel.invisible
    }

    // Incoming layer paints the current artwork 入场层绘制当前图形
    Icon {
        id: incomingIcon
        anchors.fill: parent
        iconSize: renderer.host.iconSize
        color: renderer.host.color
        themeAware: renderer.host.themeAware
        opacity: Enums.opacityLevel.visible
    }

    NumberAnimation {
        id: fadeIn
        target: incomingIcon
        property: "opacity"
        from: Enums.opacityLevel.invisible
        to: Enums.opacityLevel.visible
        duration: renderer.host.duration
        easing.type: Easing.OutCubic
        onFinished: renderer.transitionFinished()
    }

    NumberAnimation {
        id: fadeOut
        target: outgoingIcon
        property: "opacity"
        from: Enums.opacityLevel.visible
        to: Enums.opacityLevel.invisible
        duration: renderer.host.duration
        easing.type: Easing.OutCubic
    }

    Connections {
        function onCurrentIconChanged() {
            renderer._applyIconChange()
        }

        target: renderer.host
    }
}
