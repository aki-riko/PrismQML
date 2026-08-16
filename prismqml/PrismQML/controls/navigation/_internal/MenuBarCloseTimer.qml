// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// MenuBarCloseTimer - Release an on-demand menu close timer 按需释放菜单关闭计时器
Timer {
    id: closeTimer

    // ==================== Required Props 必需属性 ====================
    required property Item menuBar
    required property Item menuButton
    required property Item ownerItem

    objectName: "menuBarCloseTimer"
    interval: Enums.duration.fast
    repeat: false
    onTriggered: {
        if (!menuButton.hovered) menuBar.activeIndex = -1
        ownerItem._closeTimer = null
        destroy()
    }
}
