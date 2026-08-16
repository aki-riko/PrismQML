// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TooltipFollowAnchorTimer - Follow a moving anchor while the native host is visible 原生宿主可见时跟随移动锚点
Timer {
    id: followTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var nativeHost

    objectName: "tooltipFollowAnchorTimer"
    interval: 16
    repeat: true
    running: host.followAnchor && nativeHost.windowVisible
    onTriggered: host._reposition()
}
