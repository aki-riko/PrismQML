// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// MenuSubmenuOpenTimer - Delay submenu opening while the parent action remains hovered
// MenuSubmenuOpenTimer - 父级动作保持悬停时延迟打开子菜单
Timer {
    id: submenuOpenTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Size 尺寸 ====================
    interval: Enums.duration.fast
    repeat: false

    // ==================== Content 内容 ====================
    onTriggered: {
        if (host._pendingSubmenuAction
                && host._pendingSubmenuAction.hovered) {
            host._openSubmenuForAction(
                host._pendingSubmenuAction,
                host._pendingSubmenuComponent,
                host._pendingSubmenuProperties
            )
        }
    }
}
