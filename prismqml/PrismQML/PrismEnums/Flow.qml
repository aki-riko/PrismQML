// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Flow - Layout layer enums 布局层枚举
// Flow modes are only effective when Orient is set to flow 流式模式仅当Orient为flow时生效
// Default value: default (compact packing) 默认值：default（紧凑填充）
// Pane display modes and pane metrics belong to the layout layer as well
// 面板显示模式与面板度量同样属于布局层
QtObject {
    id: root
    
    // ==================== Public Props 公开属性 ====================
    readonly property int default_: 0     // Compact packing (heightmap algorithm) 紧凑填充（高度图算法）
    readonly property int vertical: 1     // Waterfall (equal width, variable height) 瀑布流（等宽不等高）
    readonly property int horizontal: 2   // Equal height per row 同行等高
    readonly property int sliding_window_min_items: 100 // Adaptive search threshold 自适应搜索阈值

    // SplitView pane display modes 分栏视图面板显示模式
    readonly property int split_display_overlay: 10          // Pane floats over the content 面板浮于内容之上
    readonly property int split_display_inline: 11           // Pane pushes the content 面板挤压内容
    readonly property int split_display_compact_overlay: 12  // Compact rail floats when collapsed 收起时紧凑栏浮于内容之上
    readonly property int split_display_compact_inline: 13   // Compact rail pushes when collapsed 收起时紧凑栏挤压内容
    // SplitView pane metrics (WinUI SplitView defaults) 分栏视图面板度量（WinUI SplitView 默认值）
    readonly property int split_open_pane_length: 320    // Expanded pane extent 展开面板宽度
    readonly property int split_compact_pane_length: 48  // Compact rail extent 紧凑栏宽度
    readonly property int split_pane_minimum_size: 50    // Minimum pane extent while dragging 拖拽时的最小面板宽度
    // Layout layer implicit sizes 布局层隐式尺寸
    readonly property int layout_implicit_width: 200   // Default layout container width 布局容器默认宽度
    readonly property int layout_implicit_height: 200  // Default layout container height 布局容器默认高度
}
