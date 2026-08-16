// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../"

// AutoUpdaterFeedbackTimer - Dismiss bounded AutoUpdater feedback
// AutoUpdaterFeedbackTimer - 到期后关闭有时限的自动更新反馈
Timer {
    id: feedbackTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "autoUpdaterFeedbackTimer"
    interval: host._feedbackDuration
    running: host._feedbackActive
        && host._feedbackDuration > Enums.duration.none
    onTriggered: host._dismissFeedback()
}
