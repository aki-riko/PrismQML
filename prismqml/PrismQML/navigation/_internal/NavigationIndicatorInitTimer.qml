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

    interval: 50
    onTriggered: host._initIndicatorPosition()
}
