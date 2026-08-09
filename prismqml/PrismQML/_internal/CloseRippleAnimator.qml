// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// CloseRippleAnimator - Shared ripple progress animation 共享涟漪进度动画
QtObject {
    id: animator

    // ==================== Public Props 公开属性 ====================
    property real progress: Enums.opacityLevel.invisible

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: progressAnimation.running

    // ==================== Internal Props 内部属性 ====================
    property NumberAnimation progressAnimation: NumberAnimation {
        target: animator
        property: "progress"
        to: Enums.opacityLevel.visible
        duration: Enums.windowCloseMetrics.rippleDuration
        easing.type: Easing.OutQuad
        onFinished: animator.finished()
    }

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function start() {
        animator.progress = Enums.opacityLevel.invisible
        progressAnimation.restart()
    }

    function stop() {
        progressAnimation.stop()
        animator.progress = Enums.opacityLevel.invisible
    }
}
