// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window

// WindowCloseFrameWaiter - Wait for post-transition frames before close 关闭前等待退场后帧
Item {
    id: waiter

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow

    // ==================== Internal Props 内部属性 ====================
    property bool waiting: false

    // ==================== Signals 信号 ====================
    signal completed()

    // ==================== Public Methods 公开方法 ====================
    function arm() {
        waiter.cancel()
        waiter.waiting = true
        waiter.targetWindow.requestUpdate()
    }

    function cancel() {
        waiter.waiting = false
    }

    // ==================== Content 内容 ====================
    // Qt emits afterFrameEnd after the requested post-transition render cycle.
    // Qt 在请求的退场后渲染周期结束时发出 afterFrameEnd,无需时间兜底。
    Connections {
        function onAfterFrameEnd() {
            if (!waiter.waiting) return
            waiter.cancel()
            waiter.completed()
        }

        target: waiter.targetWindow
    }

}
