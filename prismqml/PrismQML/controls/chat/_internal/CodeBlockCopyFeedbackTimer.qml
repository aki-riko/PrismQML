// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// CodeBlockCopyFeedbackTimer - Reset copy feedback after a bounded interval
// CodeBlockCopyFeedbackTimer - 在固定时长后重置复制反馈
Timer {
    id: feedbackTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "codeBlockCopyFeedbackTimer"
    interval: Enums.duration.copyFeedback
    repeat: false
    onTriggered: host._copied = false
}
