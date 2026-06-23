// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "_internal"
import "../../data"

// CalendarPickerCore - Calendar grid layout base 日历网格布局基类
// Used standalone or embedded in CalendarPicker 可单独使用或嵌入CalendarPicker
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int year: new Date().getFullYear()
    property int month: new Date().getMonth() + 1
    property int day: 0  // Selected day 选中的日期，0表示未选中
    property color accentColor: Enums.accentColor
    property var weekDays: ["日", "一", "二", "三", "四", "五", "六"]
    property string monthFormat: "{month}月 {year}"
    
    // Range mode props 范围模式属性
    property bool rangeMode: false
    property var rangeStart: null  // Date or null
    property var rangeEnd: null    // Date or null
    
    // Range bar color (opaque to avoid overlap issues) 范围条颜色（不透明避免重叠问题）
    readonly property color _rangeBarColor: Enums.isDark ? Enums.calendarColors.rangeBarDark : Enums.calendarColors.rangeBarLight
    
    // Animation props 动画属性
    property bool _animating: false
    property int _slideDirection: 0  // -1: up (prev), 1: down (next)
    
    // Next month data for seamless scroll 下月数据用于无缝滚动
    property int _nextYear: year
    property int _nextMonth: month
    readonly property int _nextFirstDay: new Date(_nextYear, _nextMonth - 1, 1).getDay()
    readonly property int _nextDaysInMonth: new Date(_nextYear, _nextMonth, 0).getDate()
    readonly property int _nextDaysInPrev: new Date(_nextYear, _nextMonth - 1, 0).getDate()
    
    // ==================== Signals 信号 ====================
    signal dayClicked(int day)
    signal dateChanged(int year, int month, int day)
    signal rangeDateClicked(date clickedDate)
    
    // ==================== Computed Props 计算属性 ====================
    readonly property int _todayYear: new Date().getFullYear()
    readonly property int _todayMonth: new Date().getMonth() + 1
    readonly property int _todayDay: new Date().getDate()
    readonly property int _firstDay: new Date(year, month - 1, 1).getDay()
    readonly property int _daysInMonth: new Date(year, month, 0).getDate()
    readonly property int _daysInPrev: new Date(year, month - 1, 0).getDate()

    property var _pendingUpdateFunc: null

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

    // Internal animation helper 内部动画辅助函数
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

        // Set grid positions based on direction 根据方向设置网格位置
        gridWrapperBehavior.enabled = false
        if (direction > 0) {
            // Down: current on top, next below 向下：当前在上，目标在下
            dayGrid.y = 0
            nextGrid.y = gridContainer.height
            gridWrapper.y = 0
        } else {
            // Up: next on top, current below 向上：目标在上，当前在下
            dayGrid.y = gridContainer.height
            nextGrid.y = 0
            gridWrapper.y = -gridContainer.height
        }
        gridWrapperBehavior.enabled = true

        // Animate to show next month 动画显示目标月
        gridWrapper.y = direction > 0 ? -gridContainer.height : 0
        animationTimer.start()
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

    // ==================== Size 尺寸 ====================
    implicitWidth: 256
    implicitHeight: mainColumn.implicitHeight
    
    Column {
        id: mainColumn
        anchors.fill: parent
        spacing: Enums.spacing.none
        
        // ========== Title Row 标题行 ==========
        Item {
            width: parent.width
            height: 34
            
            // Month/Year title 月年标题
            Rectangle {
                id: titleBtn
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: titleText.width + Enums.spacing.xl
                height: parent.height
                radius: Enums.radius.small
                color: titleArea.containsMouse ? Enums.stateColor.calendarNavHover : Enums.transparent
                
                Label {
                    id: titleText
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    type: Enums.label.type_body
                    text: control.monthFormat.replace("{month}", control.month).replace("{year}", control.year)
                    font.weight: Font.Medium
                }
                
                MouseArea {
                    id: titleArea
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            
            // Navigation buttons 导航按钮
            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: Enums.spacing.xs
                
                CalendarNavButton {
                    icon: Enums.icon.chevron_up
                    onClicked: control.prevMonth()
                }
                CalendarNavButton {
                    icon: Enums.icon.chevron_down
                    onClicked: control.nextMonth()
                }
            }
        }
        
        // ========== Week Header 星期标题 ==========
        Item {
            width: parent.width
            height: 32
            
            Row {
                anchors.fill: parent
                Repeater {
                    model: control.weekDays
                    Item {
                        width: parent.width / 7
                        height: parent.height
                        Label {
                            anchors.centerIn: parent
                            type: Enums.label.type_caption
                            text: modelData
                            font.weight: Font.Medium
                        }
                    }
                }
            }
        }
        
        // ========== Day Grid Container 日期网格容器 ==========
        Item {
            id: gridContainer
            width: parent.width
            height: Enums.controlSize.calendarGridHeight  // 6 rows
            clip: true
            
            // Wrapper for both grids 两个网格的容器
            Item {
                id: gridWrapper
                width: parent.width
                height: parent.height * 2  // Two grids stacked
                y: 0
                
                Behavior on y {
                    id: gridWrapperBehavior
                    NumberAnimation { duration: Enums.duration.slower; easing.type: Easing.OutCubic }
                }
                
                // Current month grid 当前月网格
                Grid {
                    id: dayGrid
                    width: parent.width
                    columns: 7
                    rows: 6
                    y: 0  // Always at top 固定在顶部
                    
                    Repeater {
                        model: 42
                        
                        Rectangle {
                            id: dayCell
                            width: dayGrid.width / 7
                            height: Enums.controlSize.calendarCellHeight
                            color: Enums.transparent
                            
                            property int offset: index - control._firstDay + 1
                            property bool isPrevMonth: offset <= 0
                            property bool isNextMonth: offset > control._daysInMonth
                            property bool isCurrent: !isPrevMonth && !isNextMonth
                            property int displayDay: {
                                if (isPrevMonth) return control._daysInPrev + offset
                                if (isNextMonth) return offset - control._daysInMonth
                                return offset
                            }
                            
                            property bool isToday: isCurrent && 
                                control.year === control._todayYear && 
                                control.month === control._todayMonth && 
                                displayDay === control._todayDay
                            property bool selected: !control.rangeMode && isCurrent && displayDay === control.day
                            property bool hovered: cellArea.containsMouse && isCurrent
                            
                            property date cellDate: new Date(control.year, control.month - 1, displayDay)
                            property bool isRangeStart: control.rangeMode && control.rangeStart && isCurrent && 
                                cellDate.toDateString() === control.rangeStart.toDateString()
                            property bool isRangeEnd: control.rangeMode && control.rangeEnd && isCurrent && 
                                cellDate.toDateString() === control.rangeEnd.toDateString()
                            property bool isInRange: {
                                if (!control.rangeMode || !control.rangeStart || !control.rangeEnd || !isCurrent) return false
                                var t = cellDate.getTime()
                                var s = control.rangeStart.getTime()
                                var e = control.rangeEnd.getTime()
                                return t > Math.min(s, e) && t < Math.max(s, e)
                            }
                            
                            Item {
                                id: rangeBarContainer
                                readonly property bool showBar: control.rangeMode && dayCell.isCurrent && 
                                    (dayCell.isInRange || dayCell.isRangeStart || dayCell.isRangeEnd) &&
                                    !(dayCell.isRangeStart && dayCell.isRangeEnd)
                                anchors.fill: parent
                                visible: showBar
                                layer.enabled: true
                                
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    height: Enums.controlSize.calendarCell
                                    color: control._rangeBarColor
                                    x: dayCell.isRangeStart ? parent.width / 2 : 0
                                    width: dayCell.isRangeStart || dayCell.isRangeEnd ? parent.width / 2 : parent.width
                                }
                                
                                Rectangle {
                                    visible: dayCell.isRangeStart || dayCell.isRangeEnd
                                    anchors.centerIn: parent
                                    width: Enums.controlSize.calendarCell
                                    height: Enums.controlSize.calendarCell
                                    radius: Enums.radius.xlarge
                                    color: control._rangeBarColor
                                }
                            }
                            
                            Rectangle {
                                anchors.centerIn: parent
                                width: Enums.controlSize.calendarCell
                                height: Enums.controlSize.calendarCell
                                radius: Enums.radius.xlarge
                                color: dayCell.isToday ? control.accentColor : 
                                       (dayCell.selected || dayCell.isRangeStart || dayCell.isRangeEnd) ? Enums.stateColor.transparentPressed :
                                       dayCell.hovered ? Enums.stateColor.transparentHover : Enums.transparent
                                border.width: (dayCell.selected || dayCell.isRangeStart || dayCell.isRangeEnd) && !dayCell.isToday ? Enums.border.normal : 0
                                border.color: control.accentColor
                            }
                            
                            Label {
                                anchors.centerIn: parent
                                type: Enums.label.type_body
                                text: dayCell.displayDay
                                color: dayCell.isToday ? Enums.accentForeground :
                                       (dayCell.selected || dayCell.isRangeStart || dayCell.isRangeEnd) ? control.accentColor :
                                       !dayCell.isCurrent ? Enums.stateColor.pickerTextSecondary :
                                       Enums.textColor.primary
                            }
                            
                            MouseArea {
                                id: cellArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    var targetYear = control.year, targetMonth = control.month, targetDay = dayCell.displayDay
                                    if (dayCell.isPrevMonth) {
                                        if (control.month === 1) { targetYear--; targetMonth = 12 } else targetMonth--
                                    } else if (dayCell.isNextMonth) {
                                        if (control.month === 12) { targetYear++; targetMonth = 1 } else targetMonth++
                                    }
                                    if (control.rangeMode) {
                                        control.rangeDateClicked(new Date(targetYear, targetMonth - 1, targetDay))
                                    } else {
                                        if (dayCell.isPrevMonth) control.prevMonth()
                                        else if (dayCell.isNextMonth) control.nextMonth()
                                        control.day = targetDay
                                        control.dayClicked(control.day)
                                        control.dateChanged(control.year, control.month, control.day)
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Next month grid 目标月网格
                Grid {
                    id: nextGrid
                    width: parent.width
                    columns: 7
                    rows: 6
                    y: gridContainer.height  // Always below dayGrid 固定在dayGrid下方
                    
                    Repeater {
                        model: 42
                        
                        Rectangle {
                            width: nextGrid.width / 7
                            height: Enums.controlSize.calendarCellHeight
                            color: Enums.transparent
                            
                            property int offset: index - control._nextFirstDay + 1
                            property bool isPrevMonth: offset <= 0
                            property bool isNextMonth: offset > control._nextDaysInMonth
                            property bool isCurrent: !isPrevMonth && !isNextMonth
                            property int displayDay: {
                                if (isPrevMonth) return control._nextDaysInPrev + offset
                                if (isNextMonth) return offset - control._nextDaysInMonth
                                return offset
                            }
                            
                            property bool isToday: isCurrent && 
                                control._nextYear === control._todayYear && 
                                control._nextMonth === control._todayMonth && 
                                displayDay === control._todayDay
                            
                            Rectangle {
                                anchors.centerIn: parent
                                width: Enums.controlSize.calendarCell
                                height: Enums.controlSize.calendarCell
                                radius: Enums.radius.xlarge
                                color: parent.isToday ? control.accentColor : Enums.transparent
                            }
                            
                            Label {
                                anchors.centerIn: parent
                                type: Enums.label.type_body
                                text: parent.displayDay
                                color: {
                                    if (parent.isToday) return Enums.accentForeground
                                    if (!parent.isCurrent) return Enums.stateColor.pickerTextSecondary
                                    return Enums.textColor.primary
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Animation Timer 动画定时器 ====================
    Timer {
        id: animationTimer
        interval: Enums.duration.slower + 10
        onTriggered: {
            // Disable animation for reset 禁用动画以瞬间重置
            gridWrapperBehavior.enabled = false
            
            // Execute month change 执行月份切换
            if (control._pendingUpdateFunc) {
                control._pendingUpdateFunc()
                control._pendingUpdateFunc = null
            }
            // Reset all positions instantly 瞬间重置所有位置
            dayGrid.y = 0
            nextGrid.y = gridContainer.height
            gridWrapper.y = 0
            control._animating = false
            
            // Re-enable animation 重新启用动画
            gridWrapperBehavior.enabled = true
        }
    }
}
