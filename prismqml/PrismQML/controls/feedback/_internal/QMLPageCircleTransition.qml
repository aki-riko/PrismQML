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
    // Expansion easing. OutQuint suits small page-switch radii but on a
    // full-window reveal the circle clears the edge in ~40% of the duration,
    // leaving the rest visually static; callers doing full-window reveals can
    // override this. 展开缓动。OutQuint 适合页面切换的小半径, 但全窗口揭幕时
    // 圆在约 40% 时长内就冲出边缘, 其余时间画面无变化; 做全窗口揭幕的调用方
    // 可覆盖此值。
    property int revealEasing: Easing.OutQuint
    // Collapse easing. Progress runs 1 -> 0 and the radius scales linearly with
    // it, so an ease-in curve holds the radius near maximum for most of the
    // duration and then crosses the whole remaining distance in the last few
    // frames. Measured on a real presenting display, InCubic put half the
    // radius in the final 20% of the timeline for both page switch and window
    // exit; InOutQuad spreads the motion evenly instead.
    // 收紧缓动。progress 由 1 走到 0 且半径随之线性缩放, 所以 ease-in 曲线会让
    // 半径在大部分时长里几乎不动, 最后几帧才跨完剩余全部距离。真机实测: InCubic
    // 在页面切换与窗口退场上都把半径的一半压在末尾 20% 时长里; InOutQuad 把运动
    // 均匀铺开。
    property int coverEasing: Easing.InOutQuad

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
        easing.type: transition._collapsing
            ? transition.coverEasing
            : transition.revealEasing
        onFinished: transition.finished()
    }
}
