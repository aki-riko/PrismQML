// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ChatMessageSlotMeasurementTimer - Cache a loaded bubble measurement
// ChatMessageSlotMeasurementTimer - 缓存已加载气泡的测量高度
Timer {
    id: measurementTimer

    // ==================== Required Props 必需属性 ====================
    required property var targetSlot
    required property var host

    objectName: "chatMessageSlotMeasurementTimer"
    interval: 0
    repeat: false
    onTriggered: {
        if (targetSlot.item && host) {
            host._cacheSlotHeight(targetSlot, targetSlot.item.implicitHeight)
        }
    }
}
