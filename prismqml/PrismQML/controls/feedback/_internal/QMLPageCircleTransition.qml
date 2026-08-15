// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// QMLPageCircleTransition - Real-page circle radius transition 真实页面圆形半径过渡
Item {
    id: transition

    // ==================== Public Props 公开属性 ====================
    property int coverDuration: Enums.lazyLoadingTransitionMetrics.coverDuration
    property int revealDuration: Enums.lazyLoadingTransitionMetrics.revealDuration

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: progressAnimation.running
    readonly property real progress: _progress
    readonly property bool collapsing: _collapsing

    // ==================== Internal Props 内部属性 ====================
    property real _progress: Enums.opacityLevel.invisible
    property bool _collapsing: false

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function prepare(collapsing) {
        progressAnimation.stop()
        transition._collapsing = collapsing
        transition._progress = collapsing
            ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
    }

    function startPrepared() {
        progressAnimation.restart()
    }

    function start(collapsing) {
        transition.prepare(collapsing)
        transition.startPrepared()
    }

    function stop() {
        progressAnimation.stop()
        transition._progress = Enums.opacityLevel.invisible
        transition._collapsing = false
    }

    visible: false
    Component.onDestruction: transition.stop()

    NumberAnimation {
        id: progressAnimation

        target: transition
        property: "_progress"
        from: transition._collapsing
            ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
        to: transition._collapsing
            ? Enums.opacityLevel.invisible : Enums.opacityLevel.visible
        duration: transition._collapsing
            ? transition.coverDuration
            : transition.revealDuration
        easing.type: transition._collapsing ? Easing.InCubic : Easing.OutQuint
        onFinished: transition.finished()
    }
}
