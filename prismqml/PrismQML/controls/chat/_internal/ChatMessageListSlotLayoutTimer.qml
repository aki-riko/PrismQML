// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ChatMessageListSlotLayoutTimer - Lay out loaded message slots once
// ChatMessageListSlotLayoutTimer - 一次性布局已加载的消息占位项
Timer {
    id: layoutTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "chatMessageListSlotLayoutTimer"
    interval: 0
    repeat: false
    onTriggered: {
        host._layoutPending = false
        var slotCount = host.messageRepeater.count
        var layoutStart = Math.max(0, Math.min(slotCount, host._layoutStartIndex))
        host._layoutStartIndex = -1
        var nextY = 0
        if (layoutStart > 0) {
            var previousSlot = host.messageRepeater.itemAt(layoutStart - 1)
            if (previousSlot && previousSlot._layoutReady) {
                nextY = previousSlot.y + previousSlot.height + Enums.spacing.xs
            } else {
                layoutStart = 0
            }
        }
        host._lastLayoutStartIndex = layoutStart
        for (var i = layoutStart; i < slotCount; i++) {
            var slot = host.messageRepeater.itemAt(i)
            if (!slot) continue
            slot.y = nextY
            nextY += slot.height
            if (i + 1 < slotCount) nextY += Enums.spacing.xs
            if (!slot._layoutReady) slot._layoutReady = true
        }
        host.messageColumn.height = nextY
        host._scheduleLoadRangeUpdate()
        if (host._followBottom) {
            host._pendingAnchorDelta = 0
            host._scheduleScrollToBottom()
        } else if (Math.abs(host._pendingAnchorDelta)
                >= host._heightChangeTolerance) {
            var anchorDelta = host._pendingAnchorDelta
            host._pendingAnchorDelta = 0
            host._setContentY(host.messageViewport.contentY + anchorDelta, false)
        }
    }
}
