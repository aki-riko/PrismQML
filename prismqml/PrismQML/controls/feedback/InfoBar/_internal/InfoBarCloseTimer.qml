// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// InfoBarCloseTimer - Share normal and completion close timing
// InfoBarCloseTimer - 统一普通状态与完成状态的关闭计时
Timer {
    id: closeTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Readonly State 只读状态 ====================
    readonly property bool completeMode: host._completeCloseActive

    objectName: "infoBarCloseTimer"
    running: host._autoCloseActive || host._completeCloseActive
    interval: completeMode ? host.completeDuration : host.duration
    onCompleteModeChanged: {
        if (running && (host._autoCloseActive || host._completeCloseActive)) {
            restart()
        }
    }
    onTriggered: host.hide()
}
