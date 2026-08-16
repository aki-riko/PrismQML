// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MarqueeStartTimer - Start Marquee animation after layout settles
// MarqueeStartTimer - 布局稳定后启动 Marquee 动画
Timer {
    id: startTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "marqueeStartTimer"
    interval: 100
    repeat: false
    onTriggered: host._tryStartAnimation()
}
