// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// CalendarPicker - Calendar picker type enums 日历选择器类型枚举
QtObject {
    readonly property int type_single: 0     // Single date selection 单日期选择
    readonly property int type_range: 1      // Date range selection 日期范围选择
    // Display modes 显示模式
    readonly property int display_month: 0   // Day grid 日期网格
    readonly property int display_year: 1    // Month grid 月份网格
    readonly property int display_decade: 2  // Year grid 年份网格
    // Selection modes 选择模式
    readonly property int selection_single: 0    // One day 单选一天
    readonly property int selection_multiple: 1  // Many days 多选多天
    readonly property int selection_range: 2     // Continuous range 连续区间
    // Period grid sizing 周期网格尺寸
    readonly property int monthsPerYear: 12
    readonly property int yearsPerDecade: 10
    readonly property int periodGridColumns: 3
    readonly property int decadeGridColumns: 2
    // Date field limits 日期字段边界
    readonly property int noSelectionDay: 0
    readonly property int monthMinimum: 1
    readonly property int monthMaximum: 12
    readonly property int dayMinimum: 1
    readonly property int dayMaximum: 31
    readonly property int twoDigitThreshold: 10
    readonly property int dateFieldWidth: 2
    readonly property string datePadCharacter: "0"
    readonly property string dateSeparator: "-"
    readonly property string rangeSeparator: " ~ "
    // Popup animation 弹层动画
    readonly property int popupAnimationSlideDown: 1
}
