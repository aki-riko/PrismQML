// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "_internal" as MetricsInternal

// Metrics - Size and spacing constants 尺寸和间距常量
// Includes: Duration, Spacing, Radius, Typography, IconSize, etc.
QtObject {
 id: root
 
 required property bool isDark
 property bool isTicket: false
 property bool isNeumorphism: false
 property real devicePixelRatio: 1
 // Skin palette single sources of truth are injected by Enums 皮肤配色真相源由 Enums 注入
 property var constants: null

 function _physicalPixelWidth(designWidth) {
 var ratio = root.devicePixelRatio > 0 ? root.devicePixelRatio : 1
 return Math.max(1, Math.round(designWidth * ratio)) / ratio
 }
 
 // ==================== Duration 动画时长 ====================
 readonly property QtObject duration: QtObject {
 // Animation durations in MILLISECONDS — 动画时长以毫秒为单位
 // 重要: 时长是绝对 ms, 与屏幕刷新率无关。
 // 60Hz 屏 200ms 动画 = 12 帧
 // 120Hz 屏 200ms 动画 = 24 帧
 // 240Hz 屏 200ms 动画 = 48 帧
 // 高刷屏自动获得更平滑的过渡, 不需要在此调整数值。
 // 如需逐帧驱动 (如拖拽、惯性滚动), 请使用 FrameAnimation 跟随屏幕刷新率,
 // 不要用 Timer { interval: 16 } 这种 60fps 硬编码。
 readonly property int none: 0 // No animation or delay 无动画或延迟
 readonly property int persistent: -1 // Disable automatic timeout 禁用自动关闭
 readonly property int tick: 1 // High-refresh timer tick 高刷定时器间隔(1ms)
 readonly property int ultraFast: 50
 readonly property int instant: 50
 readonly property int wheelPickerRepeatInterval: 50 // Wheel picker held-button repeat interval 滚轮选择器长按重复间隔
 readonly property int spinBoxRepeatInterval: 60 // SpinBox held-button repeat interval 微调框长按重复间隔
 readonly property int spinBoxRepeatMinInterval: 20 // SpinBox accelerated repeat lower bound 微调框加速重复最短间隔
 readonly property int fast: 100
 readonly property int normal: 150
 readonly property int medium: 200
 readonly property int slow: 250
 readonly property int slower: 300
 readonly property int page: 320 // Page transition 页面切换
 readonly property int dialog: 400
 readonly property int wheelPickerRepeatDelay: 500 // Wheel picker held-button initial delay 滚轮选择器长按初始延迟
 readonly property int spinBoxRepeatDelay: 500 // SpinBox held-button initial delay 微调框长按初始延迟
 readonly property int splashTimeout: 5000 // Splash dismiss fallback when first page never signals loaded 首屏加载信号意外不来时关闭欢迎页的兜底超时
 readonly property int splashMinimumVisible: 600 // Minimum stable splash display after the window becomes visible 窗口可见后启动画面最短稳定展示时长
 readonly property int scroll: 750
 // 导航滚轮时长必须跟随 scroll: 250ms 在高刷屏上尾段会退化成逐物理像素蠕动。
 // Navigation wheel duration tracks scroll; 250ms decays into per-physical-pixel crawl.
 readonly property int navigationScroll: scroll // Navigation wheel smooth scroll animation 导航滚轮平滑滚动动画
 readonly property int bounce: 750 // Scroll bounce animation 滚动回弹动画
 readonly property int verySlow: 1000 // Very slow ornamental animation 较慢装饰动画
 readonly property int xslow: 1200 // Extra slow ornamental animation 超慢装饰动画
 // Data component animation durations 数据组件动画时长
 readonly property int stagger: 35 // Row stagger delay 行错开延迟
 readonly property int enter: 200 // Enter/appear animation 进场动画
 readonly property int exit: 150 // Exit/disappear animation 退场动画
 readonly property int elevation: 250 // Shadow elevation transition 阴影升降
 readonly property int spring: 350 // Spring/elastic animation 弹性动画
 // Tip/Popup animation durations Tip/弹出动画时长
 readonly property int tooltipShowDelay: 500 // Default Widget tooltip delay Widget 工具提示默认延迟
 readonly property int tipShow: 200 // TipPopup show animation 提示显示动画
 readonly property int tipArrow: 180 // TipPopup arrow animation 提示箭头动画
 readonly property int tipHide: 125 // TipPopup hide animation 提示隐藏动画
 // Notification/display durations 通知/显示时长
 readonly property int toast: 3000 // Toast default 默认提示
 readonly property int infoBar: 3000 // InfoBar default 信息条
 readonly property int notification: 5000 // Desktop notification 桌面通知
 readonly property int confetti: 3000 // Confetti animation 彩纸动画
 readonly property int pulse: 2000 // Pulse animation 脉冲动画
 readonly property int countUp: 1000 // CountUp animation 计数动画
 readonly property int marquee: 1000 // Marquee pause 跑马灯暂停
 readonly property int splashBreathe: 1200 // Splash icon breathe cycle half-duration 启动画面图标单程呼吸时长
 readonly property int splashProgressSpin: 1000 // Splash progress rotation cycle 启动画面进度旋转周期
 readonly property int chart: 500 // Chart animation 图表动画
 readonly property int progressComplete: 1500 // Progress complete display 进度完成后显示时长
 readonly property int copyFeedback: 1500 // Clipboard copy feedback display 复制反馈显示时长
 // Indeterminate progress timings 不确定进度时长
 readonly property int progressLoop: 2000 // Single bar loop cycle 单条循环周期
 readonly property int emptyFloat: 1500 // Empty state float animation 空状态浮动动画
 // Indicator animation durations 指示器动画时长
 readonly property int crossFade: 600 // CrossFade animation 交叉淡入动画
 }

 // ==================== Motion 运动参数 ====================
 readonly property QtObject motion: QtObject {
 readonly property int hoverExitDuration: root.duration.none // Hover exit resets immediately 悬浮退出立即复位
 readonly property int navigationTitleMarqueeSpeed: 25 // Navigation title hover marquee speed in pixels per second 导航标题悬浮跑马灯速度（像素/秒）

 }
 
 // ==================== Z-Index 层级 ====================
 readonly property QtObject zIndex: QtObject {
 readonly property int background: -1
 readonly property int base: 0
 readonly property int content: 1
 readonly property int header: 2
 readonly property int controls: 3
 readonly property int controlsAbove: 4
 readonly property int popup: 5
 readonly property int modal: 6
 readonly property int overlay: 7
 readonly property int tooltip: 8
 readonly property int splash: 9999
 readonly property int inputInteraction: 10 // Input cursor/focus interaction layer 输入光标与焦点交互层
 readonly property int inputControls: 11 // Input embedded controls above interaction layer 输入内嵌控件层
 }
 
 // ==================== Opacity 透明度 ====================
 readonly property QtObject opacity: QtObject {
 readonly property real invisible: 0.0
 readonly property real watermark: 0.3 // Watermark text opacity (Fluent Design) 水印文字透明度
 readonly property real faint: 0.1
 readonly property real light: 0.3
 readonly property real medium: 0.5
 readonly property real secondary: 0.6 // Secondary text/icon opacity 次要文字/图标透明度
 readonly property real heavy: 0.7
 readonly property real strong: 0.85
 readonly property real visible: 1.0
 readonly property real disabled: 0.4
 readonly property real hover: 0.08
 readonly property real pressed: 0.12
 }
 
 // ==================== Mask 遮罩参数 ====================
 readonly property QtObject mask: QtObject {
 readonly property real thresholdMin: 0.5 // Mask threshold minimum 遮罩阈值最小值
 readonly property real spreadAtMin: 0.0 // Mask spread at minimum 遮罩最小扩散
 readonly property real thresholdFull: 0.0 // Full mask threshold 完全遮罩阈值
 readonly property real spreadFull: 1.0 // Full mask spread 完全遮罩扩散
 }
 
 // ==================== Blur 模糊半径 ====================
 readonly property QtObject blur: QtObject {
 readonly property real acrylic: 30 // Acrylic effect blur 亚克力效果模糊
 readonly property real background: 64 // Background blur 背景模糊
 readonly property real light: 16 // Light blur 轻度模糊
 }
 
 // ==================== Border 边框宽度 ====================
 readonly property QtObject border: QtObject {
 readonly property int none: 0
 // Quantize design widths to whole physical pixels. 分数缩放下将设计描边量化为整数物理像素。
 // This prevents one logical edge from rasterizing as alternating 1/2-pixel lines at 125%/150%.
 // 避免同一逻辑描边在 125%/150% 下因方向与落点不同交替栅格化为 1/2 像素。
 readonly property real thin: root._physicalPixelWidth(1)
 readonly property real medium: root._physicalPixelWidth(1.5)
 readonly property real normal: root._physicalPixelWidth(2)
 readonly property real thick: root._physicalPixelWidth(3)
 }

 // ==================== Neobrutalism 新粗野皮肤度量+配色 ====================
 // 几何范式集中放此; 配色【引用 Constants.neoColors 单一真相源】(dark-aware), 不在此重复定义,
 // 否则改一处忘另一处会出 bug(深色边框没反转即此坑)。控件读 Enums.neo.xxx。
 readonly property QtObject neo: QtObject {
 // ---- 几何 ----
 readonly property real borderWidth: root._physicalPixelWidth(2) // 粗描边宽度
 readonly property int radius: 6 // 圆角(0.375rem≈6px, 接近直角)
 readonly property real shadowOffset: 4 // 硬阴影偏移(X=Y), 即"纸面投影"距离
 readonly property real pressOffset: 4 // 按下时控件下移/右移距离(= shadowOffset, 视觉上压平阴影)
 // ---- 配色: 全部指向 Constants.neoColors(按 isDark 自动切 light/dark) ----
 readonly property color shadowColor: root.constants.neoColors.shadow
 readonly property color borderColor: root.constants.neoColors.border
 readonly property color background: root.constants.neoColors.background
 readonly property color surface: root.constants.neoColors.surface
 readonly property color foreground: root.constants.neoColors.foreground
 readonly property color secondaryForeground: root.constants.neoColors.secondaryForeground
 readonly property color primary: root.constants.neoColors.primary
 readonly property color primaryForeground: root.constants.neoColors.primaryForeground
 readonly property color success: root.constants.neoColors.success
 readonly property color danger: root.constants.neoColors.danger
 readonly property color warning: root.constants.neoColors.warning
 readonly property color info: root.constants.neoColors.info
 }

 // ==================== Neumorphism 新拟态皮肤度量+配色 ====================
 // Convex surfaces use paired outer shadows; inputs and tracks opt into inset mode.
 // 凸起表面使用双向外阴影，输入框与轨道可使用内凹模式。
 readonly property QtObject neumorphism: QtObject {
     readonly property real borderWidth: 0
     readonly property int radius: 14
     // Keep regular surfaces close to the canvas at fractional DPI; popups keep their own elevation tokens.
     // 普通表面在分数 DPI 下保持贴近画布；弹层继续使用独立的悬浮 token。
     readonly property real shadowOffset: 4
     readonly property real shadowBlur: 12
     // Pull the opaque shadow core under the surface so it cannot look like a half outline.
     // 将阴影实色核心收回表面下方，避免形成半圈描边。
     readonly property real shadowSpread: -shadowOffset
     readonly property real popupShadowOffset: 4
     readonly property real popupShadowBlur: 14
     readonly property real popupShadowSpread: -popupShadowOffset
     // Transparent native-window margin for the complete popup shadow.
     // 原生透明窗口为完整弹层阴影预留的安全边距。
     readonly property real popupShadowMargin: root.spacing.xl
     readonly property real insetEdgeSize: root.spacing.xs
     readonly property real insetSoftness: root.spacing.s
     readonly property real insetNormalSampleStep: root.spacing.micro
     readonly property real insetDarkOpacity: root.opacity.light
     readonly property real insetLightOpacity: root.opacity.light
     readonly property real switchShadowOffset: 2
     readonly property real switchShadowBlur: 6
     readonly property real switchShadowSpread: -switchShadowOffset
     readonly property real pressInset: 2
     readonly property color background: root.constants.neumorphismColors.background
     readonly property color surface: root.constants.neumorphismColors.surface
     readonly property color muted: root.constants.neumorphismColors.muted
     readonly property color hover: root.constants.neumorphismColors.hover
     readonly property color pressed: root.constants.neumorphismColors.pressed
     readonly property color disabledSurface: root.constants.neumorphismColors.disabledSurface
     readonly property color divider: root.constants.neumorphismColors.divider
     readonly property color indicator: root.constants.neumorphismColors.indicator
     readonly property color indicatorHover: root.constants.neumorphismColors.indicatorHover
     readonly property color foreground: root.constants.neumorphismColors.foreground
     readonly property color secondaryForeground: root.constants.neumorphismColors.secondaryForeground
     readonly property color disabledForeground: root.constants.neumorphismColors.disabledForeground
     readonly property color shadowDark: root.constants.neumorphismColors.shadowDark
     readonly property color shadowLight: root.constants.neumorphismColors.shadowLight
     readonly property color primary: root.constants.neumorphismColors.primary
     readonly property color primaryForeground: root.constants.neumorphismColors.primaryForeground
 }

 // ==================== Vintage Ticket 复古票据皮肤度量+配色 ====================
 // Ticket surfaces use fine ink lines, square paper geometry and no elevation shadow.
 // 票据表面使用油墨细线、直角纸面与零悬浮阴影。
 readonly property QtObject ticket: QtObject {
 readonly property real borderWidth: root._physicalPixelWidth(1)
 readonly property real emphasisBorderWidth: root._physicalPixelWidth(2)
 readonly property int radius: 0
 readonly property int perforationLength: 6
 readonly property int perforationGap: 4
 readonly property color background: root.constants.ticketColors.background
 readonly property color surface: root.constants.ticketColors.surface
 readonly property color muted: root.constants.ticketColors.muted
 readonly property color foreground: root.constants.ticketColors.foreground
 readonly property color secondaryForeground: root.constants.ticketColors.secondaryForeground
 readonly property color disabledForeground: root.constants.ticketColors.disabledForeground
 readonly property color borderColor: root.constants.ticketColors.border
 readonly property color dividerColor: root.constants.ticketColors.divider
 readonly property color primary: root.constants.ticketColors.primary
 readonly property color primaryForeground: root.constants.ticketColors.primaryForeground
 readonly property color success: root.constants.ticketColors.success
 readonly property color danger: root.constants.ticketColors.danger
 readonly property color warning: root.constants.ticketColors.warning
 readonly property color info: root.constants.ticketColors.info
 }
 
 // ==================== IconSize 图标尺寸 ====================
 readonly property QtObject iconSize: QtObject {
 readonly property int micro: 8
 readonly property int tiny: 10
 readonly property int xs: 12
 readonly property int checkmark: 12 // Checkbox checkmark icon 复选框勾选图标
 readonly property int s: 14
 readonly property int small: 16 // Small icon (tree/list) 小图标（树形/列表）
 readonly property int m: 16
 readonly property int l: 18
 readonly property int xl: 20
 readonly property int xxl: 24
 readonly property int xxxl: 32
 readonly property int display: 48
 }
 
 // ==================== Spacing 间距 ====================
 readonly property QtObject spacing: QtObject {
 readonly property int none: 0
 readonly property int micro: 1
 readonly property int xxs: 2
 readonly property int cardElevate: 3
 readonly property int xs: 4
 readonly property int cardShadow: 5
 readonly property int s: 6
 readonly property int m: 8
 readonly property int l: 12
 readonly property int xl: 16
 readonly property int xxl: 20
 readonly property int xxxl: 24
 // Layout specific spacing 布局专用间距
 readonly property int timelineIndent: 40 // Timeline card left padding 时间线卡片左内边距
 readonly property int timelineHeaderHeight: 40 // Timeline header height 时间线标题高度
 readonly property int timelineGraphLane: 16 // Timeline graph lane spacing 时间线图轨道间距
 readonly property int timelineGraphPadding: 8 // Timeline graph horizontal padding 时间线图水平留白
 readonly property int arrowAreaWidth: 40 // ComboBox arrow area width 下拉框箭头区域宽度
 readonly property int listItemPadding: 12 // List item left/right padding 列表项左右内边距
 // Window layout spacing 窗口布局间距
 readonly property int navTitleGap: 160 // top-nav window nav left margin 顶部导航左边距
 readonly property int windowButtonGap: 150 // top-nav window right margin for buttons 窗口按钮右边距
 readonly property int navigationScrollStep: 72 // Navigation wheel scroll distance per tick 导航滚轮每格滚动距离
 // Scroll overshoot 滚动超出
 readonly property int scrollOvershoot: 150 // Scroll overshoot distance 滚动超出距离
 }
 
 // ==================== Radius 圆角 ====================
 readonly property QtObject radius: QtObject {
 readonly property int none: 0
 // Ticket surfaces are square by default; explicit circle geometry keeps semantic circles.
 // 票据皮肤的通用表面默认直角；显式圆形几何继续保留语义圆形。
 readonly property real micro: root.isTicket ? 0 : 1.5
 readonly property int tiny: root.isTicket ? 0 : 2
 readonly property int small: root.isTicket ? 0 : 4
 readonly property int card: root.isTicket ? 0 : 5
 readonly property int medium: root.isTicket ? 0 : 6 // Medium radius 中等圆角
 readonly property int large: root.isTicket ? 0 : 8
 readonly property int dialog: root.isTicket ? 0 : 10 // Fluent Design dialog radius 对话框圆角
 readonly property int xlarge: root.isTicket ? 0 : 16
 readonly property int pill: 9999
 }
 
 // ==================== Control Size 控件尺寸 ====================
 readonly property QtObject controlSize: QtObject {
 // Toggle controls 切换控件
 readonly property int radioOuter: 20 // Fluent Design: radius=10 → diameter=20
 readonly property int radioInner: 8
 readonly property int checkboxOuter: 18
 readonly property int checkboxInner: 12
 readonly property int switchWidth: 44
 readonly property int switchHeight: 24
 readonly property int switchThumb: 20
 // Input controls 输入控件
 readonly property int inputHeight: 32 // Fluent Design standard height 标准高度（与 buttonHeight 对齐）
 readonly property int inputDefaultWidth: 200 // Input default width 输入框默认宽度
 readonly property int inputHeightLarge: 40
 readonly property int inputHeightCompact: 28
 readonly property int inputHeightLabel: 56 // Label input height (with floating label) 带浮动标签输入框高度
 readonly property int textEditScrollThumbMinHeight: 20 // TextEdit scroll thumb minimum height 多行文本滚动拇指最小高度
 readonly property int inputLabelTextHeight: 24 // Floating label text field height 浮动标签文本框高度
 readonly property int pickerRow: 36
 // Navigation controls 导航控件
 readonly property int navBarHeight: 48 // Top navigation bar height
 readonly property int navBarWidth: 68 // NavigationBar width (64px button + 2px margins) 导航栏宽度
 readonly property int navBarItemWidth: 64 // NavigationBarItem width 导航栏项宽度
 readonly property int navBarItemHeight: 60 // NavigationBarItem height 导航栏项高度
 readonly property int bottomTabBarHeight: 56 // BottomTabBar height 底部导航栏高度
 readonly property int tabBarHeight: 40 // TabBar height
 readonly property int segmentedHeight: 36 // SegmentedControl height
 readonly property int segmentedMinWidth: 60 // SegmentedControl item min width 分段项最小宽度
 readonly property int segmentedToolSize: 36 // Segmented tool item size 分段工具项尺寸
 readonly property int commandBarButtonSize: 36 // CommandBar button size (square) 命令栏按钮尺寸（正方形）
 readonly property int statusBarHeight: 24 // StatusBar height 状态栏高度
 // Feedback controls 反馈控件
 readonly property int tooltipHeight: 28 // Tooltip height (single line) 提示单行高度
 readonly property int tooltipMaxWidth: 320 // Tooltip max width before wrapping 提示自动换行前的最大宽度
 readonly property int toastWidth: 360 // Toast width
 readonly property int toastMaxWidth: 800 // Toast maximum width Toast 最大宽度
 readonly property int toastHeight: 80 // Toast height
 // Chat controls 聊天控件
 readonly property int chatContentMaxWidth: 600 // Shared chat content width 聊天内容共享最大宽度
 readonly property int codeBlockDefaultWidth: 400 // Code block default width 代码块默认宽度
 readonly property int codeBlockHeaderHeight: 24 // Code block header height 代码块标题栏高度
 readonly property int codeBlockCopyButtonWidth: 50 // Code block copy button width 代码块复制按钮宽度
 readonly property int codeBlockCopyButtonHeight: 22 // Code block copy button height 代码块复制按钮高度
 // Container controls 容器控件
 readonly property int cardWidth: 400 // Card default width
 readonly property int cardContentWidth: 300 // Card content area width (cardWidth - icon/padding area) 卡片内容区域宽度
 readonly property int cardHeight: 64 // Card default height
 readonly property int dropFileHeight: 140 // DropZone default height 拖放组件默认高度
 readonly property int splitPaneMinimumSize: 50 // SplitPane pane minimum extent 分割面板最小范围
 // Calendar controls 日历控件
 readonly property int calendarCell: 32 // Calendar day cell size 日历日期单元格尺寸
 readonly property int calendarCellHeight: 36 // Calendar cell row height 日历单元格行高
 // Timeline controls 时间线控件
 readonly property int timelineIcon: 15 // Timeline group icon size 时间线分组图标尺寸
 readonly property int timelineCardIcon: 12 // Timeline card icon size 时间线卡片图标尺寸
 readonly property int timelineIconText: 10 // Timeline icon inner text size 时间线图标内文字尺寸
 readonly property int timelineCardIconText: 8 // Timeline card icon inner text size 时间线卡片图标内文字尺寸
 readonly property int timelineGraphNode: 10 // Timeline graph commit node size 时间线图提交节点尺寸
 // Button controls 按钮控件
 readonly property int closeButton: 32 // Close button size 关闭按钮尺寸
 readonly property int buttonMinWidth: 80 // Button minimum width 按钮最小宽度
 readonly property int buttonHeight: 32 // Button height 按钮高度
 readonly property int toolButtonWidth: 36 // ToolButton width 工具按钮宽度
 readonly property int splitButtonArrowWidth: 26 // Split button arrow area width 分割按钮箭头区域宽度
 readonly property int splitButtonContentOffset: 13 // Split button content offset 分割按钮内容偏移
 readonly property int dropdownArrowWidth: 20 // Dropdown button arrow width 下拉按钮箭头宽度
 // Dialog controls 对话框控件
 readonly property int dialogButtonHeight: 32 // Dialog button height 对话框按钮高度
 // Navigation item controls 导航项控件
 readonly property int topNavItemHeight: 36 // top-nav window nav item height 顶部导航项高度
 readonly property int topNavItemPadding: 24 // top-nav window nav item padding 顶部导航项内边距
 readonly property int topNavIndicatorHeight: 3 // top-nav window indicator height 顶部导航指示条高度
 readonly property int navIndicatorHeight: 16 // Navigation indicator height 导航指示条高度
 readonly property int navIndicatorHeightPressed: 18 // Navigation indicator height when pressed 按下时导航指示条高度
 readonly property int navIndicatorWidth: 3 // Navigation indicator width 导航指示条宽度
 readonly property int navPanelExpandWidth: 320 // Navigation panel expand width (WinUI NavigationView OpenPaneLength) 导航面板展开宽度
 readonly property int navPanelCompactWidth: 48 // Navigation panel compact width 导航面板折叠宽度
 readonly property int navItemHeight: 40 // Navigation item height 导航项高度
 readonly property int navItemSpacing: 4 // Navigation item spacing 导航项间距
 readonly property int navPanelPaddingV: 5 // Navigation panel vertical padding 导航面板垂直内边距
 readonly property int navPanelPaddingH: 4 // Navigation panel horizontal padding 导航面板水平内边距
 // Icon controls 图标控件
 readonly property int checkIconSize: 12 // CheckIcon/CloseIcon size 勾选/关闭图标尺寸
 readonly property int chevronIconSize: 10 // ChevronIcon size 箭头图标尺寸
 readonly property int flipViewNavButton: 28 // FlipView nav button size 翻页导航按钮尺寸
 // Table controls 表格控件
 readonly property int tableHeaderHeight: 44 // Table header height 表头高度
 readonly property int tableRowHeight: 48 // Table row height 行高
 readonly property int tablePaginationHeight: 50 // Table pagination height 分页高度
 // Feedback controls 反馈控件
 readonly property int resultStateIconSize: 80 // ResultState icon container 结果状态图标容器
 readonly property int emptyStateButtonHeight: 32 // EmptyState button height 空状态按钮高度
 readonly property int stateDescMaxWidth: 280 // StateWidget result description max width 结果描述最大宽度
 readonly property int stateDescEmptyWidth: 260 // StateWidget empty description max width 空状态描述最大宽度
 readonly property int stateButtonPaddingLarge: 32 // StateWidget result button padding 结果按钮内边距
 readonly property int stateButtonPaddingSmall: 24 // StateWidget empty button padding 空状态按钮内边距
 readonly property int flyoutIconSize: 36 // Flyout icon container 弹出层图标容器
 readonly property int flyoutCloseSize: 32 // Flyout close button 弹出层关闭按钮
 // Input controls 输入控件
 readonly property int pinBoxCellSize: 44 // PinInput cell size PIN输入框单元格尺寸
 readonly property int shortcutKeyHeight: 26 // ShortcutEditor key height 快捷键高度
 readonly property int shortcutKeyMinWidth: 36 // ShortcutEditor key min width 快捷键最小宽度
 readonly property int shortcutKeyMaxWidth: 50 // ShortcutEditor key max width 快捷键最大宽度
 readonly property int shortcutPickerMinWidth: 180 // ShortcutEditor min width 快捷键选择器最小宽度
 readonly property int closeButtonSize: 28 // CloseButton default size 关闭按钮默认尺寸
 readonly property int lineEditClearButtonSize: 20 // LineEdit clear button size 单行输入清除按钮尺寸
 readonly property int lineEditLabelWidth: 250 // Floating-label LineEdit default width 浮动标签输入框默认宽度
 readonly property int lineEditTagWidth: 300 // Tag LineEdit default width 标签输入框默认宽度
 readonly property int focusLineHeight: 10 // FocusLine height 焦点线高度
 readonly property int wheelPickerItemHeight: 34 // CycleWheelPicker item height 滚轮选择器项高度
 readonly property int wheelPickerRowHeight: 36 // CycleWheelPicker row height 滚轮选择器行高（与 calendarGridHeight 36×6=216 对齐）
 readonly property int wheelPickerAreaHeight: 216 // CycleWheelPicker wheel area height 滚轮区域高度（6 行 × 36px）
 readonly property int wheelPickerMaxFlickVelocity: 800 // Wheel picker maximum flick velocity 滚轮选择器最大甩动速度
 readonly property int wheelPickerFlickDeceleration: 1500 // Wheel picker flick deceleration 滚轮选择器甩动减速度
 readonly property int datePickerWidth: 280 // DatePicker width 日期选择器宽度
 // Chart controls 图表控件
 readonly property int chartLegendWidth: 110 // Chart legend width 图表图例宽度
 readonly property int chartLabelWidth: 90 // Chart label width 图表标签宽度
 readonly property int chartYAxisWidth: 40 // Chart Y-axis minimum width 图表Y轴最小宽度
 readonly property int chartYAxisMaxWidth: 180 // Chart Y-axis automatic maximum width 图表Y轴自动最大宽度
 readonly property int chartXAxisHeight: 25 // Chart X-axis height 图表X轴高度
 readonly property int chartDataZoomDefaultWidth: 400 // Chart data zoom default width 图表数据缩放器默认宽度
 readonly property int chartDataZoomDefaultHeight: 60 // Chart data zoom default height 图表数据缩放器默认高度
 readonly property int chartDataZoomBarHeight: 50 // Embedded chart data zoom height 内嵌图表数据缩放器高度
 // Container controls 容器控件
 readonly property int commandBarMoreWidth: 40 // CommandBar more button width 命令栏更多按钮宽度
 readonly property int commandBarSeparatorWidth: 8 // CommandBar separator width 命令栏分隔线宽度
 readonly property int toolBoxItemHeight: 44 // Tool box item height 工具箱项高度
 readonly property int expanderIconSize: 32 // Expander icon size 展开器图标尺寸
 readonly property int countdownDigitSize: 50 // Countdown digit box size 倒计时数字框尺寸
 readonly property int scrollBarWidth: 8 // ScrollBar width 滚动条宽度
 // Dialog controls 对话框控件
 readonly property int dialogDefaultWidth: 320 // Dialog default width 对话框默认宽度
 readonly property int dialogDefaultHeight: 200 // Dialog default height 对话框默认高度
 readonly property int desktopNotificationWidth: 360 // Desktop notification width 桌面通知宽度
 // ComboBox tree controls 下拉树控件
 readonly property int treeIndentSize: 16 // Tree indent/icon size 树形缩进/图标尺寸
 readonly property int treeCheckboxSize: 18 // Tree checkbox size 树形复选框尺寸
 readonly property int treeItemHeight: 36 // Tree item height 树形项高度
 readonly property int treeIndicatorMargin: 17 // Tree indicator vertical margin 树形指示条垂直边距
 // Calendar controls 日历控件
 readonly property int calendarNavButtonSize: 32 // Calendar nav button size 日历导航按钮尺寸
 readonly property int calendarPopupWidth: 280 // Calendar popup width 日历弹出宽度
 readonly property int calendarGridHeight: 216 // Calendar grid height (36*6) 日历网格高度
 readonly property int calendarPickerWidth: 180 // Single calendar picker width 单日期选择器宽度
 readonly property int calendarPickerRangeWidth: 220 // Range calendar picker width 日期范围选择器宽度
 // Step controls 步骤控件
 readonly property int stepConnectorWidth: 60 // Step connector width 步骤连接线宽度
 // Edit button controls 编辑按钮控件
 readonly property int editButtonWidth: 60 // Edit button width 编辑按钮宽度
 // Progress controls 进度控件
 readonly property int progressRingSize: 96 // Determinate ring default size 确定环默认尺寸
 readonly property int indeterminateRingSize: 72 // Indeterminate ring default size 不确定环默认尺寸
 readonly property int progressRingStroke: 5 // Determinate ring stroke width 确定环线宽
 readonly property int progressBarHeight: 4 // ProgressBar height 进度条高度
 readonly property int progressStrokeWidth: 4 // Progress stroke width 进度线宽
 // QRCode controls 二维码控件
 readonly property int qrcodeSize: 128 // QRCode default size 二维码默认尺寸
 // State widget controls 状态组件控件
 readonly property int stateImageSize: 96 // StateWidget image size 状态组件图片尺寸
 // Default component sizes 默认组件尺寸
 readonly property int chartDefaultWidth: 400 // Chart default width 图表默认宽度
 readonly property int chartDefaultHeight: 300 // Chart default height 图表默认高度
 readonly property int listDefaultWidth: 200 // List default width 列表默认宽度
 readonly property int listDefaultHeight: 300 // List default height 列表默认高度
 readonly property int listItemHeight: 36 // List item height 列表项高度(与 Tree/Table 统一)
 readonly property int listRevealDiameter: 120 // List item reveal highlight diameter 列表项悬浮光晕直径
 readonly property int tableDefaultWidth: 400 // Table default width 表格默认宽度
 readonly property int tableDefaultHeight: 300 // Table default height 表格默认高度
 readonly property int treeDefaultWidth: 300 // Tree default width 树形默认宽度
 readonly property int treeDefaultHeight: 400 // Tree default height 树形默认高度
 readonly property int carouselDefaultWidth: 400 // Carousel default width 轮播默认宽度
 readonly property int carouselDefaultHeight: 200 // Carousel default height 轮播默认高度
 readonly property int countdownHeight: 60 // Countdown height 倒计时高度
 readonly property int resultStateWidth: 300 // ResultState width 结果状态宽度
 // Navigation controls 导航控件
 readonly property int navFilledItemWidth: 256 // NavigationFilledItem width 填充导航项宽度
 readonly property int popUpOffset: 80 // PopUp animation offset 弹出动画偏移量（8倍数对齐）
 // Picker controls 选择器控件
 readonly property int timePickerWidth: 280 // TimePicker width 时间选择器宽度
 readonly property int timePickerCompactWidth: 200 // TimePicker compact width 紧凑时间选择器宽度
 readonly property int spinBoxWidth: 130 // SpinBox width 数字输入框宽度
 readonly property int spinBoxCompactWidth: 80 // SpinBox compact width 紧凑数字输入框宽度
 readonly property int spinBoxCompactDoubleExtraWidth: 10 // Extra width for compact decimals 紧凑小数微调框额外宽度
 // Menu controls 菜单控件
 readonly property int menuMinWidth: 160 // Menu minimum width 菜单最小宽度
 readonly property int menuSeparatorHeight: 8 // Menu separator height 菜单分隔线高度 (8px 网格对齐)
 // Tooltip controls 提示控件
 readonly property int tooltipWidth: 200 // Tooltip width 提示宽度
 readonly property int teachingTipWidth: 280 // TeachingTip width 教学提示宽度
 readonly property int teachingTipHeight: 120 // TeachingTip height 教学提示高度
 // Calendar popup controls 日历弹窗控件
 readonly property int calendarPopupHeight: 300 // Calendar popup height 日历弹窗高度（统一高度）
 }

 // ==================== Window 窗口度量 ====================
 readonly property QtObject window: QtObject {
 readonly property int defaultWidth: 960
 readonly property int defaultHeight: 780
 readonly property int minimumWidth: 500
 readonly property int minimumHeight: 400
 readonly property int titleBarHeight: 48
 readonly property int captionButtonHeight: 32
 readonly property int captionButtonWidth: 48
 readonly property int titleBarLeftMargin: 12
 readonly property int qmlShadowSize: 16
 readonly property int titleIconSize: 18
 readonly property int captionIconSize: 10
 readonly property int titleIconGap: 8
 readonly property int resizeEdge: 8
 readonly property int resizeCorner: 16
 readonly property int iconDeferredLoadDelayMs: 1 // Deferred window-icon source activation delay 窗口图标源延迟激活时间
 readonly property int resizeHandlesDelayMs: 1200 // Deferred resize-handle load delay 调整大小手柄延迟加载时间
 readonly property int splitStartupDelayMs: 50 // Split-window core loader startup delay 分栏窗口核心加载器启动延迟
 readonly property int micaReapplyDelayMs: 16 // First Mica reapply delay after visibility change 可见性变化后的首次 Mica 重应用延迟
 readonly property int micaLateReapplyDelayMs: 180 // Late Mica reapply fallback delay Mica 延迟重应用兜底时间
 readonly property int navPanelMinWidth: 200 // Split-window left panel min width 左侧面板最小宽度
 readonly property int iconRenderSize: 256 // Icon render size for crisp SVG (fixed high-res) 图标渲染尺寸（固定高分辨率）
 }

 // ==================== Popup 弹出窗口度量 ====================
 readonly property QtObject popup: QtObject {
 readonly property int defaultSize: 200 // Default panel size 默认面板尺寸
 readonly property int windowPadding: 16
 readonly property int panelOffset: 8
 readonly property int minWidth: 64
 readonly property int minHeight: 32
 readonly property int controlGap: 2
 readonly property int positionEpsilon: 1
 readonly property int showAnimDelayMs: 16
 readonly property int hideDelayMs: 150
 readonly property int closingDelayMs: 150
 readonly property int pickerRowCount: 4
 // Animation params - Show 显示动画参数
 readonly property int showOpacityDuration: 120 // Popup fade-in duration 弹层淡入时长
 readonly property int showRevealDuration: 240 // Popup plane reveal duration 弹层平面显现时长
 // Blur params 模糊参数
 readonly property real blurFrom: 0.3 // Initial blur 初始模糊
 readonly property real blurMid: 0.1 // Mid blur 中间模糊
 readonly property int blurMax: 16 // Max blur radius 最大模糊半径
 readonly property real blurMultiplier: 1.0 // Blur multiplier 模糊倍数
 // Animation params - Hide 隐藏动画参数
 readonly property int hideOpacityDuration: 100 // Popup fade-out duration 弹层淡出时长
 readonly property int hideRevealDuration: 110 // Popup plane hide duration 弹层平面收回时长
 }

 // ==================== InfoBar 信息条度量 ====================
 readonly property QtObject infoBar: QtObject {
 readonly property int height: 48
 readonly property int iconContainerSize: 36
 readonly property int iconSize: 16
 readonly property int closeButtonSize: 36
 readonly property int closeIconSize: 12
 readonly property int closeRadius: 5
 readonly property int margin: 8
 readonly property int textLeftGap: 2
 readonly property int textRightMargin: 12
 readonly property int textSpacing: 8
 readonly property real hideScale: 0.95
 readonly property int hideDelayMs: 200
 }

 // ==================== ComboBox 下拉框度量 ====================
 readonly property QtObject comboBox: QtObject {
 readonly property int defaultWidth: 180
 readonly property int arrowAreaWidth: 40
 readonly property int popupDefaultHeight: 200
 readonly property int popupMaxHeight: 300
 readonly property int popupDefaultMaxItems: 9
 readonly property int itemHeight: 32
 readonly property int popupPadding: 8
 readonly property int scrollBarWidth: 6
 readonly property int scrollBarRightMargin: 8
 readonly property int minPopupWidth: 120
 readonly property int searchBoxHeight: 44
 readonly property int treePopupMinWidth: 280
 readonly property int treePopupHeight: 350
 }

 // ==================== Search 搜索度量 ====================
 readonly property QtObject search: QtObject {
 readonly property int popupAnchoredMinWidth: 240
 readonly property int popupCenteredWidth: 600
 readonly property int popupFallbackHeight: 56
 readonly property int resultListWidth: 360
 readonly property int resultEmptyHeight: 60
 readonly property int resultItemHeight: 48
 readonly property int resultIconSize: 18
 readonly property int resultIndicatorWidth: 3
 }

 // ==================== Skeleton 骨架屏度量 ====================
 readonly property QtObject skeletonMetrics: QtObject {
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
 }

 // ==================== ImageCropperDialog 裁剪窗口度量 ====================
 readonly property QtObject imageCropperDialog: QtObject {
 readonly property int previewWidth: 120
 readonly property int previewHeight: 80
 readonly property real cropRectDefaultX: 0.1
 readonly property real cropRectDefaultY: 0.1
 readonly property real cropRectDefaultW: 0.8
 readonly property real cropRectDefaultH: 0.8
 readonly property int panelWidth: 640 // Unified panel size 统一面板尺寸
 readonly property int panelHeight: 480
 readonly property int bottomToolbarHeight: 48
 readonly property int bottomToolbarWidthPadding: 40
 readonly property int bottomToolbarBottomMargin: 0
 readonly property int toolbarContentGap: 18 // Gap between toolbar and content 工具栏与内容间距
 readonly property int containerBottomMargin: 66 // bottomToolbarHeight + toolbarContentGap

 readonly property int cropBorderWidth: 2
 readonly property int cropMoveMargin: 20
 readonly property int handleSize: 14
 readonly property int handleRadius: 7
 readonly property int handleCount: 4
 readonly property int handleOffset: 7
 readonly property int handleOuterMargin: -3
 readonly property int handleHitMargin: -8
 readonly property real handleShadowAlpha: 0.3

 readonly property real wheelZoomIn: 1.1
 readonly property real wheelZoomOut: 0.9
 readonly property int minCropSize: 60
 readonly property int toolButtonSize: 40
 readonly property int toolButtonIconSize: 18
 readonly property real toolButtonHoverAlpha: 0.1
 readonly property int toolTipOffset: 8
 readonly property int dividerWidth: 1
 readonly property int dividerHeight: 28
 }

 // ==================== SplashScreen 启动画面度量 ====================
 readonly property QtObject splashScreen: QtObject {
 readonly property int iconSize: root.controlSize.progressRingSize + root.spacing.s
 readonly property real iconShadowBlur: 0.8
 readonly property int iconShadowOffset: root.spacing.s
 readonly property real iconBreatheMinScale: 0.9
 readonly property real iconBreatheMaxScale: 1.1
 readonly property int progressRingSize: root.iconSize.xl
 readonly property real progressRingBorderWidth: root.border.normal
 readonly property real progressTrackOpacity: root.opacity.light
 readonly property int progressDotSize: root.progressRing.orbitDotSize
 readonly property int progressDotRadius: root.progressRing.orbitDotRadius
 readonly property int progressDotTopMargin: root.progressRing.orbitDotTopMargin
 }

 // ==================== LazyLoadingTransition 懒加载过渡度量 ====================
 readonly property QtObject lazyLoadingTransition: QtObject {
 // Circle collapse duration, shared by page switch and window exit. Measured on
 // a real presenting display: page switch and window exit produce identical
 // pacing here, so one value serves both.
 // 圆形收紧时长, 页面切换与窗口退场共用。真机实测: 两者节奏完全相同, 故共用一值。
 readonly property int coverDuration: 420
 // Loading indicator visible time between collapse end and Loader activation.
 // Callers derive lazyActivationDelay as coverDuration + this, so changing the
 // collapse duration no longer silently squeezes the indicator to nothing.
 // 收紧结束到 Loader 激活之间, 加载指示器的可见时间。调用方用 coverDuration 加
 // 此值推出 lazyActivationDelay, 因此改收紧时长不会再把指示器静默压到零。
 readonly property int loaderActivationHeadroom: 100
 readonly property int revealDuration: 500 // Target page circle expansion 目标页面圆形展开时长
 readonly property int splashRevealDuration: 1000 // Splash entrance reveal duration 启动画面入场揭幕时长
 readonly property real edgeSoftness: 1.5 // Circular mask antialiasing width 圆形遮罩抗锯齿宽度
 readonly property real breatheMinScale: 0.97 // Waiting ring minimum breathe scale 等待圆环最小呼吸缩放
 readonly property real breatheMaxScale: 1.03 // Waiting ring maximum breathe scale 等待圆环最大呼吸缩放
 readonly property int breatheHalfDuration: root.duration.crossFade // Waiting ring half breathe cycle 等待圆环半程呼吸时长
 }

 // ==================== ProgressRing 进度环度量 ====================
 readonly property QtObject progressRing: QtObject {
 readonly property int spinDuration: 800 // Default progress ring rotation cycle 默认进度环旋转周期
 readonly property int fixedArcSweep: 90 // Legacy lazy-loading quarter arc 原懒加载四分之一圆弧
 readonly property int orbitDotSize: root.spacing.s // Orbiting dot size 绕圈圆点尺寸
 readonly property int orbitDotRadius: root.radius.tiny
 readonly property int orbitDotTopMargin: -root.spacing.micro // Orbiting dot offset 绕圈圆点偏移
 }

 // ==================== ColorPicker 颜色选择器度量 ====================
 readonly property QtObject colorPicker: QtObject {
 // Trigger button 触发按钮
 readonly property int triggerWidth: 56 // Trigger button width 触发按钮宽度
 
 // Palette
 readonly property int paletteCellSize: 28
 readonly property int paletteCellSpacing: 4
 readonly property int paletteColumns: 10
 readonly property int palettePreviewSize: 28
 readonly property int paletteSelectedBorderWidth: 2

 // Circle swatches 圆形色块
 readonly property int circleDefaultSize: 28
 readonly property real circleHoverOpacity: 0.8
 readonly property int circleLoaderFallbackWidth: 0

 // Public popup sizing 公开弹层尺寸
 readonly property int palettePopupWidth: 360
 readonly property int pickerPopupWidth: 320
 readonly property int fallbackPopupWidth: 300
 readonly property int palettePopupHeight: 370
 readonly property int pickerPopupHeight: 480
 readonly property int fallbackPopupHeight: 400

 // Channel slider
 readonly property int channelSliderWidth: 260
 readonly property int channelSliderHeight: 24
 readonly property int channelLabelWidth: 16
 readonly property int channelInputWidth: 48
 readonly property int channelInputFocusedBorderWidth: 2
 readonly property int channelInputBorderWidth: 1
 readonly property int channelMinValue: 0
 readonly property int channelMaxValue: 255
 readonly property int channelAlphaIndex: 3
 readonly property int channelShowInputWidth: 90
 readonly property int channelHideInputWidth: 40
 readonly property int checkerboardCellSize: 6
 readonly property int checkerboardParity: 2
 readonly property int handleBorderWidth: 2

 // Hue slider
 readonly property int hueSliderWidth: 260
 readonly property int hueTrackHeight: 12
 readonly property int hueHandleSize: 16
 readonly property int hueHandleBorderWidth: 2
 readonly property int hueHandleInnerPadding: 6
 readonly property real hueValueDefault: 0.5
 readonly property real hueUpdateEpsilon: 0.001

 // Brightness slider
 readonly property int brightnessSliderWidth: 260
 readonly property int brightnessTrackHeight: 12
 readonly property int brightnessHandleSize: 16
 readonly property int brightnessHandleInnerPadding: 6
 readonly property real brightnessValueDefault: 1.0
 readonly property real brightnessUpdateEpsilon: 0.001

 // Panel rendering 面板渲染
 readonly property int panelDefaultHeight: 200
 readonly property int panelCanvasColumnWidth: 1
 readonly property real panelSelectorLuminanceFactor: 0.5
 readonly property real panelSelectorLuminanceThreshold: 0.5

 // Dialog layout 对话框布局
 readonly property int dialogContentWidth: 392
 readonly property int dialogPanelSize: 260
 readonly property int dialogBrightnessHeight: 22
 readonly property int dialogBrightnessHandleSize: 18
 readonly property int dialogPreviewWidth: 46
 readonly property int dialogPreviewHeight: 126

 readonly property int dialogInputWidth: 138
 readonly property int dialogInputHeight: 32
 readonly property int dialogHexPrefixX: 8
 readonly property int dialogHexInputLeftMargin: 20
 readonly property int dialogHexMaxLength: 6
 readonly property int dialogCustomRowSpacing: 60

 // Dialog defaults and constants
 readonly property real dialogHueDefault: 0.5
 readonly property real dialogSaturationDefault: 1.0
 readonly property real dialogBrightnessDefault: 1.0
 readonly property int dialogAlphaDefault: 255
 readonly property int dialogRgbChannelR: 0
 readonly property int dialogRgbChannelG: 1
 readonly property int dialogRgbChannelB: 2
 readonly property int dialogHexStartIndex: 1
 readonly property int dialogHexSubstringLength: 6
 readonly property string dialogHexPrefix: "#"
 readonly property int dialogAlphaMaxValue: 255
 readonly property int dialogHexRegexMaxLen: 6
 readonly property int dialogHexRegexExactLen: 6

 // Dropdown content
 readonly property int dropdownWidth: 300
 readonly property int dropdownPanelHeight: 220
 readonly property int dropdownModeWidth: 80
 readonly property int dropdownHexGap: 92
 readonly property int dropdownSeparatorHeight: 1
 readonly property int dropdownModeCycleCount: 3
 readonly property int dropdownModeCycleStep: 1
 readonly property string dropdownArrowText: "∨"

 // Inputs component
 readonly property int inputsWidth: 260
 readonly property int inputsModeWidth: 72
 readonly property int inputsHexWidth: 80
 readonly property int inputsModeArrowFontOffset: 4

 // Hex formatting/parse helpers
 readonly property int hexByteLen: 2
 readonly property int hexRgbLen: 6
 readonly property int hexRgbaLen: 8
 readonly property int hexAlphaOffset: 2
 readonly property int hexRadix: 16
 readonly property string hexPadCharacter: "0"
 }
 
 // ==================== Typography 字体 ====================
 readonly property QtObject typography: QtObject {
 readonly property int tiny: 8 // Timeline card icon text 时间线卡片图标文字
 readonly property int micro: 10 // Timeline icon text 时间线图标文字
 readonly property int captionCompact: 11 // Compact caption text 紧凑说明文字
 readonly property int caption: 12
 readonly property int bodySmall: 13
 readonly property int body: 14
 readonly property int bodyLarge: 15
 readonly property int subtitle: 16
 readonly property int title: 18
 readonly property int titleLarge: 20
 readonly property int display: 24
 readonly property int displayLarge: 28
 readonly property int metric: 32
 readonly property int hero: 36
 readonly property int giant: 40
 readonly property int mega: 68
 }
 
  // ==================== Shadow 阴影 ====================
  // Shadow levels keep their public Enums.shadow object shape while the
  // skin-dependent implementation lives in a dedicated owner.
  readonly property QtObject shadow: MetricsInternal.MetricsShadow {
  isDark: root.isDark
  isTicket: root.isTicket
  }

 readonly property QtObject demoMetrics: QtObject {
 readonly property int carouselInterval: 2500
 readonly property int feedbackNotificationWidth: 320 // Gallery notification showcase width Gallery 通知展示宽度
 readonly property real feedbackProgressBarStep: 0.05 // Gallery progress bar step Gallery 进度条步长
 readonly property real feedbackProgressRingStep: 0.03 // Gallery progress ring step Gallery 进度环步长
 readonly property int feedbackProgressRingInterval: 80 // Gallery progress ring tick Gallery 进度环更新间隔
 readonly property int qrcodeModuleSize: 3
 readonly property int ratingDefaultValue: 3
 readonly property real pieChartInnerRadius: 0.6
 readonly property int countdownDurationMs: 3600000
 readonly property int flipViewAutoPlayIntervalMs: 3000
 readonly property int scrollBarMargin: 10
 readonly property int scrollBarThickness: 6
 readonly property real scrollWheelFactor: 0.8
 readonly property int gapLarge: 32
 readonly property int infiniteDuration: -1
 readonly property int toolTipFontSize: 11
 }
 
 // ==================== List Indicator 列表指示条 ====================
 readonly property QtObject listIndicator: QtObject {
 // 列表项选中指示条的度量参数(按下/选中态的高度比例与圆角)

 // Height ratio when pressed 按下时高度比例
 readonly property real pressedRatio: 0.36
 // Height ratio when normal 正常时高度比例
 readonly property real normalRatio: 0.3
 }

 // ==================== Navigation 导航 ====================
 // 侧边栏溢出提示度量拆到 _internal, 保持本文件在体积门禁之内。
 // Sidebar overflow hint metrics live in _internal to stay under the size gate.
 readonly property QtObject navigation: MetricsInternal.MetricsNavigation {
  opacityScale: root.opacity
  durationScale: root.duration
  railInset: root.spacing.xxs
  railBarWidth: root.controlSize.scrollBarWidth
 }
 // alias 只能穿透一层 id, 两层属性路径会被拒绝, 因此这里用绑定而非 alias。
 // An alias cannot walk a two-level property path, so bind instead of aliasing.
 readonly property QtObject navigationFade: root.navigation.fade
 readonly property QtObject navigationRail: root.navigation.rail
}
