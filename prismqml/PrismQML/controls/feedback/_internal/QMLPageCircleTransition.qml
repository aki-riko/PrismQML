// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// QMLPageCircleTransition - Single-circle loading-page transition 单圆形加载页过渡
Item {
    id: transition

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: progressAnimation.running
    readonly property real progress: _progress
    readonly property bool revealTarget: _revealTarget

    // ==================== Internal Props 内部属性 ====================
    property real _progress: Enums.opacityLevel.invisible
    property bool _revealTarget: false

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function start(revealTarget) {
        transition.stop()
        transition._revealTarget = revealTarget
        transition._progress = Enums.opacityLevel.invisible
        progressAnimation.restart()
    }

    function stop() {
        progressAnimation.stop()
        transition._progress = Enums.opacityLevel.invisible
    }

    visible: false
    Component.onDestruction: transition.stop()

    NumberAnimation {
        id: progressAnimation

        target: transition
        property: "_progress"
        from: Enums.opacityLevel.invisible
        to: Enums.opacityLevel.visible
        duration: transition._revealTarget
            ? Enums.lazyLoadingTransitionMetrics.revealDuration
            : Enums.lazyLoadingTransitionMetrics.coverDuration
        easing.type: transition._revealTarget ? Easing.OutQuint : Easing.InCubic
        onFinished: transition.finished()
    }
}
