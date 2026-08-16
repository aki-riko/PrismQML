// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// FlowLayoutLayoutTimer - Perform one deferred full layout
// FlowLayoutLayoutTimer - 一次性执行延迟的完整布局
Timer {
    id: layoutTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "flowLayoutLayoutTimer"
    interval: 0
    repeat: false
    onTriggered: host._performLayout()
}
