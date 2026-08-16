// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SpinBoxFeedbackTimer - Clear one spin button feedback state
// SpinBoxFeedbackTimer - 清理一个微调按钮的反馈状态
Timer {
    id: feedbackTimer

    // ==================== Required Props 必需属性 ====================
    required property var spinControl
    required property bool increase

    objectName: increase
        ? "spinBoxIncreaseFeedbackTimer"
        : "spinBoxDecreaseFeedbackTimer"
    interval: Enums.duration.fast
    repeat: false
    onTriggered: {
        var button = increase
            ? spinControl._increaseButton : spinControl._decreaseButton
        if (!button) return
        button.pseudoHovered = false
        button.pseudoPressed = false
    }
}
