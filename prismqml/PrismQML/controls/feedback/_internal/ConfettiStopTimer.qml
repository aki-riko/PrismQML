// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ConfettiStopTimer - Stop the effect after its configured lifetime
// ConfettiStopTimer - 配置生命周期结束后停止效果
Timer {
    id: stopTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "confettiStopTimer"
    interval: host.duration + Enums.duration.dialog
    running: host.running
    onTriggered: host.running = false
}
