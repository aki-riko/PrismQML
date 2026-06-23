// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Flow - Flow layout mode enums 流式布局模式枚举
// Only effective when Orient is set to flow 仅当Orient为flow时生效
// Default value: default (compact packing) 默认值：default（紧凑填充）
QtObject {
    id: root
    
    // ==================== Flow Modes 流式模式 ====================
    readonly property int default_: 0     // Compact packing (heightmap algorithm) 紧凑填充（高度图算法）
    readonly property int vertical: 1     // Waterfall (equal width, variable height) 瀑布流（等宽不等高）
    readonly property int horizontal: 2   // Equal height per row 同行等高
}
