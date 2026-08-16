// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ButtonCountdownTimer - Tick an active button countdown
// ButtonCountdownTimer - 驱动活动按钮倒计时
Timer {
    id: countdownTimer

    // ==================== Required Props 必需属性 ====================
    required property var button

    // ==================== Size 尺寸 ====================
    interval: Enums.duration.countUp
    repeat: true
    running: button._countdownActive

    // ==================== Content 内容 ====================
    onTriggered: {
        button._countdownRemaining--
        if (button._countdownRemaining <= 0) {
            button._countdownActive = false
            button.countdownFinished()
        }
    }
}
