// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConfirmDialogCountdownTimer - Advance the confirmation safety countdown
// ConfirmDialogCountdownTimer - 推进确认操作安全倒计时
Timer {
    id: countdownTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "confirmDialogCountdownTimer"
    interval: 1000
    repeat: true
    onTriggered: {
        if (host._countdownRemaining > 0) {
            host._countdownRemaining--
            if (host._countdownRemaining === 0) running = false
        }
    }
}
