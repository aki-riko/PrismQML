// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsFilledStartupTimer - Defer filled-window core loading
// WindowsFilledStartupTimer - 延迟加载填充式窗口核心界面
Timer {
    id: startupTimer

    // ==================== Required Props 必需属性 ====================
    required property var targetLoader

    objectName: "windowsFilledStartupTimer"
    interval: Enums.window.splitStartupDelayMs
    running: true
    onTriggered: targetLoader.active = true
}
