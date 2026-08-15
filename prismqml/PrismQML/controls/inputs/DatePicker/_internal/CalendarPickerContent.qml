// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "."

// CalendarPickerContent - Calendar visual tree and lazy next-month grid 日历视觉树与惰性下月网格
// Keeps CalendarPickerCore focused on public date state and navigation orchestration.
// 将 CalendarPickerCore 入口限制为公开日期状态与导航编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var calendarControl

    // ==================== Public Props 公开属性 ====================
    property alias gridWrapper: gridWrapper
    property alias gridWrapperBehavior: gridWrapperBehavior
    property alias dayGrid: dayGrid
    property alias nextGrid: nextGrid
    property alias animationTimer: animationTimer
    readonly property real gridContainerHeight: gridContainer.height

    implicitHeight: mainColumn.implicitHeight
    anchors.fill: parent

    // ==================== Content 内容 ====================
    Column {
        id: mainColumn
        anchors.fill: parent
        spacing: Enums.spacing.none

        // Title row 标题行
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
                color: titleArea.containsMouse
                    ? Enums.stateColor.calendarNavHover : Enums.transparent

                Label {
                    id: titleText
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    type: Enums.label.type_body
                    text: calendarControl.monthFormat
                        .replace("{month}", calendarControl.month)
                        .replace("{year}", calendarControl.year)
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
                    onClicked: calendarControl.prevMonth()
                }
                CalendarNavButton {
                    icon: Enums.icon.chevron_down
                    onClicked: calendarControl.nextMonth()
                }
            }
        }

        // Week header 星期标题
        Item {
            width: parent.width
            height: 32

            Row {
                anchors.fill: parent
                Repeater {
                    model: calendarControl.weekDays
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

        // Day grid container 日期网格容器
        Item {
            id: gridContainer
            width: parent.width
            height: Enums.controlSize.calendarGridHeight
            clip: true

            // Wrapper for both grids 两个网格的容器
            Item {
                id: gridWrapper
                width: parent.width
                height: parent.height * 2
                y: 0

                Behavior on y {
                    id: gridWrapperBehavior
                    NumberAnimation {
                        duration: Enums.duration.slower
                        easing.type: Easing.OutCubic
                    }
                }

                // Current month grid 当前月网格
                Grid {
                    id: dayGrid
                    width: parent.width
                    columns: 7
                    rows: 6
                    y: 0

                    Repeater {
                        model: 42

                        Rectangle {
                            id: dayCell

                            property int offset: index - calendarControl._firstDay + 1
                            property bool isPrevMonth: offset <= 0
                            property bool isNextMonth: offset > calendarControl._daysInMonth
                            property bool isCurrent: !isPrevMonth && !isNextMonth
                            property int displayDay: {
                                if (isPrevMonth) return calendarControl._daysInPrev + offset
                                if (isNextMonth) return offset - calendarControl._daysInMonth
                                return offset
                            }

                            property bool isToday: isCurrent
                                && calendarControl.year === calendarControl._todayYear
                                && calendarControl.month === calendarControl._todayMonth
                                && displayDay === calendarControl._todayDay
                            property bool selected: !calendarControl.rangeMode
                                && isCurrent && displayDay === calendarControl.day
                            property bool hovered: cellArea.containsMouse && isCurrent

                            property date cellDate: new Date(
                                calendarControl.year, calendarControl.month - 1, displayDay
                            )
                            property bool isRangeStart: calendarControl.rangeMode
                                && calendarControl.rangeStart && isCurrent
                                && cellDate.toDateString()
                                    === calendarControl.rangeStart.toDateString()
                            property bool isRangeEnd: calendarControl.rangeMode
                                && calendarControl.rangeEnd && isCurrent
                                && cellDate.toDateString()
                                    === calendarControl.rangeEnd.toDateString()
                            property bool isInRange: {
                                if (!calendarControl.rangeMode || !calendarControl.rangeStart
                                        || !calendarControl.rangeEnd || !isCurrent) return false
                                var t = cellDate.getTime()
                                var s = calendarControl.rangeStart.getTime()
                                var e = calendarControl.rangeEnd.getTime()
                                return t > Math.min(s, e) && t < Math.max(s, e)
                            }

                            width: dayGrid.width / 7
                            height: Enums.controlSize.calendarCellHeight
                            color: Enums.transparent

                            Item {
                                id: rangeBarContainer
                                readonly property bool showBar: calendarControl.rangeMode
                                    && dayCell.isCurrent
                                    && (dayCell.isInRange || dayCell.isRangeStart
                                        || dayCell.isRangeEnd)
                                    && !(dayCell.isRangeStart && dayCell.isRangeEnd)
                                anchors.fill: parent
                                visible: showBar
                                layer.enabled: showBar

                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    height: Enums.controlSize.calendarCell
                                    color: calendarControl._rangeBarColor
                                    x: dayCell.isRangeStart ? parent.width / 2 : 0
                                    width: dayCell.isRangeStart || dayCell.isRangeEnd
                                        ? parent.width / 2 : parent.width
                                }

                                Rectangle {
                                    visible: dayCell.isRangeStart || dayCell.isRangeEnd
                                    anchors.centerIn: parent
                                    width: Enums.controlSize.calendarCell
                                    height: Enums.controlSize.calendarCell
                                    radius: width / 2
                                    color: calendarControl._rangeBarColor
                                }
                            }

                            Rectangle {
                                anchors.centerIn: parent
                                width: Enums.controlSize.calendarCell
                                height: Enums.controlSize.calendarCell
                                radius: width / 2
                                color: dayCell.isToday ? calendarControl.accentColor
                                    : (dayCell.selected || dayCell.isRangeStart
                                       || dayCell.isRangeEnd)
                                        ? Enums.stateColor.transparentPressed
                                        : dayCell.hovered
                                            ? Enums.stateColor.transparentHover
                                            : Enums.transparent
                                border.width: (dayCell.selected || dayCell.isRangeStart
                                    || dayCell.isRangeEnd) && !dayCell.isToday
                                    ? Enums.border.normal : 0
                                border.color: calendarControl.accentColor
                            }

                            Label {
                                anchors.centerIn: parent
                                type: Enums.label.type_body
                                text: dayCell.displayDay
                                color: dayCell.isToday ? Enums.accentForeground
                                    : (dayCell.selected || dayCell.isRangeStart
                                       || dayCell.isRangeEnd) ? calendarControl.accentColor
                                    : !dayCell.isCurrent ? Enums.stateColor.pickerTextSecondary
                                    : Enums.textColor.primary
                            }

                            MouseArea {
                                id: cellArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    var targetYear = calendarControl.year
                                    var targetMonth = calendarControl.month
                                    var targetDay = dayCell.displayDay
                                    if (dayCell.isPrevMonth) {
                                        if (calendarControl.month === 1) {
                                            targetYear--
                                            targetMonth = 12
                                        } else targetMonth--
                                    } else if (dayCell.isNextMonth) {
                                        if (calendarControl.month === 12) {
                                            targetYear++
                                            targetMonth = 1
                                        } else targetMonth++
                                    }
                                    if (calendarControl.rangeMode) {
                                        calendarControl.rangeDateClicked(
                                            new Date(targetYear, targetMonth - 1, targetDay)
                                        )
                                    } else {
                                        if (dayCell.isPrevMonth) calendarControl.prevMonth()
                                        else if (dayCell.isNextMonth) calendarControl.nextMonth()
                                        calendarControl.day = targetDay
                                        calendarControl.dayClicked(calendarControl.day)
                                        calendarControl.dateChanged(
                                            targetYear, targetMonth, targetDay
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                // Next month grid 目标月网格
                Loader {
                    id: nextGrid
                    width: parent.width
                    height: gridContainer.height
                    y: gridContainer.height

                    active: calendarControl._nextGridRequested
                    sourceComponent: Component {
                        Grid {
                            anchors.fill: parent
                            columns: 7
                            rows: 6

                            Repeater {
                                model: 42

                                Rectangle {
                                    property int offset: index - calendarControl._nextFirstDay + 1
                                    property bool isPrevMonth: offset <= 0
                                    property bool isNextMonth:
                                        offset > calendarControl._nextDaysInMonth
                                    property bool isCurrent: !isPrevMonth && !isNextMonth
                                    property int displayDay: {
                                        if (isPrevMonth) {
                                            return calendarControl._nextDaysInPrev + offset
                                        }
                                        if (isNextMonth) {
                                            return offset - calendarControl._nextDaysInMonth
                                        }
                                        return offset
                                    }

                                    property bool isToday: isCurrent
                                        && calendarControl._nextYear === calendarControl._todayYear
                                        && calendarControl._nextMonth === calendarControl._todayMonth
                                        && displayDay === calendarControl._todayDay

                                    width: nextGrid.width / 7
                                    height: Enums.controlSize.calendarCellHeight
                                    color: Enums.transparent

                                    Rectangle {
                                        anchors.centerIn: parent
                                        width: Enums.controlSize.calendarCell
                                        height: Enums.controlSize.calendarCell
                                        radius: width / 2
                                        color: parent.isToday
                                            ? calendarControl.accentColor : Enums.transparent
                                    }

                                    Label {
                                        anchors.centerIn: parent
                                        type: Enums.label.type_body
                                        text: parent.displayDay
                                        color: {
                                            if (parent.isToday) return Enums.accentForeground
                                            if (!parent.isCurrent) {
                                                return Enums.stateColor.pickerTextSecondary
                                            }
                                            return Enums.textColor.primary
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Animation timer 动画定时器
    Timer {
        id: animationTimer
        interval: Enums.duration.slower + 10
        onTriggered: {
            // Disable animation for reset 禁用动画以瞬间重置
            gridWrapperBehavior.enabled = false

            // Execute month change 执行月份切换
            if (calendarControl._pendingUpdateFunc) {
                calendarControl._pendingUpdateFunc()
                calendarControl._pendingUpdateFunc = null
            }
            // Reset all positions instantly 瞬间重置所有位置
            dayGrid.y = 0
            nextGrid.y = gridContainer.height
            gridWrapper.y = 0
            calendarControl._animating = false

            // Re-enable animation 重新启用动画
            gridWrapperBehavior.enabled = true
        }
    }
}
