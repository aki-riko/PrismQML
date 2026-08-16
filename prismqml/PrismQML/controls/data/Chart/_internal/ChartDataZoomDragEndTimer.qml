// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ChartDataZoomDragEndTimer - End direct manipulation after slider input idles
// ChartDataZoomDragEndTimer - 滑块输入空闲后结束直接操作状态
Timer {
    id: dragEndTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "chartDataZoomDragEndTimer"
    interval: Enums.duration.slow
    repeat: false
    onTriggered: {
        host._dragging = false
        host.interactiveChanged(false)
    }
}
