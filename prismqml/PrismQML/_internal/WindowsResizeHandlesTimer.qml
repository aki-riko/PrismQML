// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsResizeHandlesTimer - Defer resize-handle creation
// WindowsResizeHandlesTimer - 延迟创建窗口调整大小手柄
Timer {
    id: resizeHandlesTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    interval: Enums.window.resizeHandlesDelayMs
    repeat: false
    onTriggered: host._resizeHandlesReady = true
}
