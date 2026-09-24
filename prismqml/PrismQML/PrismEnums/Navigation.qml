// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Navigation - Navigation pane display modes 导航面板显示模式
// For: NavigationView 适用于
QtObject {
    // No mode set: NavigationView keeps its historical behaviour and isExpanded stays
    // fully caller-owned. 未设置模式: 保持历史行为, isExpanded 仍完全归调用方。
    readonly property int pane_unspecified: 0
    // Pick by the pane's own width 按面板自身宽度自选
    readonly property int pane_auto: 1
    // Expanded sidebar 展开侧边栏
    readonly property int pane_left: 2
    // Compact icon rail 紧凑图标栏
    readonly property int pane_left_compact: 3
    // Collapsed to the menu button; opening reveals the rail in place
    // 折叠到只剩菜单按钮; 打开时就地展开为图标栏
    readonly property int pane_left_minimal: 4
}
