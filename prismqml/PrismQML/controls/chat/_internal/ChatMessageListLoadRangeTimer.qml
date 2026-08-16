// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ChatMessageListLoadRangeTimer - Update the virtualized load range once
// ChatMessageListLoadRangeTimer - 一次性更新虚拟化加载区间
Timer {
    id: rangeTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "chatMessageListLoadRangeTimer"
    interval: 0
    repeat: false
    onTriggered: {
        host._rangeUpdatePending = false
        var count = host.messageRepeater.count
        if (count === 0) {
            host._applyLoadRange(-1, -1)
            return
        }
        var finalSlot = host.messageRepeater.itemAt(count - 1)
        if (!finalSlot || !finalSlot._layoutReady) {
            host._scheduleSlotLayout(0)
            return
        }
        var topY = host.messageViewport.contentY - host._loadMargin
        var bottomY = host.messageViewport.contentY + host.messageViewport.height
            + host._loadMargin
        var firstIndex = host._findFirstLoadIndex(topY)
        var lastIndex = host._findLastLoadIndex(bottomY)
        if (firstIndex > lastIndex) {
            host._applyLoadRange(-1, -1)
            return
        }
        host._applyLoadRange(firstIndex, lastIndex)
    }
}
