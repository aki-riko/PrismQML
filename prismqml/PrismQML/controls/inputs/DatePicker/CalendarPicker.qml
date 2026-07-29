// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import QtQuick.Window
import QtQuick.Effects
import "../../data"
import "../../icons"
import "../../utils"

// CalendarPicker - Calendar picker with popup 日历选择器（带弹窗）
// Uses CalendarPickerCore for calendar grid layout 使用CalendarPickerCore作为日历网格布局
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Type enum 类型枚举: Enums.calendarPicker.type_single / type_range
    property int type: Enums.calendarPicker.type_single

    // Single mode props 单选模式属性
    property int year: new Date().getFullYear()
    property int month: new Date().getMonth() + Enums.calendarPicker.monthMinimum
    property int day: new Date().getDate()
    property bool hasDate: true

    // Range mode props 范围模式属性
    property date startDate: new Date()
    property date endDate: new Date()
    property bool hasRange: false
    property bool isOpen: false
    property color accentColor: Enums.accentColor

    // Localization 本地化
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
    property string placeholderText: {
        Translator._v
        return _isRange ? Translator.tr("select_date_range")
                        : Translator.tr("select_date")
    }
    property string startHint: {
        Translator._v
        return Translator.tr("select_start_date")
    }
    property string endHint: {
        Translator._v
        return Translator.tr("select_end_date")
    }

    // ==================== Internal Props 内部属性 ====================
    property bool _selectingStart: true  // Selecting start or end 选择开始或结束

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isRange: type === Enums.calendarPicker.type_range
    readonly property string displayDate: {
        if (_isRange) {
            return hasRange ? _formatDate(startDate) + Enums.calendarPicker.rangeSeparator + _formatDate(endDate) : placeholderText
        }
        return hasDate ? (year + Enums.calendarPicker.dateSeparator + (month < Enums.calendarPicker.twoDigitThreshold ? Enums.calendarPicker.datePadCharacter : "") + month + Enums.calendarPicker.dateSeparator + (day < Enums.calendarPicker.twoDigitThreshold ? Enums.calendarPicker.datePadCharacter : "") + day) : placeholderText
    }

    // ==================== Signals 信号 ====================
    signal dateChanged(int year, int month, int day)
    signal rangeChanged(date startDate, date endDate)

    // ==================== Internal Methods 内部方法 ====================
    function _formatDate(d) {
        return d.getFullYear() + Enums.calendarPicker.dateSeparator + String(d.getMonth() + Enums.calendarPicker.monthMinimum).padStart(Enums.calendarPicker.dateFieldWidth, Enums.calendarPicker.datePadCharacter) + Enums.calendarPicker.dateSeparator + String(d.getDate()).padStart(Enums.calendarPicker.dateFieldWidth, Enums.calendarPicker.datePadCharacter)
    }

    // ==================== Public Methods 公开方法 ====================
    function openPopup() {
        // Sync CalendarView with current date 同步日历视图到当前日期
        if (_isRange) {
            calendarView.year = startDate.getFullYear()
            calendarView.month = startDate.getMonth() + Enums.calendarPicker.monthMinimum
            calendarView.day = Enums.calendarPicker.noSelectionDay
            calendarView.rangeMode = true
            calendarView.rangeStart = hasRange ? startDate : null
            calendarView.rangeEnd = hasRange ? endDate : null
            _selectingStart = true
        } else {
            calendarView.year = control.year
            calendarView.month = control.month
            calendarView.day = control.hasDate ? control.day : Enums.calendarPicker.noSelectionDay
            calendarView.rangeMode = false
        }

        calPopup.popupWidth = Enums.controlSize.calendarPopupWidth
        calPopup.popupHeight = Enums.controlSize.calendarPopupHeight
        calPopup.openAtControl(control)
        isOpen = true
    }

    function closePopup() { calPopup.close(); isOpen = false }

    function setDate(y, m, d) {
        year = y
        month = Math.max(Enums.calendarPicker.monthMinimum, Math.min(Enums.calendarPicker.monthMaximum, m))
        day = Math.max(Enums.calendarPicker.dayMinimum, Math.min(Enums.calendarPicker.dayMaximum, d))
        hasDate = true
    }

    function setRange(start, end) {
        startDate = start
        endDate = end
        hasRange = true
    }

    function getDate() { return new Date(year, month - Enums.calendarPicker.monthMinimum, day) }
    function reset() {
        if (_isRange) { hasRange = false; _selectingStart = true }
        else hasDate = false
    }

    // Open popup (alias) 打开弹窗（别名）
    function open() {
        openPopup()
    }

    // Close popup (alias) 关闭弹窗（别名）
    function close() {
        closePopup()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: _isRange ? Enums.controlSize.calendarPickerRangeWidth : Enums.controlSize.calendarPickerWidth
    implicitHeight: Enums.controlSize.inputHeight
    radius: Enums.radius.small

    // Fluent Design CalendarPicker style 样式
    color: {
        if (!enabled) return Enums.stateColor.controlBgDisabled
        if (mouseArea.pressed) return Enums.stateColor.controlBgPressed
        if (mouseArea.containsMouse) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }

    border.width: Enums.border.thin
    border.color: Enums.stateColor.pickerBorder

    // ==================== Content 内容 ====================
    Label {
        anchors.left: parent.left
        anchors.right: calIcon.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.m
        type: Enums.label.type_body
        text: displayDate
        color: {
            if (!enabled) return Enums.stateColor.pickerTextDisabled
            if (!hasDate) return Enums.stateColor.pickerTextPlaceholder
            return Enums.textColor.primary
        }
        elide: Text.ElideRight
    }

    Icon {
        id: calIcon
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        iconSize: Enums.controlSize.checkIconSize
        icon: Enums.icon.calendar
        opacity: (_isRange ? hasRange : hasDate) ? Enums.opacityLevel.visible : Enums.opacityLevel.secondary
    }

    // Interaction 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: control.enabled
        enabled: control.enabled
        onClicked: isOpen ? closePopup() : openPopup()
    }

    // Popup window 弹出窗口
    PopupWindowCore {
        id: calPopup
        popupWidth: Enums.controlSize.calendarPopupWidth
        popupHeight: Enums.controlSize.calendarPopupHeight
        popupRadius: Enums.radius.large
        animationType: Enums.calendarPicker.popupAnimationSlideDown
        onClosed: control.isOpen = false
        
        // Wheel area for month navigation 滚轮切换月份
        MouseArea {
            anchors.fill: parent
            onWheel: function(wheel) {
                if (wheel.angleDelta.y > 0) {
                    calendarView.prevMonth()
                } else if (wheel.angleDelta.y < 0) {
                    calendarView.nextMonth()
                }
            }
        }
        
        // Use CalendarPickerCore for calendar grid 使用CalendarPickerCore作为日历网格
        CalendarPickerCore {
            id: calendarView
            anchors.fill: parent
            anchors.margins: Enums.spacing.m
            accentColor: control.accentColor
            weekDays: control.weekDays
            monthFormat: control.monthFormat
            
            onDateChanged: function(y, m, d) {
                if (!control._isRange) {
                    control.year = y
                    control.month = m
                    control.day = d
                    control.hasDate = true
                    control.dateChanged(y, m, d)
                    control.closePopup()
                }
            }
            
            onRangeDateClicked: function(clickedDate) {
                if (!control._isRange) return
                
                if (control._selectingStart) {
                    // First click: set start date 第一次点击：设置开始日期
                    calendarView.rangeStart = clickedDate
                    calendarView.rangeEnd = clickedDate
                    control._selectingStart = false
                } else {
                    // Second click: set end date and close 第二次点击：设置结束日期并关闭
                    if (clickedDate < calendarView.rangeStart) {
                        calendarView.rangeEnd = calendarView.rangeStart
                        calendarView.rangeStart = clickedDate
                    } else {
                        calendarView.rangeEnd = clickedDate
                    }
                    control.startDate = calendarView.rangeStart
                    control.endDate = calendarView.rangeEnd
                    control.hasRange = true
                    control.rangeChanged(control.startDate, control.endDate)
                    control._selectingStart = true
                    control.closePopup()
                }
            }
        }
    }
}
