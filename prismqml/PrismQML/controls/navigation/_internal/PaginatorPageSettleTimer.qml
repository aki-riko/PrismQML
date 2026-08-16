// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// PaginatorPageSettleTimer - Settle the loaded page window after sliding
// PaginatorPageSettleTimer - 滑动结束后收敛已加载页码窗口
Timer {
    id: pageSettleTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var slideAnimation

    objectName: "paginatorPageSettleTimer"
    interval: 0
    repeat: false
    onTriggered: {
        if (!slideAnimation.running) host._settleLoadedPages()
    }
}
