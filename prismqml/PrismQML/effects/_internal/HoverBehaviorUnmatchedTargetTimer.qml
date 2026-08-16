// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// HoverBehaviorUnmatchedTargetTimer - Clear an unmatched target transition 清理未配对的目标过渡
Timer {
    id: unmatchedTargetTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "hoverBehaviorUnmatchedTargetTimer"
    interval: Enums.duration.none
    repeat: false
    onTriggered: host._awaitingActiveAfterTarget = false
}
