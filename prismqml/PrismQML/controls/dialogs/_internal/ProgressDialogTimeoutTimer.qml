// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ProgressDialogTimeoutTimer - Close a progress dialog after its wait limit
// ProgressDialogTimeoutTimer - 超过等待上限后关闭进度对话框
Timer {
    id: timeoutTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "progressDialogTimeoutTimer"
    interval: host.maxWaitingTime
    running: host._isOpen && host.maxWaitingTime > 0
    onTriggered: {
        host.timeout()
        host.close()
    }
}
