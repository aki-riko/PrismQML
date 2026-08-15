// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as DatePickerInternal

// CalendarPickerCore - Calendar grid layout base 日历网格布局基类
// Used standalone or embedded in CalendarPicker 可单独使用或嵌入CalendarPicker
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int year: new Date().getFullYear()
    property int month: new Date().getMonth() + 1
    property int day: 0  // Selected day 选中的日期，0表示未选中
    property color accentColor: Enums.accentColor
    property var weekDays: {
        Translator._v
        return [
            Translator.tr("sunday"), Translator.tr("monday"),
            Translator.tr("tuesday"), Translator.tr("wednesday"),
            Translator.tr("thursday"), Translator.tr("friday"),
            Translator.tr("saturday")
        ]
    }
    property string monthFormat: {
        Translator._v
        return Translator.tr("calendar_month_format")
    }
    
    // Range mode props 范围模式属性
    property bool rangeMode: false
    property var rangeStart: null  // Date or null
    property var rangeEnd: null    // Date or null
    
    // ==================== Internal Props 内部属性 ====================
    // Animation props 动画属性
    property bool _animating: false
    property int _slideDirection: 0  // -1: up (prev), 1: down (next)

    // Next month data for seamless scroll 下月数据用于无缝滚动
    property int _nextYear: year
    property int _nextMonth: month
    property var _pendingUpdateFunc: null
    property bool _nextGridRequested: false

    // ==================== Readonly State 只读状态 ====================
    // Range bar color (opaque to avoid overlap issues) 范围条颜色（不透明避免重叠问题）
    readonly property color _rangeBarColor: Enums.isDark ? Enums.calendarColors.rangeBarDark : Enums.calendarColors.rangeBarLight
    readonly property int _nextFirstDay: new Date(_nextYear, _nextMonth - 1, 1).getDay()
    readonly property int _nextDaysInMonth: new Date(_nextYear, _nextMonth, 0).getDate()
    readonly property int _nextDaysInPrev: new Date(_nextYear, _nextMonth - 1, 0).getDate()
    readonly property int _todayYear: new Date().getFullYear()
    readonly property int _todayMonth: new Date().getMonth() + 1
    readonly property int _todayDay: new Date().getDate()
    readonly property int _firstDay: new Date(year, month - 1, 1).getDay()
    readonly property int _daysInMonth: new Date(year, month, 0).getDate()
    readonly property int _daysInPrev: new Date(year, month - 1, 0).getDate()

    // ==================== Signals 信号 ====================
    signal dayClicked(int day)
    signal dateChanged(int year, int month, int day)
    signal rangeDateClicked(date clickedDate)

    // ==================== Public Methods 公开方法 ====================
    function prevMonth() {
        if (_animating) return
        _animateSwitch(-1, function() {
            if (month === 1) { year--; month = 12 }
            else month--
        })
    }

    function nextMonth() {
        if (_animating) return
        _animateSwitch(1, function() {
            if (month === 12) { year++; month = 1 }
            else month++
        })
    }

    function setDate(y, m, d) {
        year = y
        month = Math.max(1, Math.min(12, m))
        day = d
    }

    function goToToday() {
        year = _todayYear
        month = _todayMonth
        day = _todayDay
    }

    function getDate() {
        return new Date(year, month - 1, day)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _animateSwitch(direction, updateFunc) {
        _animating = true
        _slideDirection = direction
        _pendingUpdateFunc = updateFunc

        // Calculate next month data 计算目标月份数据
        if (direction > 0) {
            // Next month 下一月
            if (month === 12) { _nextYear = year + 1; _nextMonth = 1 }
            else { _nextYear = year; _nextMonth = month + 1 }
        } else {
            // Prev month 上一月
            if (month === 1) { _nextYear = year - 1; _nextMonth = 12 }
            else { _nextYear = year; _nextMonth = month - 1 }
        }
        _nextGridRequested = true

        // Set grid positions based on direction 根据方向设置网格位置
        contentLayer.gridWrapperBehavior.enabled = false
        if (direction > 0) {
            // Down: current on top, next below 向下：当前在上，目标在下
            contentLayer.dayGrid.y = 0
            contentLayer.nextGrid.y = contentLayer.gridContainerHeight
            contentLayer.gridWrapper.y = 0
        } else {
            // Up: next on top, current below 向上：目标在上，当前在下
            contentLayer.dayGrid.y = contentLayer.gridContainerHeight
            contentLayer.nextGrid.y = 0
            contentLayer.gridWrapper.y = -contentLayer.gridContainerHeight
        }
        contentLayer.gridWrapperBehavior.enabled = true

        // Animate to show next month 动画显示目标月
        contentLayer.gridWrapper.y = direction > 0
            ? -contentLayer.gridContainerHeight : 0
        contentLayer.animationTimer.start()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: 256
    implicitHeight: contentLayer.implicitHeight
    
    DatePickerInternal.CalendarPickerContent {
        id: contentLayer
        calendarControl: control
    }
}
