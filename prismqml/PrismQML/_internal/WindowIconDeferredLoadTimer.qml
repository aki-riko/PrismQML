// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowIconDeferredLoadTimer - Commit a deferred icon source
// WindowIconDeferredLoadTimer - 提交延迟加载的图标源
Timer {
    id: deferredLoadTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "windowIconDeferredLoadTimer"
    interval: Enums.window.iconDeferredLoadDelayMs
    repeat: false
    onTriggered: host._deferredLoadReady = true
}
