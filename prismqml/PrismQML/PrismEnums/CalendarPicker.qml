// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// CalendarPicker - Calendar picker type enums 日历选择器类型枚举
QtObject {
    readonly property int type_single: 0     // Single date selection 单日期选择
    readonly property int type_range: 1      // Date range selection 日期范围选择
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
