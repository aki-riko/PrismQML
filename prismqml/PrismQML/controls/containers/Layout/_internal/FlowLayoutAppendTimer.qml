// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// FlowLayoutAppendTimer - Apply queued tail items once
// FlowLayoutAppendTimer - 一次性应用排队的尾部子项
Timer {
    id: appendTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "flowLayoutAppendTimer"
    interval: 0
    repeat: false
    onTriggered: {
        host._appendLayoutPending = false
        host._appendDefaultItems()
    }
}
