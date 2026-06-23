// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// WindowType - Window type enums 窗口类型枚举
QtObject {
    // Window types 窗口类型
    readonly property int type_fluent: 0           // Window - expandable side navigation 展开式侧边导航
    readonly property int type_ms: 1               // Compact side navigation 紧凑侧边导航
    readonly property int type_filled_split: 2     // Filled split navigation 填充分割式导航

    // Window type names for display 窗口类型显示名称
    readonly property var typeNames: [
        "Window",
        "CompactWindow",
        "SplitWindow"
    ]
    
    // Window type descriptions 窗口类型描述
    readonly property var typeDescriptions: [
        "展开式侧边导航",
        "紧凑侧边导航",
        "填充分割式导航"
    ]
    
    // Title bar position 标题栏位置
    readonly property int title_bar_top: 0          // Top - default 顶部（默认）
    readonly property int title_bar_left: 1         // Left panel 左侧面板
}
