// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// TeachingTip - Teaching tip anchor position enums 教学提示锚点位置枚举
// Grouped by primary direction with its two corner variants 按主方向+其两个细分分组
QtObject {
    readonly property int anchor_none: 0          // No anchor 无锚点(默认)
    readonly property int anchor_top: 1           // Top center 顶部中心
    readonly property int anchor_top_left: 2       // Top left 顶部左侧
    readonly property int anchor_top_right: 3      // Top right 顶部右侧
    readonly property int anchor_bottom: 4        // Bottom center 底部中心
    readonly property int anchor_bottom_left: 5    // Bottom left 底部左侧
    readonly property int anchor_bottom_right: 6   // Bottom right 底部右侧
    readonly property int anchor_left: 7          // Left center 左侧中心
    readonly property int anchor_left_top: 8       // Left top 左侧顶部
    readonly property int anchor_left_bottom: 9    // Left bottom 左侧底部
    readonly property int anchor_right: 10        // Right center 右侧中心
    readonly property int anchor_right_top: 11     // Right top 右侧顶部
    readonly property int anchor_right_bottom: 12  // Right bottom 右侧底部
}
