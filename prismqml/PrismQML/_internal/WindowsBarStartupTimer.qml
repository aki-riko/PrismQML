// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsBarStartupTimer - Start the navigation-bar content after presentation
// WindowsBarStartupTimer - 窗口首帧呈现后启动导航栏内容
Timer {
    id: startupTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var targetLoader

    objectName: "windowsBarStartupTimer"
    interval: Enums.duration.none
    running: !host._startupContentStarted &&
        (host.lazyLoading || host._startupPresentationReady)

    // ==================== Content 内容 ====================
    onTriggered: {
        host._startupContentStarted = true
        host.profileTime("WindowsBar startupTimer triggered")
        targetLoader.setSource(Qt.resolvedUrl("WindowsBarContent.qml"), {
            "hostWindow": host,
            "contentTopMargin": host.contentTopMargin
        })
        targetLoader.active = true
        host.profileTime("WindowsBar mainLoader.active=true")
    }
}
