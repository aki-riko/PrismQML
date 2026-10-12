// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsControlSize - Control dimensions 控件尺寸
QtObject {
    id: controlSize

    // ==================== Required Props 必需属性 ====================
    required property int touchTargetFloor


    // Toggle controls 切换控件
    readonly property int radioOuter: 20 // Fluent Design: radius=10 → diameter=20 Fluent 规范：圆角 10 → 直径 20
    readonly property int radioInner: 8
    readonly property int checkboxOuter: 18
    readonly property int checkboxInner: 12
    readonly property int switchWidth: 44
    readonly property int switchHeight: 24
    readonly property int switchThumb: 20
    // Input controls 输入控件
    readonly property int inputHeight: Math.max(32, controlSize.touchTargetFloor) // Fluent Design standard height 标准高度（与 buttonHeight 对齐）
    readonly property int inputDefaultWidth: 200 // Input default width 输入框默认宽度
    readonly property int inputHeightLarge: Math.max(40, controlSize.touchTargetFloor)
    readonly property int inputHeightCompact: Math.max(28, controlSize.touchTargetFloor)
    readonly property int inputHeightLabel: 56 // Label input height (with floating label) 带浮动标签输入框高度
    readonly property int textEditScrollThumbMinHeight: 20 // TextEdit scroll thumb minimum height 多行文本滚动拇指最小高度
    readonly property int inputLabelTextHeight: 24 // Floating label text field height 浮动标签文本框高度
    readonly property int pickerRow: Math.max(36, controlSize.touchTargetFloor)
    // Navigation controls 导航控件
    readonly property int navBarHeight: 48 // Top navigation bar height
    readonly property int navBarWidth: 68 // NavigationBar width (64px button + 2px margins) 导航栏宽度
    readonly property int navBarItemWidth: 64 // NavigationBarItem width 导航栏项宽度
    readonly property int navBarItemHeight: 60 // NavigationBarItem height 导航栏项高度
    readonly property int bottomTabBarHeight: 56 // BottomTabBar height 底部导航栏高度
    readonly property int tabBarHeight: Math.max(40, controlSize.touchTargetFloor) // TabBar height
    readonly property int tabBarVerticalWidth: 200 // Vertical TabBar strip width 纵向标签条宽度
    readonly property int commandPaletteWidth: 560 // CommandPalette panel width 命令面板宽度
    readonly property real commandPaletteTopRatio: 0.18 // CommandPalette upper-third placement ratio 命令面板上三分之一位置比例
    readonly property int swipeActionWidth: 72 // SwipeControl revealed action width 滑动操作宽度
    readonly property int refreshPullThreshold: 64 // RefreshContainer pull distance to refresh 下拉刷新触发距离
    readonly property int refreshIndicatorSize: 28 // RefreshContainer indicator size 下拉刷新指示器尺寸
    readonly property int segmentedHeight: Math.max(36, controlSize.touchTargetFloor) // SegmentedControl height
    readonly property int segmentedMinWidth: 60 // SegmentedControl item min width 分段项最小宽度
    readonly property int segmentedToolSize: Math.max(36, controlSize.touchTargetFloor) // Segmented tool item size 分段工具项尺寸
    readonly property int selectorBarHeight: Math.max(40, controlSize.touchTargetFloor) // SelectorBar height 选择条高度
    readonly property int selectorBarMinItemWidth: 72 // SelectorBar item min width 选择条项最小宽度
    readonly property int commandBarButtonSize: Math.max(36, controlSize.touchTargetFloor) // CommandBar button size (square) 命令栏按钮尺寸（正方形）
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
    readonly property int galleryCardLabelMaxWidth: 220 // Gallery example label max width 画廊示例标签最大宽度
    readonly property int dropFileHeight: 140 // DropZone default height 拖放组件默认高度
    readonly property int splitPaneMinimumSize: 50 // SplitPane pane minimum extent 分割面板最小范围
    // Calendar controls 日历控件
    readonly property int calendarCell: Math.max(32, controlSize.touchTargetFloor) // Calendar day cell size 日历日期单元格尺寸
    readonly property int calendarCellHeight: Math.max(36, controlSize.touchTargetFloor) // Calendar cell row height 日历单元格行高
    // Timeline controls 时间线控件
    // Keep (timelineIcon - timelineIconText) even so anchors.centerIn resolves to a
    // whole-pixel gap. An odd difference makes Qt round the anchor center and offsets
    // the glyph by half a logical pixel, which grows to 1.25px at 150% scaling.
    // 保持 (timelineIcon - timelineIconText) 为偶数, 使 anchors.centerIn 得到整数间距。
    // 差值为奇数时 Qt 会对锚点中心取整, 图标偏移半个逻辑像素, 在 150% 缩放下放大到 1.25px。
    readonly property int timelineIcon: 16 // Timeline group icon size 时间线分组图标尺寸
    readonly property int timelineCardIcon: 12 // Timeline card icon size 时间线卡片图标尺寸
    readonly property int timelineIconText: 10 // Timeline icon inner text size 时间线图标内文字尺寸
    readonly property int timelineCardIconText: 8 // Timeline card icon inner text size 时间线卡片图标内文字尺寸
    readonly property int timelineGraphNode: 10 // Timeline graph commit node size 时间线图提交节点尺寸
    // Button controls 按钮控件
    readonly property int closeButton: Math.max(32, controlSize.touchTargetFloor) // Close button size 关闭按钮尺寸
    readonly property int buttonMinWidth: 80 // Button minimum width 按钮最小宽度
    readonly property int buttonHeight: Math.max(32, controlSize.touchTargetFloor) // Button height 按钮高度
    readonly property int toolButtonWidth: Math.max(36, controlSize.touchTargetFloor) // ToolButton width 工具按钮宽度
    readonly property int splitButtonArrowWidth: 26 // Split button arrow area width 分割按钮箭头区域宽度
    readonly property int splitButtonContentOffset: 13 // Split button content offset 分割按钮内容偏移
    readonly property int dropdownArrowWidth: 20 // Dropdown button arrow width 下拉按钮箭头宽度
    // Dialog controls 对话框控件
    readonly property int dialogButtonHeight: Math.max(32, controlSize.touchTargetFloor) // Dialog button height 对话框按钮高度
    // Navigation item controls 导航项控件
    readonly property int topNavItemHeight: Math.max(36, controlSize.touchTargetFloor) // top-nav window nav item height 顶部导航项高度
    readonly property int topNavItemPadding: 24 // top-nav window nav item padding 顶部导航项内边距
    readonly property int topNavIndicatorHeight: 3 // top-nav window indicator height 顶部导航指示条高度
    readonly property int navIndicatorHeight: 16 // Navigation indicator height 导航指示条高度
    readonly property int navIndicatorHeightPressed: 18 // Navigation indicator height when pressed 按下时导航指示条高度
    readonly property int navIndicatorWidth: 3 // Navigation indicator width 导航指示条宽度
    readonly property int navPanelExpandWidth: 320 // Navigation panel expand width (WinUI NavigationView OpenPaneLength) 导航面板展开宽度
    readonly property int navPanelCompactWidth: 48 // Navigation panel compact width 导航面板折叠宽度
    readonly property int navItemHeight: Math.max(40, controlSize.touchTargetFloor) // Navigation item height 导航项高度
    readonly property int navItemSpacing: 4 // Navigation item spacing 导航项间距
    readonly property int navPanelPaddingV: 5 // Navigation panel vertical padding 导航面板垂直内边距
    readonly property int navPanelPaddingH: 4 // Navigation panel horizontal padding 导航面板水平内边距
    // Icon controls 图标控件
    readonly property int checkIconSize: 12 // CheckIcon/CloseIcon size 勾选/关闭图标尺寸
    readonly property int chevronIconSize: 10 // ChevronIcon size 箭头图标尺寸
    readonly property int flipViewNavButton: Math.max(28, controlSize.touchTargetFloor) // FlipView nav button size 翻页导航按钮尺寸
    // Table controls 表格控件
    readonly property int tableHeaderHeight: Math.max(44, controlSize.touchTargetFloor) // Table header height 表头高度
    readonly property int tableRowHeight: 48 // Table row height 行高
    readonly property int tablePaginationHeight: 50 // Table pagination height 分页高度
    // Feedback controls 反馈控件
    readonly property int resultStateIconSize: 80 // ResultState icon container 结果状态图标容器
    readonly property int emptyStateButtonHeight: Math.max(32, controlSize.touchTargetFloor) // StateWidget empty button height StateWidget 空状态按钮高度
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
    readonly property int closeButtonSize: Math.max(28, controlSize.touchTargetFloor) // CloseButton default size 关闭按钮默认尺寸
    readonly property int lineEditClearButtonSize: 20 // LineEdit clear button size 单行输入清除按钮尺寸
    readonly property int lineEditLabelWidth: 250 // Floating-label LineEdit default width 浮动标签输入框默认宽度
    readonly property int lineEditTagWidth: 300 // Tag LineEdit default width 标签输入框默认宽度
    readonly property int focusLineHeight: 10 // FocusLine height 焦点线高度
    readonly property int wheelPickerItemHeight: Math.max(34, controlSize.touchTargetFloor) // CycleWheelPicker item height 滚轮选择器项高度
    readonly property int wheelPickerRowHeight: Math.max(36, controlSize.touchTargetFloor) // CycleWheelPicker row height 滚轮选择器行高（与 calendarGridHeight 36×6=216 对齐）
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
    readonly property int toolBoxItemHeight: Math.max(44, controlSize.touchTargetFloor) // Tool box item height 工具箱项高度
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
    readonly property int treeItemHeight: Math.max(36, controlSize.touchTargetFloor) // Tree item height 树形项高度
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
    readonly property int listItemHeight: Math.max(36, controlSize.touchTargetFloor) // List item height 列表项高度(与 Tree/Table 统一)
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
