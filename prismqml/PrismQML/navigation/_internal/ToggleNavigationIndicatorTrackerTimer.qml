// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ToggleNavigationIndicatorTrackerTimer - Track the toggle indicator on presented frames
// ToggleNavigationIndicatorTrackerTimer - 每个实际呈现帧跟踪切换栏指示器
FrameAnimation {
    id: indicatorTracker

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Internal Props 内部属性 ====================
    property bool _scrolling: false

    running: _scrolling
    onTriggered: host._updateIndicator(false)
}
