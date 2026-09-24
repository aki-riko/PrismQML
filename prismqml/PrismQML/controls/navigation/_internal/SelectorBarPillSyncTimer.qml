// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SelectorBarPillSyncTimer - Settle the selected-cell geometry after delegate rebuilds
// SelectorBarPillSyncTimer - 委托重建后稳定选中单元几何
// A Repeater can briefly report no delegate for a valid index, so the target is only
// accepted once two consecutive ticks agree on the same cell geometry.
// Repeater 在合法索引上可能短暂没有委托, 因此只有连续两次 tick 得到同一几何才接受目标。
Timer {
    id: pillSyncTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var itemRepeater

    // ==================== Internal Props 内部属性 ====================
    property string candidate: ""

    // ==================== Public Methods 公开方法 ====================
    function schedule(shouldAnimate) {
        if (shouldAnimate) {
            stop()
            candidate = ""
            host._updateSlidePosition(true)
            return
        }
        candidate = ""
        restart()
    }

    objectName: "selectorBarPillSyncTimer"
    interval: Enums.duration.tick
    onTriggered: {
        var item = itemRepeater.itemAt(host.currentIndex)
        if (!item || typeof item.x !== "number") {
            // A valid model may still be waiting for its delegate 合法模型可能仍在等待委托
            if (host.currentIndex >= 0 && host.currentIndex < host._safeItems.length) {
                restart()
                return
            }
            candidate = ""
            host._updateSlidePosition(false)
            return
        }

        var next = item.x + ":" + item.y + ":" + item.width + ":" + item.height
        if (candidate !== next) {
            candidate = next
            restart()
            return
        }

        candidate = ""
        host._updateSlidePosition(false)
    }
}
