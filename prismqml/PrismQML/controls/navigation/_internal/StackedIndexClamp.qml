// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedIndexClamp - Page index clamping 页面索引收敛
// Keeps the display/current/pending indexes valid whenever the page count
// changes; the host only owns the ready flag and the change wiring.
// 页数变化时保持显示/目标/待切索引合法; 宿主只保留就绪标志与变更接线。
Item {
    id: indexClamp

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Internal Methods 内部方法 ====================
    function clamp() {
        if (host.count <= 0) {
            host._displayIndex = 0
            host.previousIndex = 0
            host._pendingLazySwitchIndex = -1
            if (!host.pageModeConflict && host.currentIndex !== 0) host.currentIndex = 0
            return
        }
        var lastIndex = host.count - 1
        var clampedDisplay = Math.max(0, Math.min(host._displayIndex, lastIndex))
        var clampedCurrent = Math.max(0, Math.min(host.currentIndex, lastIndex))
        if (host._displayIndex !== clampedDisplay) {
            host._displayIndex = clampedDisplay
            host.previousIndex = clampedDisplay
        }
        if (host.currentIndex !== clampedCurrent) host.currentIndex = clampedCurrent
        if (host._pendingLazySwitchIndex > lastIndex) host._pendingLazySwitchIndex = -1
    }

    visible: false
}
