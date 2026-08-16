// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ChatMessageListScrollToBottomTimer - Coalesce one deferred bottom scroll
// ChatMessageListScrollToBottomTimer - 合并一次延迟滚底操作
Timer {
    id: scrollTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "chatMessageListScrollToBottomTimer"
    interval: 0
    repeat: false
    onTriggered: {
        host._scrollPending = false
        if (host._followBottom) host._scrollToBottom()
    }
}
