// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// DesktopNotificationAutoCloseTimer - Close a desktop notification after its duration
// DesktopNotificationAutoCloseTimer - 持续时间结束后关闭桌面通知
Timer {
    id: autoCloseTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "desktopNotificationAutoCloseTimer"
    interval: host.duration
    onTriggered: host.hide()
}
