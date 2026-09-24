// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NavigationIndicatorInitTimer - Initialize the indicator after layout settles
// NavigationIndicatorInitTimer - 布局稳定后初始化指示器
Timer {
    id: initTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    // Retry window for asynchronously incubated delegates. 异步委托的重试窗口。
    property bool _retrying: false
    property real _retryDeadline: 0

    function armInitialization() {
        _retrying = false
        _retryDeadline = 0
        restart()
    }

    // Initialize on the next event-loop turn so the first settled frame already
    // carries the selected indicator after the delegate geometry is available.
    // 在下一轮事件循环初始化，让委托几何可用后的首个稳定帧就带上选中指示器。
    interval: _retrying ? Enums.duration.slow : Enums.duration.none
    onTriggered: {
        var ready = host._initIndicatorPosition()
        if (ready) {
            _retrying = false
            _retryDeadline = 0
            return
        }
        if (_retryDeadline === 0)
            _retryDeadline = Date.now() + Enums.duration.notification
        _retrying = Date.now() < _retryDeadline
        if (_retrying) restart()
    }
}
