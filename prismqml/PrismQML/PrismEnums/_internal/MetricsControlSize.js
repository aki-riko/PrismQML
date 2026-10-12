// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// MetricsControlSize - Control dimensions 控件尺寸
// Kept as plain data so the metrics namespace does not introduce another QML type.
// 使用纯数据对象，避免为度量命名空间新增 QML 类型。
function create(touchTargetFloor) {
    var floor = Math.max(0, Number(touchTargetFloor) || 0)
    return {
        touchTargetFloor: floor,

        // Toggle controls 切换控件
        radioOuter: 20,
        radioInner: 8,
        checkboxOuter: 18,
        checkboxInner: 12,
        switchWidth: 44,
        switchHeight: 24,
        switchThumb: 20,

        // Input controls 输入控件
        inputHeight: Math.max(32, floor),
        inputDefaultWidth: 200,
        inputHeightLarge: Math.max(40, floor),
        inputHeightCompact: Math.max(28, floor),
        inputHeightLabel: 56,
        textEditScrollThumbMinHeight: 20,
        inputLabelTextHeight: 24,
        pickerRow: Math.max(36, floor),

        // Navigation controls 导航控件
        navBarHeight: 48,
        navBarWidth: 68,
        navBarItemWidth: 64,
        navBarItemHeight: 60,
        bottomTabBarHeight: 56,
        tabBarHeight: Math.max(40, floor),
        tabBarVerticalWidth: 200,
        commandPaletteWidth: 560,
        commandPaletteTopRatio: 0.18,
        swipeActionWidth: 72,
        refreshPullThreshold: 64,
        refreshIndicatorSize: 28,
        segmentedHeight: Math.max(36, floor),
        segmentedMinWidth: 60,
        segmentedToolSize: Math.max(36, floor),
        selectorBarHeight: Math.max(40, floor),
        selectorBarMinItemWidth: 72,
        commandBarButtonSize: Math.max(36, floor),
        statusBarHeight: 24,

        // Feedback controls 反馈控件
        tooltipHeight: 28,
        tooltipMaxWidth: 320,
        toastWidth: 360,
        toastMaxWidth: 800,
        toastHeight: 80,

        // Chat controls 聊天控件
        chatContentMaxWidth: 600,
        codeBlockDefaultWidth: 400,
        codeBlockHeaderHeight: 24,
        codeBlockCopyButtonWidth: 50,
        codeBlockCopyButtonHeight: 22,

        // Container controls 容器控件
        cardWidth: 400,
        cardContentWidth: 300,
        cardHeight: 64,
        galleryCardLabelMaxWidth: 220,
        dropFileHeight: 140,
        splitPaneMinimumSize: 50,

        // Calendar controls 日历控件
        calendarCell: Math.max(32, floor),
        calendarCellHeight: Math.max(36, floor),

        // Timeline controls 时间线控件
        timelineIcon: 16,
        timelineCardIcon: 12,
        timelineIconText: 10,
        timelineCardIconText: 8,
        timelineGraphNode: 10,

        // Button controls 按钮控件
        closeButton: Math.max(32, floor),
        buttonMinWidth: 80,
        buttonHeight: Math.max(32, floor),
        toolButtonWidth: Math.max(36, floor),
        splitButtonArrowWidth: 26,
        splitButtonContentOffset: 13,
        dropdownArrowWidth: 20,
        dialogButtonHeight: Math.max(32, floor),

        // Navigation item controls 导航项控件
        topNavItemHeight: Math.max(36, floor),
        topNavItemPadding: 24,
        topNavIndicatorHeight: 3,
        navIndicatorHeight: 16,
        navIndicatorHeightPressed: 18,
        navIndicatorWidth: 3,
        navPanelExpandWidth: 320,
        navPanelCompactWidth: 48,
        navItemHeight: Math.max(40, floor),
        navItemSpacing: 4,
        navPanelPaddingV: 5,
        navPanelPaddingH: 4,

        // Icon controls 图标控件
        checkIconSize: 12,
        chevronIconSize: 10,
        flipViewNavButton: Math.max(28, floor),

        // Table controls 表格控件
        tableHeaderHeight: Math.max(44, floor),
        tableRowHeight: 48,
        tablePaginationHeight: 50,

        // Feedback controls 反馈控件
        resultStateIconSize: 80,
        emptyStateButtonHeight: Math.max(32, floor),
        stateDescMaxWidth: 280,
        stateDescEmptyWidth: 260,
        stateButtonPaddingLarge: 32,
        stateButtonPaddingSmall: 24,
        flyoutIconSize: 36,
        flyoutCloseSize: 32,

        // Input controls 输入控件
        pinBoxCellSize: 44,
        shortcutKeyHeight: 26,
        shortcutKeyMinWidth: 36,
        shortcutKeyMaxWidth: 50,
        shortcutPickerMinWidth: 180,
        closeButtonSize: Math.max(28, floor),
        lineEditClearButtonSize: 20,
        lineEditLabelWidth: 250,
        lineEditTagWidth: 300,
        focusLineHeight: 10,
        wheelPickerItemHeight: Math.max(34, floor),
        wheelPickerRowHeight: Math.max(36, floor),
        wheelPickerAreaHeight: 216,
        wheelPickerMaxFlickVelocity: 800,
        wheelPickerFlickDeceleration: 1500,
        datePickerWidth: 280,

        // Chart controls 图表控件
        chartLegendWidth: 110,
        chartLabelWidth: 90,
        chartYAxisWidth: 40,
        chartYAxisMaxWidth: 180,
        chartXAxisHeight: 25,
        chartDataZoomDefaultWidth: 400,
        chartDataZoomDefaultHeight: 60,
        chartDataZoomBarHeight: 50,

        // Container controls 容器控件
        commandBarMoreWidth: 40,
        commandBarSeparatorWidth: 8,
        toolBoxItemHeight: Math.max(44, floor),
        expanderIconSize: 32,
        countdownDigitSize: 50,
        scrollBarWidth: 8,

        // Dialog controls 对话框控件
        dialogDefaultWidth: 320,
        dialogDefaultHeight: 200,
        desktopNotificationWidth: 360,

        // ComboBox tree controls 下拉树控件
        treeIndentSize: 16,
        treeCheckboxSize: 18,
        treeItemHeight: Math.max(36, floor),
        treeIndicatorMargin: 17,

        // Calendar controls 日历控件
        calendarNavButtonSize: 32,
        calendarPopupWidth: 280,
        calendarGridHeight: 216,
        calendarPickerWidth: 180,
        calendarPickerRangeWidth: 220,

        // Step and edit controls 步骤与编辑控件
        stepConnectorWidth: 60,
        editButtonWidth: 60,

        // Progress and QR controls 进度与二维码控件
        progressRingSize: 96,
        indeterminateRingSize: 72,
        progressRingStroke: 5,
        progressBarHeight: 4,
        progressStrokeWidth: 4,
        qrcodeSize: 128,

        // State and default component sizes 状态与默认组件尺寸
        stateImageSize: 96,
        chartDefaultWidth: 400,
        chartDefaultHeight: 300,
        listDefaultWidth: 200,
        listDefaultHeight: 300,
        listItemHeight: Math.max(36, floor),
        listRevealDiameter: 120,
        tableDefaultWidth: 400,
        tableDefaultHeight: 300,
        treeDefaultWidth: 300,
        treeDefaultHeight: 400,
        carouselDefaultWidth: 400,
        carouselDefaultHeight: 200,
        countdownHeight: 60,
        resultStateWidth: 300,

        // Navigation and picker controls 导航与选择器控件
        navFilledItemWidth: 256,
        popUpOffset: 80,
        timePickerWidth: 280,
        timePickerCompactWidth: 200,
        spinBoxWidth: 130,
        spinBoxCompactWidth: 80,
        spinBoxCompactDoubleExtraWidth: 10,

        // Menu and tooltip controls 菜单与提示控件
        menuMinWidth: 160,
        menuSeparatorHeight: 8,
        tooltipWidth: 200,
        teachingTipWidth: 280,
        teachingTipHeight: 120,
        calendarPopupHeight: 300
    }
}
