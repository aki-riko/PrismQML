// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ViewportInitTimer - Initialize viewport tracking after layout 布局完成后初始化视口跟踪
Timer {
    id: initTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "viewportInitTimer"
    interval: 50
    repeat: false
    onTriggered: host._init()
}
