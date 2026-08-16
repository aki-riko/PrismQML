// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// ToggleNavigationIndicatorTrackerTimer - Track the toggle indicator while scrolling
// ToggleNavigationIndicatorTrackerTimer - 滚动期间跟踪切换栏指示器
Timer {
    id: indicatorTracker

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Internal Props 内部属性 ====================
    property bool _scrolling: false

    interval: Enums.duration.tick
    repeat: true
    running: _scrolling
    onTriggered: host._updateIndicator(false)
}
