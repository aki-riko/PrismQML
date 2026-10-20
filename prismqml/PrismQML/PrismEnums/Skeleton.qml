// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Skeleton - Skeleton shape and block enums 骨架屏形状与块类型枚举
QtObject {
    readonly property int shape_rect: 0         // Rectangle 矩形
    readonly property int shape_circle: 1       // Circle 圆形
    readonly property int shape_rounded: 2      // Rounded rectangle 圆角矩形

    // Declared skeleton block types 声明式骨架块类型
    readonly property int block_title: 0            // Page title 大标题
    readonly property int block_subtitle: 1         // Section heading 分节标题
    readonly property int block_text: 2             // Single text line 单行文本
    readonly property int block_textLines: 3        // Paragraph of text lines 多行文本
    readonly property int block_card: 4             // Card container 卡片容器
    readonly property int block_buttonRow: 5        // Row of buttons 按钮行
    readonly property int block_button: 6           // Single button 单个按钮
    readonly property int block_icon: 7             // Square icon 方形图标
    readonly property int block_avatar: 8           // Round avatar 圆形头像
    readonly property int block_image: 9            // Image block 图片块
    readonly property int block_list: 10            // List container 列表容器
    readonly property int block_listItem: 11        // Single list row 单条列表项
    readonly property int block_input: 12           // Text input 输入框
    readonly property int block_tabs: 13            // Tab strip 标签栏
    readonly property int block_divider: 14         // Thin divider line 细分隔线
    readonly property int block_chart: 15           // Chart area 图表区域
    readonly property int block_carousel: 16        // Horizontal carousel 横向轮播
    readonly property int block_table: 17           // Table with columns 表格
}
