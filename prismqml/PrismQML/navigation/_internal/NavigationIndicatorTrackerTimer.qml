// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// NavigationIndicatorTrackerTimer - Track the indicator on every presented frame
// NavigationIndicatorTrackerTimer - 每个实际呈现帧跟踪指示器位置
FrameAnimation {
    id: indicatorTracker

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var indicator

    // ==================== Internal Props 内部属性 ====================
    property bool _scrolling: false

    running: _scrolling
    onTriggered: {
        if (!indicator.running) {
            host._updateIndicatorPositionRealtime()
        }
    }
}
