// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ToastAutoCloseTimer - Close an incomplete Toast after its duration
// ToastAutoCloseTimer - 在普通 Toast 持续时间结束后关闭
Timer {
    id: hideTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "toastHideTimer"
    interval: host.duration
    running: host.visible && host.duration > 0 && !host._isProgressMode
    onTriggered: host.hide()
}
