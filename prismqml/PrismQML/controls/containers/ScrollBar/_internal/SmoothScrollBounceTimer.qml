// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollBounceTimer - On-demand axis bounce timer 按需轴向回弹计时器
// Keeps timer completion coupled to the owning scroll helper.
// 保持计时完成与所属平滑滚动宿主的生命周期绑定。
Timer {
    id: bounceTimer

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper
    required property bool verticalAxis

    // ==================== Size 尺寸 ====================
    interval: Enums.duration.fast

    // ==================== Content 内容 ====================
    onTriggered: {
        if (verticalAxis) scrollHelper._bounceBackV()
        else scrollHelper._bounceBackH()
        scrollHelper._releaseBounceTimer(verticalAxis, bounceTimer)
    }
}
