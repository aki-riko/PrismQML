// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsSplitStartupTimer - Defer split-window core loading
// WindowsSplitStartupTimer - 延迟加载分栏窗口核心界面
Timer {
    id: startupTimer

    // ==================== Required Props 必需属性 ====================
    required property var targetLoader

    objectName: "windowsSplitStartupTimer"
    interval: Enums.window.splitStartupDelayMs
    running: true
    onTriggered: targetLoader.active = true
}
