// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NavigationIndicatorScrollStopTimer - Stop indicator tracking after scrolling
// NavigationIndicatorScrollStopTimer - 滚动结束后停止指示器跟踪
Timer {
    id: scrollStopTimer

    // ==================== Required Props 必需属性 ====================
    required property var tracker

    interval: Enums.duration.fast
    onTriggered: tracker._scrolling = false
}
