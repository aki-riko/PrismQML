// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SegmentedSlideSyncTimer - Settle selected-segment geometry on the main axis after delegate rebuilds
// SegmentedSlideSyncTimer - 委托重建后沿主轴稳定选中分段几何
Timer {
    id: slideSyncTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property Item segmentRow
    required property var itemRepeater

    // ==================== Internal Props 内部属性 ====================
    property bool candidateReady: false
    property real candidateX: 0
    property real candidateWidth: 0

    // ==================== Public Methods 公开方法 ====================
    function schedule(shouldAnimate) {
        if (shouldAnimate) {
            stop()
            candidateReady = false
            host._updateSlidePosition(true)
            return
        }

        candidateReady = false
        restart()
    }

    objectName: "segmentedControlSlideSyncTimer"
    interval: Enums.duration.tick
    onTriggered: {
        var item = itemRepeater.itemAt(host.currentIndex)
        if (!item || typeof item.x !== "number") {
            // A valid model may briefly have no delegate while Repeater rebuilds
            // Repeater 重建期间，有效模型可能短暂没有对应 delegate
            if (host.currentIndex >= 0 && host.currentIndex < host._safeItems.length) {
                restart()
                return
            }
            candidateReady = false
            host._updateSlidePosition(false)
            return
        }

        var nextCandidateX = host.vertical
            ? segmentRow.y + item.y : segmentRow.x + item.x
        var nextCandidateWidth = host.vertical
            ? (item.height || 0) : (item.width || 0)
        if (!candidateReady
                || candidateX !== nextCandidateX
                || candidateWidth !== nextCandidateWidth) {
            candidateReady = true
            candidateX = nextCandidateX
            candidateWidth = nextCandidateWidth
            restart()
            return
        }

        candidateReady = false
        host._updateSlidePosition(false)
    }
}
