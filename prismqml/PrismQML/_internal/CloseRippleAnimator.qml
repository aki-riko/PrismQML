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
    property bool reverse: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: progressAnimation.running

    // ==================== Internal Props 内部属性 ====================
    property NumberAnimation progressAnimation: NumberAnimation {
        target: animator
        property: "progress"
        from: animator.reverse
            ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
        to: animator.reverse
            ? Enums.opacityLevel.invisible : Enums.opacityLevel.visible
        duration: Enums.windowCloseMetrics.rippleDuration
        easing.type: animator.reverse ? Easing.InQuad : Easing.OutQuad
        onFinished: animator.finished()
    }

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function prepare() {
        progressAnimation.stop()
        animator.progress = animator.reverse
            ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
    }

    function startPrepared() {
        progressAnimation.restart()
    }

    function start() {
        animator.prepare()
        animator.startPrepared()
    }

    function stop() {
        progressAnimation.stop()
        animator.progress = Enums.opacityLevel.invisible
    }
}
