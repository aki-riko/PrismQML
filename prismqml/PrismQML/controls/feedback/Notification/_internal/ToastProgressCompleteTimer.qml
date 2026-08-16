// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ToastProgressCompleteTimer - Close a completed progress Toast
// ToastProgressCompleteTimer - 关闭已完成进度的 Toast
Timer {
    id: completeTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "toastCompleteTimer"
    running: host._progressComplete && host.visible
    interval: host.completeDuration
    onTriggered: host.hide()
}
