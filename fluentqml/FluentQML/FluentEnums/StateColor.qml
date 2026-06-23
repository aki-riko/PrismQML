// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// StateColor - Theme-aware interaction colors 主题感知交互色
// No hardcoding Qt.rgba 禁止硬编码
QtObject {
    id: root
    
    required property bool isDark
    property bool isNeo: false
    required property color accentColor
    property var constants: null
    readonly property QtObject _neo: constants ? constants.neoColors : null
    
    // Hover state bg 悬停状态背景
    readonly property color hover: root.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.04)
    readonly property color hoverStrong: root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.06)
    readonly property color bgMedium: root.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.03)
    // Pressed state bg 按下状态背景
    readonly property color pressed: root.isDark ? Qt.rgba(1,1,1,0.04) : Qt.rgba(0,0,0,0.04)
    readonly property color pressedStrong: root.isDark ? Qt.rgba(1,1,1,0.08) : Qt.rgba(0,0,0,0.06)
    // Border color 边框颜色
    readonly property color border: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.08))
    readonly property color borderLight: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.08) : Qt.rgba(0,0,0,0.06))
    readonly property color borderStrong: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.15) : Qt.rgba(0,0,0,0.12))
    // Divider 分隔线
    // divider: 轻量分隔线(非控件边框)。neo 用中等灰, 不用纯黑(纯黑细线滚动会抖动闪烁,
    // 且 neo 的轻分隔不该和粗黑边一样重)。控件边框需黑用 border/dialogBorder。
    readonly property color divider: isNeo ? Qt.rgba(0,0,0,0.22) : (root.isDark ? Qt.rgba(1,1,1,0.12) : Qt.rgba(0,0,0,0.12))
    // Navigation divider (lighter in light mode) 导航分隔线（浅色模式更淡）
    readonly property color navDivider: root.isDark ? Qt.rgba(1,1,1,0.08) : Qt.rgba(0,0,0,0.04)
    // Selected state 选中状态 — 浅色模式必须用 accent 浅色 (#cce4f7), 之前的 "white"
    // 跟 cardColor 完全一样, 用户看不见选中, 列表/表格看似永远没选中。
    readonly property color selected: root.isDark ? "#0d3d6d" : "#cce4f7"
    // Selected + hover 叠加色 — 选中行 hover 时颜色再加深一点, 跟 Excel/QTableWidget 一致,
    // 让用户知道悬浮在选中行上 (而不是 hover 被 selected 覆盖看似没反应)
    readonly property color selectedHover: root.isDark ? "#13558f" : "#b8d8f0"
    // Track/Background 轨道/背景
    readonly property color track: root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.08)
    // Close button hover 关闭按钮悬停
    readonly property color closeHover: root.isDark ? Qt.rgba(1,1,1,0.15) : Qt.rgba(0,0,0,0.1)
    // Scrollbar/Indicator 滚动条/指示器
    readonly property color indicator: root.isDark ? Qt.rgba(1,1,1,0.2) : Qt.rgba(0,0,0,0.2)
    readonly property color indicatorHover: root.isDark ? Qt.rgba(1,1,1,0.25) : Qt.rgba(0,0,0,0.25)
    readonly property color indicatorActive: root.isDark ? Qt.rgba(1,1,1,0.3) : Qt.rgba(0,0,0,0.3)
    // Light pressed 轻按下状态
    readonly property color pressedLight: root.isDark ? Qt.rgba(1,1,1,0.04) : Qt.rgba(0,0,0,0.03)
    // Separator 分割线
    readonly property color separator: root.isDark ? Qt.rgba(1,1,1,0.12) : Qt.rgba(0,0,0,0.08)
    // Scroll track/thumb 滚动条
    readonly property color scrollTrack: root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(0,0,0,0.03)
    readonly property color scrollThumb: root.isDark ? Qt.rgba(1,1,1,0.35) : Qt.rgba(0,0,0,0.25)
    readonly property color scrollThumbHover: root.isDark ? Qt.rgba(1,1,1,0.5) : Qt.rgba(0,0,0,0.4)
    readonly property color scrollThumbPressed: root.isDark ? Qt.rgba(1,1,1,0.6) : Qt.rgba(0,0,0,0.5)
    // Input border 输入框边框
    readonly property color inputBorder: root.isDark ? Qt.rgba(1,1,1,0.12) : Qt.rgba(0,0,0,0.1)
    readonly property color inputBorderStrong: root.isDark ? Qt.rgba(1,1,1,0.2) : Qt.rgba(0,0,0,0.15)
    readonly property color inputBorderNormal: root.isDark ? Qt.rgba(1,1,1,0.08) : Qt.rgba(0,0,0,0.05)
    readonly property color inputBorderDisabled: root.isDark ? Qt.rgba(1,1,1,0.07) : Qt.rgba(0,0,0,0.05)
    // Card border 卡片边框
    readonly property color cardBorder: root.isDark ? indicator : Qt.rgba(0,0,0,0.08)
    // Background variants 背景色变体
    readonly property color bgLight: root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(0,0,0,0.04)
    // Hover variants hover变体
    readonly property color hoverLight: root.isDark ? Qt.rgba(1,1,1,0.04) : Qt.rgba(0,0,0,0.03)
    readonly property color hoverMedium: root.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.06)
    // Selected variants 选中状态变体
    readonly property color selectedStrong: root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.06)
    // Hover/Pressed subtle hover/pressed超轻
    readonly property color hoverSubtle: root.isDark ? Qt.rgba(1,1,1,0.04) : Qt.rgba(0,0,0,0.02)
    readonly property color pressedSubtle: root.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.04)
    // Border subtle 边框透明
    readonly property color borderSubtle: root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(0,0,0,0.05)
    // Disabled bg 禁用背景
    readonly property color disabledBg: root.isDark ? "#2a2a2a" : "#e8e8e8"
    // Primary button disabled bg Primary按钮禁用背景
    // Microsoft WinUI AccentFillColorDisabled: Dark #28FFFFFF / Light #37000000
    readonly property color primaryDisabled: root.isDark ? Qt.rgba(1,1,1,0.157) : Qt.rgba(0,0,0,0.216)
    // Disabled border 禁用边框
    readonly property color disabledBorder: root.isDark ? Qt.rgba(1,1,1,0.16) : Qt.rgba(0,0,0,0.22)
    // Toggle special states Toggle特殊状态
    readonly property color toggleBorder: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.6) : Qt.rgba(0,0,0,0.45))
    readonly property color toggleBorderHover: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.78) : Qt.rgba(0,0,0,0.57))
    readonly property color togglePressed: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.45))
    // CheckBox unchecked fill 复选框未勾选填充
    // Microsoft WinUI ControlAltFill 官方令牌:
    //   normal = ControlAltFillColorSecondary (Dark #19000000 / Light #06000000)
    //   hover  = ControlAltFillColorTertiary  (Dark #0BFFFFFF / Light #0F000000)
    //   press  = ControlAltFillColorQuarternary(Dark #12FFFFFF / Light #18000000)
    readonly property color checkBoxFill: isNeo ? _neo.surface : (root.isDark ? Qt.rgba(0,0,0,0.098) : Qt.rgba(0,0,0,0.024))
    readonly property color checkBoxFillHover: isNeo ? _neo.muted : (root.isDark ? Qt.rgba(1,1,1,0.043) : Qt.rgba(0,0,0,0.059))
    readonly property color checkBoxFillPressed: isNeo ? Qt.darker(_neo.surface, 1.08) : (root.isDark ? Qt.rgba(1,1,1,0.071) : Qt.rgba(0,0,0,0.094))
    // Semi-transparent text 半透明文字
    readonly property color textMedium: root.isDark ? Qt.rgba(1,1,1,0.5) : Qt.rgba(0,0,0,0.5)
    // Drop zone 拖放区域
    readonly property color dropBg: root.isDark ? Qt.rgba(1,1,1,0.02) : Qt.rgba(0,0,0,0.01)
    readonly property color dropBorderHover: root.isDark ? Qt.rgba(1,1,1,0.3) : Qt.rgba(0,0,0,0.2)
    readonly property color disabledTextLight: root.isDark ? Qt.rgba(1,1,1,0.4) : Qt.rgba(0,0,0,0.35)
    readonly property color disabledGray: Qt.rgba(0.5,0.5,0.5,0.5)
    readonly property color dialogOverlay: Qt.rgba(0,0,0,0.4)
    readonly property color dialogBorder: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.1))
    // GroupBox border 组边框
    readonly property color groupBorder: root.isDark ? Qt.rgba(1,1,1,0.15) : Qt.rgba(0,0,0,0.12)
    // Strong text 强调文字
    readonly property color textStrong: root.isDark ? Qt.rgba(1,1,1,0.9) : Qt.rgba(0,0,0,0.8)
    // Slider track 滑块轨道
    readonly property color sliderTrack: root.isDark ? Qt.rgba(1,1,1,0.2) : Qt.rgba(0,0,0,0.39)
    readonly property color sliderTrackDisabled: root.isDark ? Qt.rgba(1,1,1,0.12) : Qt.rgba(0,0,0,0.29)
    // Scroll handle 滚动条手柄
    readonly property color scrollHandleHover: root.isDark ? Qt.rgba(1,1,1,0.4) : Qt.rgba(0,0,0,0.3)
    readonly property color scrollHandleDefault: root.isDark ? Qt.rgba(1,1,1,0.25) : Qt.rgba(0,0,0,0.2)
    // Card default bg 卡片默认背景
    readonly property color cardDefaultBg: root.isDark ? Qt.rgba(1,1,1,0.03) : Qt.rgba(0,0,0,0.02)
    readonly property color notificationText: root.isDark ? Qt.rgba(1,1,1,0.75) : Qt.rgba(0,0,0,0.65)
    // compact-nav window content area 内容区
    readonly property color contentBorder: root.isDark ? Qt.rgba(0,0,0,0.18) : "#e4e7ea"
    readonly property color contentBg: isNeo ? _neo.background : (root.isDark ? "#272727" : "#f7f9fc")
    // Semi-transparent content bg for Mica effect 云母效果半透明内容背景
    readonly property color contentBgTransparent: root.isDark ? Qt.rgba(1,1,1,0.03) : Qt.rgba(1,1,1,0.5)
    // Loading/Progress 加载/进度
    readonly property color loadingBorder: root.isDark ? Qt.rgba(1,1,1,0.15) : Qt.rgba(0,0,0,0.1)
    readonly property color progressTrack: root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.06)
    
    // Skeleton loading 骨架屏
    readonly property color skeletonBase: root.isDark ? Qt.rgba(1,1,1,0.12) : Qt.rgba(0,0,0,0.09)
    readonly property color skeletonShimmer: root.isDark ? Qt.rgba(1,1,1,0.25) : Qt.rgba(0,0,0,0.04)
    
    // SettingCard 颜色 (Fluent Design 配色规范)
    readonly property color settingCardBg: root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(1,1,1,0.7)
    readonly property color settingCardBorder: root.isDark ? Qt.rgba(0,0,0,0.2) : Qt.rgba(0,0,0,0.075)
    // Expand view bg 展开视图背景
    readonly property color expandViewBg: isNeo ? _neo.surface : (root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(1,1,1,0.7))
    // Content label color (Microsoft WinUI TextFillColorSecondary: Dark #C5FFFFFF / Light #9E000000)
    readonly property color settingCardContent: root.isDark ? Qt.rgba(1,1,1,0.77) : Qt.rgba(0,0,0,0.61)
    // Expand button hover/pressed
    readonly property color expandBtnHover: root.isDark ? Qt.rgba(1,1,1,0.055) : Qt.rgba(0,0,0,0.055)
    readonly property color expandBtnPressed: root.isDark ? Qt.rgba(1,1,1,0.04) : Qt.rgba(0,0,0,0.04)
    // Expander separator (stronger than border) 展开器分隔线（比边框更深）
    readonly property color expanderSeparator: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.2) : Qt.rgba(0,0,0,0.15))
    
    // ==================== Fluent Design Precise Values 精确匹配值 ====================
    // Control background colors 控件背景颜色（按钮、输入框、下拉框等）
    // Unified opaque colors for all controls 所有控件统一不透明色
    // Light: 默认fefefe, 悬浮fafafa, 按下/聚焦fcfcfc
    // Dark: 默认4e4e4e, 悬浮595959, 按下/聚焦4e4e4e
    readonly property color controlBg: isNeo ? _neo.surface : (root.isDark ? "#4e4e4e" : "#fefefe")
    // 全局统一 hover/pressed 灰阶 (Fluent UI 标准 subtle hover):
    // controlBgHover = menuItemHover = tableHoverLight = #f0f0f0,
    // 所有可交互行/项 hover 视觉一致, 用户能明显感知。
    readonly property color controlBgHover: isNeo ? _neo.muted : (root.isDark ? "#3c3c3c" : "#f0f0f0")
    readonly property color controlBgPressed: isNeo ? Qt.darker(_neo.surface, 1.08) : (root.isDark ? "#353535" : "#e5e5e5")
    readonly property color controlBgDisabled: isNeo ? _neo.muted : (root.isDark ? "#3a3a3a" : "#ffffff")
    // Transparent button colors 透明按钮颜色
    // Light: hover ebebeb, pressed ededed | Dark: hover 3a3a3a, pressed 323232
    readonly property color transparentHover: isNeo ? _neo.muted : (root.isDark ? "#3a3a3a" : "#ebebeb")
    readonly property color transparentPressed: isNeo ? Qt.darker(_neo.muted, 1.05) : (root.isDark ? "#323232" : "#ededed")
    // Transparent button default bg (same RGB as hover, alpha=0) 透明按钮默认背景（与悬浮色相同RGB，alpha=0）
    // Prevents gray flash during ColorAnimation from transparent to hover color 防止从透明到悬浮色的颜色动画出现灰色闪烁
    readonly property color controlBgTransparent: root.isDark ? Qt.rgba(58/255, 58/255, 58/255, 0) : Qt.rgba(235/255, 235/255, 235/255, 0)
    readonly property color pickerBorder: isNeo ? _neo.border : (root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(0,0,0,0.07))
    readonly property color pickerTextDisabled: root.isDark ? Qt.rgba(1,1,1,0.4) : Qt.rgba(0,0,0,0.35)
    readonly property color pickerTextPlaceholder: root.isDark ? Qt.rgba(1,1,1,0.6) : Qt.rgba(0,0,0,0.6)
    readonly property color pickerTextSecondary: root.isDark ? Qt.rgba(1,1,1,0.4) : Qt.rgba(0,0,0,0.4)
    
    // Calendar navigation button 日历导航按钮
    readonly property color calendarNavHover: root.isDark ? Qt.rgba(1,1,1,0.035) : Qt.rgba(0,0,0,0.035)
    readonly property color calendarNavPressed: root.isDark ? Qt.rgba(1,1,1,0.024) : Qt.rgba(0,0,0,0.024)
    
    // Menu item colors (popup menu, dropdown list items) 菜单项颜色（弹出菜单、下拉列表项）
    // Default transparent, hover (light: #f0f0f0, dark: #3c3c3c), pressed (light: #eaeaea, dark: #373737) 默认透明，悬浮浅色 f0f0f0/深色 3c3c3c，按下浅色 eaeaea/深色 373737
    readonly property color menuItemHover: root.isDark ? "#3c3c3c" : "#f0f0f0"
    readonly property color menuItemPressed: root.isDark ? "#373737" : "#eaeaea"
    
    // Chip 颜色 (不透明)
    readonly property color chipBg: root.isDark ? "#2d2d2d" : "#f0f0f0"
    readonly property color chipBgHover: root.isDark ? "#3a3a3a" : "#e8e8e8"
    readonly property color chipBgPressed: root.isDark ? "#212121" : "#f7f7f7"
    readonly property color chipCloseHover: root.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.06)
    readonly property color chipClosePressed: root.isDark ? Qt.rgba(1,1,1,0.15) : Qt.rgba(0,0,0,0.1)
    
    // ==================== Accent Color Variants 主题色变体 ====================
    // Accent with alpha - for backgrounds 主题色透明度背景
    readonly property color accentSubtle: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.1)
    readonly property color accentLight: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.15)
    readonly property color accentMedium: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.3)
    readonly property color accentBorder: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.3)
    
    // ==================== Mask/Overlay 遮罩/覆盖层 ====================
    // Image cropper mask (dark mask for light mode) 图片裁剪遮罩（浅色模式用深色遮罩）
    readonly property color maskHeavy: Qt.rgba(0,0,0,0.6)
    readonly property color maskMedium: Qt.rgba(0,0,0,0.4)
    readonly property color maskLight: Qt.rgba(0,0,0,0.3)
    readonly property color maskSubtle: Qt.rgba(0,0,0,0.2)
    // Image cropper mask (light mask for dark mode) 图片裁剪遮罩（深色模式用浅色遮罩）
    readonly property color maskWhiteHeavy: Qt.rgba(1,1,1,0.5)
    readonly property color maskWhiteMedium: Qt.rgba(1,1,1,0.35)
    readonly property color maskWhiteLight: Qt.rgba(1,1,1,0.25)
    // Theme-aware cropper mask 主题感知裁剪遮罩
    readonly property color cropperMask: root.isDark ? maskWhiteHeavy : maskHeavy
    // Theme-aware cropper line/handle 主题感知裁剪线条/手柄（深色模式用深色，浅色模式用白色）
    readonly property color cropperLine: root.isDark ? Qt.rgba(0.1,0.1,0.1,1) : Qt.rgba(1,1,1,1)
    
    readonly property color whiteTransparent: Qt.rgba(1,1,1,0)
    
    // White overlay (for tools on dark bg) 白色覆盖层
    readonly property color whiteOverlay: Qt.rgba(1,1,1,0.15)
    readonly property color whiteOverlayHover: Qt.rgba(1,1,1,0.2)
    readonly property color whiteOverlayPressed: Qt.rgba(1,1,1,0.1)
    // On-accent semi-transparent (for Primary/Gradient button elements) 主题色按钮上的半透明白色
    readonly property color onAccentOverlay: Qt.rgba(1,1,1,0.3)
    // White button on image (for FlipView nav buttons) 图片上的白色按钮
    readonly property color whiteButton: Qt.rgba(1,1,1,0.8)
    readonly property color whiteButtonHover: Qt.rgba(1,1,1,0.95)
    // ==================== ColorPicker Specific 颜色选择器专用 ====================
    // ColorPicker channel slider 颜色通道滑块
    readonly property color colorSliderThumbBorder: root.isDark ? Qt.rgba(0,0,0,0.3) : Qt.rgba(0,0,0,0.2)
    
    // ==================== FilterBar Specific 筛选栏专用 ====================
    // FilterBar container/item 容器/选项
    readonly property color filterContainer: root.isDark ? Qt.rgba(1,1,1,0.05) : Qt.rgba(0,0,0,0.04)
    readonly property color filterItemHover: root.isDark ? Qt.rgba(1,1,1,0.08) : Qt.rgba(0,0,0,0.06)
    
    // ==================== PipsPager Specific 分页指示器专用 ====================
    // Pip indicator colors 分页指示器颜色
    readonly property color pipNormal: root.isDark ? Qt.rgba(1,1,1,0.5) : Qt.rgba(0,0,0,0.45)
    readonly property color pipActive: root.isDark ? Qt.rgba(1,1,1,0.8) : Qt.rgba(0,0,0,0.62)
    
    // ==================== Chart Colors 图表颜色 ====================
    // Chart tooltip text (white on dark bg) 图表tooltip文字（深色背景上的白字）
    readonly property color chartTooltipText: Qt.rgba(1,1,1,0.7)
    
    // Chart gradient/fill alphas 图表渐变/填充透明度
    readonly property real chartFillStrong: 0.6       // Stacked area fill 堆叠面积填充
    readonly property real chartFillMedium: 0.3       // Area gradient top 面积渐变顶部
    readonly property real chartFillLight: 0.15       // Area gradient middle 面积渐变中部
    readonly property real chartFillSubtle: 0.05      // Area gradient bottom 面积渐变底部
    readonly property real chartFillFaint: 0.02       // Area gradient end 面积渐变末端
    readonly property real chartLineAlpha: 0.5        // Average line alpha 平均线透明度
    readonly property real chartStrokeAlpha: 0.6      // Stroke alpha 描边透明度
    
    // ==================== Filled Button Colors 填充按钮颜色 ====================
    // Fluent Design FilledButton hover/pressed fallback colors 填充按钮悬停/按下回退色
    readonly property color filledHover: "#c9cacb"
    readonly property color filledPressed: "#979798"
    
    // ==================== SegmentedControl Colors 分段控件颜色 ====================
    // Background 背景
    readonly property color segmentedBg: root.isDark ? Qt.rgba(0,0,0,0.1) : Qt.rgba(0,0,0,0.02)
    // Border 边框
    readonly property color segmentedBorder: root.isDark ? Qt.rgba(1,1,1,0.08) : Qt.rgba(0,0,0,0.06)
    // Selected item bg 选中项背景
    readonly property color segmentedSelected: root.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(1,1,1,0.7)
    // Selected item border 选中项边框
    readonly property color segmentedSelectedBorder: root.isDark ? Qt.rgba(1,1,1,0.055) : Qt.rgba(0,0,0,0.075)
    // Hover bg 悬停背景
    readonly property color segmentedHover: root.isDark ? Qt.rgba(1,1,1,0.035) : Qt.rgba(0,0,0,0.035)
    // Pressed bg 按下背景
    readonly property color segmentedPressed: root.isDark ? Qt.rgba(1,1,1,0.025) : Qt.rgba(0,0,0,0.025)
    
    // ==================== Dialog Button Group 对话框按钮组 ====================
    // Button group background 按钮组背景
    readonly property color actionsRowBg: isNeo ? _neo.muted : (root.isDark ? Qt.rgba(1,1,1,0.04) : Qt.rgba(0,0,0,0.024))
    
    // ==================== Navigation Selected 导航选中 ====================
    // Navigation bar item selected bg 导航栏项选中背景
    // dark: navigation selected overlay; Light: use transparentHover for Mica contrast
    readonly property color navSelected: root.isDark ? Qt.rgba(1,1,1,0.16) : transparentHover
    
    // ==================== TreeWidget Colors 树形组件颜色 ====================
    // Tree item hover/selected bg 树形项悬停/选中背景
    readonly property color treeItemHover: root.isDark ? Qt.rgba(1,1,1,0.035) : Qt.rgba(0,0,0,0.035)

    // ==================== List item state layers 列表项状态层 ====================
    // Microsoft WinUI SubtleFill 官方令牌:
    //   hover  = SubtleFillColorSecondary (Dark #0FFFFFFF / Light #09000000)
    //   press  = SubtleFillColorTertiary  (Dark #0AFFFFFF / Light #06000000)
    readonly property color listItemHover: root.isDark ? Qt.rgba(1,1,1,0.059) : Qt.rgba(0,0,0,0.035)
    readonly property color listItemPressed: root.isDark ? Qt.rgba(1,1,1,0.039) : Qt.rgba(0,0,0,0.024)
    
    // ==================== Acrylic Effect 亚克力效果 ====================
    // Acrylic tint color 亚克力 tint 颜色
    // dark: 微软 WinUI AcrylicInAppFillColorDefault 基色 #2C2C2C + 80% opacity (0.8 档)
    // light: #f3f3f3 with ~70% opacity
    readonly property color acrylicTintColor: root.isDark ? Qt.rgba(44/255, 44/255, 44/255, 204/255) : Qt.rgba(243/255, 243/255, 243/255, 180/255)
}