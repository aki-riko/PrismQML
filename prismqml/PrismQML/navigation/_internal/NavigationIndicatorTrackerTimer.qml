// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NavigationIndicatorTrackerTimer - Track indicator position while scrolling
// NavigationIndicatorTrackerTimer - 滚动期间跟踪指示器位置
Timer {
    id: indicatorTracker

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var indicator

    // ==================== Internal Props 内部属性 ====================
    property bool _scrolling: false

    interval: Enums.duration.tick
    repeat: true
    running: _scrolling
    onTriggered: {
        if (!indicator.running) {
            host._updateIndicatorPositionRealtime()
        }
    }
}
