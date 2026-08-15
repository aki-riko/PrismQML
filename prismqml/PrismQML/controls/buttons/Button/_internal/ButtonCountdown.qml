// ButtonCountdown - Lazy countdown timer shell 懒加载倒计时器壳
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../../../.."

// ButtonCountdown - Keeps countdown timing out of ButtonCore 将倒计时逻辑从 ButtonCore 中拆出
Loader {
    id: countdownLoader

    // ==================== Required Props 必需属性 ====================
    required property var button

    active: button.feature === Enums.button.feature_countdown
            || button._countdownActive
    sourceComponent: Timer {
        interval: Enums.duration.countUp
        repeat: true
        running: countdownLoader.button._countdownActive
        onTriggered: {
            countdownLoader.button._countdownRemaining--
            if (countdownLoader.button._countdownRemaining <= 0) {
                countdownLoader.button._countdownActive = false
                countdownLoader.button.countdownFinished()
            }
        }
    }
}
