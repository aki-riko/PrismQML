// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TooltipFollowAnchorTimer - Follow a moving anchor on each presented frame 每个实际呈现帧跟随移动锚点
FrameAnimation {
    id: followTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var nativeHost

    objectName: "tooltipFollowAnchorTimer"
    running: host.followAnchor && nativeHost.windowVisible
    onTriggered: host._reposition()
}
