// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsSkeleton - Skeleton placeholder metrics 骨架屏占位度量
// Static data only; kept in _internal so Metrics.qml stays inside its size gate.
// 仅静态数据; 放在 _internal 以保证 Metrics.qml 留在体积门禁内。
QtObject {
    id: skeleton

    // ==================== Public Props 公开属性 ====================
    readonly property int rectWidth: 200
    readonly property int rectHeight: 16
    readonly property int circleSize: 48
    readonly property real shimmerWidthRatio: 0.5
    readonly property int shimmerDurationMs: 1500
    readonly property int shimmerPauseMs: 500
    readonly property real baseAlphaLight: 0.06
    readonly property real baseAlphaDark: 0.08
    readonly property real shimmerAlphaLight: 0.04
    readonly property real shimmerAlphaDark: 0.12
    // QMLPage skeleton layout 懒加载页面骨架布局
    readonly property int pageHeaderHeight: 24 // Header bar height 标题条高度
    readonly property real pageHeaderWidthRatio: 0.4 // Header width share of the available width 标题条占可用宽度比例
    readonly property int pageRowHeight: 16 // Content row height 内容行高度
    readonly property real pageRowLongRatio: 0.9 // Long row width share 长行宽度比例
    readonly property real pageRowShortRatio: 0.6 // Short row width share 短行宽度比例
    readonly property int pageRowMinCount: 2 // Fewest content rows 最少内容行数
    readonly property int pageRowMaxCount: 16 // Most content rows 最多内容行数
    readonly property int pageCardHeight: 72 // Bottom card height 底部卡片高度
    // Declared skeleton block layout 声明式骨架块布局
    // Every declared block derives its size from these tokens plus the area it is
    // given, so a page declaration describes structure only, never geometry.
    // 每个声明块都按这些令牌加自身可用区域推导尺寸，因此页面声明只描述结构，不含几何。
    readonly property int blockGap: 12 // Vertical gap between blocks 块间距
    readonly property int blockTitleHeight: 28 // Page title height 大标题高度
    readonly property real blockTitleWidthRatio: 0.55 // Title width share 标题宽度比例
    readonly property int blockSubtitleHeight: 20 // Section heading height 分节标题高度
    readonly property real blockSubtitleWidthRatio: 0.4 // Heading width share 分节标题宽度比例
    readonly property int blockTextHeight: 14 // Text line height 文本行高度
    readonly property real blockTextWidthRatio: 0.85 // Text width share 文本宽度比例
    readonly property real blockTextShortWidthRatio: 0.6 // Short text width share 短文本宽度比例
    readonly property int blockTextLineGap: 8 // Gap between text lines 文本行间距
    readonly property int blockDefaultTextLines: 3 // Default paragraph lines 默认段落行数
    readonly property int blockMaxTextLines: 12 // Longest paragraph 最长段落行数
    readonly property int blockCardPadding: 16 // Card inner padding 卡片内边距
    readonly property int blockCardGap: 12 // Gap between cards 卡片间距
    readonly property int blockDefaultCards: 1 // Default cards in a group 默认卡片数
    readonly property int blockMaxCards: 6 // Most cards in a group 最多卡片数
    readonly property int blockButtonHeight: 28 // Button height 按钮高度
    readonly property int blockButtonWidth: 96 // Button width 按钮宽度
    readonly property int blockButtonGap: 8 // Gap between buttons 按钮间距
    // Width of one cell in a side-by-side example row. Real rows hold fixed-width
    // controls (an input is 180-280px, a button ~96px), not equal slices of the
    // whole card, so the row must stay compact and left-aligned instead of
    // stretching edge to edge.
    // 并排示例行中单个单元的宽度。真实的行放的是固定宽度控件(输入框 180-280px, 按钮约
    // 96px), 而不是整张卡片的等分切片, 因此该行必须保持紧凑左对齐, 不铺满整行。
    readonly property int blockRowCellWidth: 220 // Row cell width 行单元宽度
    readonly property int blockDefaultButtons: 2 // Default buttons in a row 默认按钮数
    readonly property int blockMaxButtons: 6 // Most buttons in a row 最多按钮数
    readonly property int blockIconSize: 24 // Square icon size 方形图标边长
    readonly property int blockAvatarSize: 40 // Round avatar diameter 圆形头像直径
    readonly property real blockImageHeightRatio: 0.24 // Image height share 图片高度比例
    readonly property int blockImageMinHeight: 96 // Shortest image 图片最小高度
    readonly property real blockChartHeightRatio: 0.3 // Chart height share 图表高度比例
    readonly property int blockChartMinHeight: 120 // Shortest chart 图表最小高度
    readonly property real blockCarouselHeightRatio: 0.22 // Carousel height share 轮播高度比例
    readonly property int blockCarouselMinHeight: 96 // Shortest carousel 轮播最小高度
    readonly property real blockCarouselCardWidthRatio: 0.42 // Carousel card width share 轮播卡片宽度比例
    readonly property int blockCarouselCardCount: 3 // Carousel cards per row 轮播卡片数
    readonly property int blockListItemHeight: 44 // List row height 列表项高度
    readonly property int blockListGap: 8 // Gap between list rows 列表项间距
    readonly property int blockDefaultItems: 4 // Default list rows 默认列表项数
    readonly property int blockMaxItems: 12 // Most list rows 最多列表项数
    readonly property int blockInputHeight: 36 // Input height 输入框高度
    readonly property int blockTabHeight: 36 // Tab strip height 标签栏高度
    readonly property int blockTabWidth: 96 // Single tab width 单个标签宽度
    readonly property int blockTabCount: 4 // Tabs in a strip 标签栏标签数
    readonly property int blockDividerThickness: 1 // Divider line thickness 分隔线粗细
    readonly property int blockTableHeaderHeight: 28 // Table header height 表头高度
    readonly property int blockTableRowHeight: 32 // Table row height 表格行高度
    readonly property int blockTableDefaultRows: 3 // Default table rows 默认表格行数
    readonly property int blockTableMaxRows: 10 // Most table rows 最多表格行数
    readonly property int blockTableColumnGap: 12 // Gap between table columns 表格列间距
    readonly property int blockDefaultColumns: 4 // Default table columns 默认表格列数
    readonly property int blockMaxColumns: 8 // Most table columns 最多表格列数
    readonly property int blockBreadcrumbHeight: 12 // Card breadcrumb height 面包屑高度
    readonly property real blockBreadcrumbWidthRatio: 0.3 // Breadcrumb width share 面包屑宽度比例
}
