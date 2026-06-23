// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../effects"
import QtQuick.Effects
import "../../utils"
import "../../data"
import ".."
import "./_internal"
import "./_internal/DateTimeHelpers.js" as Helpers

// DateTimePicker - Unified date/time wheel picker 统一日期时间滚轮选择器
// Control via type/datePrecision/timePrecision/timeFormat 通过枚举控制
// Auto-localized via Translator 自动本地化
Rectangle {
    id: control

    // ==================== Type Props 类型属性 ====================
    property int type: Enums.picker.type_date
    property int datePrecision: Enums.picker.date_day
    property int timePrecision: Enums.picker.time_minute
    property int timeFormat: Enums.picker.format_24h

    // ==================== Value Props 值属性 ====================
    property int year: new Date().getFullYear()
    property int month: new Date().getMonth() + 1
    property int day: new Date().getDate()
    property int hour: -1  // -1 = not set
    property int minute: -1
    property int second: -1
    property bool isOpen: false

    // ==================== Range Props 范围属性 ====================
    property int minYear: new Date().getFullYear() - 100
    property int maxYear: new Date().getFullYear() + 100

    // ==================== Optional Override 可选覆盖 ====================
    // Removed: resetEnabled property 已删除：重置功能属性

    // ==================== Localization (auto from Translator) 本地化 ====================
    // Bind to _v to trigger re-evaluation on language change 绑定_v实现语言切换时自动更新
    readonly property int _tv: Translator._v
    readonly property string _lang: Translator.language
    readonly property bool _isEastern: _lang === "zh_CN" || _lang === "zh_TW" || _lang === "ja" || _lang === "ko"
    readonly property bool _yearFirst: _isEastern  // YMD for eastern, MDY/DMY for western
    readonly property string _yearSuffix: { _tv; return _isEastern ? Translator.tr("year") : "" }
    readonly property string _monthSuffix: { _tv; return _isEastern ? Translator.tr("month") : "" }
    readonly property string _daySuffix: { _tv; return _isEastern ? Translator.tr("day") : "" }
    readonly property string _hourSuffix: { _tv; return _isEastern ? Translator.tr("hour") : "" }
    readonly property string _minuteSuffix: { _tv; return _isEastern ? Translator.tr("minute") : "" }
    readonly property string _secondSuffix: { _tv; return _isEastern ? Translator.tr("second") : "" }
    readonly property string _amText: "AM"
    readonly property string _pmText: "PM"
    readonly property string _24hText: "24H"
    readonly property string _confirmText: { _tv; return Translator.tr("ok") }
    readonly property string _cancelText: { _tv; return Translator.tr("cancel") }
    readonly property string _resetText: { _tv; return Translator.tr("reset") }

    // ==================== Computed Props 计算属性 ====================
    readonly property bool _hasDate: type === Enums.picker.type_date || type === Enums.picker.type_datetime
    readonly property bool _hasTime: type === Enums.picker.type_time || type === Enums.picker.type_datetime
    readonly property bool _showYear: _hasDate && datePrecision >= Enums.picker.date_year
    readonly property bool _showMonth: _hasDate && datePrecision >= Enums.picker.date_month
    readonly property bool _showDay: _hasDate && datePrecision >= Enums.picker.date_day
    readonly property bool _showHour: _hasTime && timePrecision >= Enums.picker.time_hour
    readonly property bool _showMinute: _hasTime && timePrecision >= Enums.picker.time_minute
    readonly property bool _showSecond: _hasTime && timePrecision >= Enums.picker.time_second
    readonly property bool _is12Hour: _hasTime && timeFormat === Enums.picker.format_12h

    // Column count 列数
    readonly property int _dateColCount: (_showYear ? 1 : 0) + (_showMonth ? 1 : 0) + (_showDay ? 1 : 0)
    readonly property int _timeColCount: (_showHour ? 1 : 0) + (_showMinute ? 1 : 0) + (_showSecond ? 1 : 0) + (_is12Hour ? 1 : 0)
    readonly property int _totalColCount: (_hasDate ? _dateColCount : 0) + (_hasTime ? _timeColCount : 0)

    // ==================== Popup State 弹窗状态 ====================
    property int _tempYear: year
    property int _tempMonth: month
    property int _tempDay: day
    property int _tempHour: 0
    property int _tempMinute: 0
    property int _tempSecond: 0
    property bool _tempIsAm: true
    property bool _tempUse24H: false  // Temp 24H mode in popup 弹窗内临时24小时制模式
    property bool _initializing: false  // Prevent recursive updates during init 初始化时防止递归更新

    // ==================== Signals 信号 ====================
    signal dateTimeChanged(int year, int month, int day, int hour, int minute, int second)
    signal dateChanged(int year, int month, int day)
    signal timeChanged(int hour, int minute, int second)

    // ==================== Helper Functions 辅助函数 ====================
    function _buildDisplayModel() { return Helpers.buildDisplayModel(control, Translator) }
    function _getMonthName(m) { return Helpers.getMonthName(Translator, m) }
    function _pad(n) { return Helpers.pad(n) }
    function getDaysInMonth(y, m) { return Helpers.getDaysInMonth(y, m) }

    function openPopup() {
        var now = new Date()
        _tempYear = year > 0 ? year : now.getFullYear()
        _tempMonth = month > 0 ? month : now.getMonth() + 1
        _tempDay = day > 0 ? day : now.getDate()
        _tempHour = hour >= 0 ? hour : now.getHours()
        _tempMinute = minute >= 0 ? minute : now.getMinutes()
        _tempSecond = second >= 0 ? second : now.getSeconds()
        _tempIsAm = _tempHour < 12
        _tempUse24H = false  // Reset to 12H mode when opening 打开时重置为12小时制

        pickerPopup.popupWidth = control.width
        pickerPopup.popupHeight = 280
        pickerPopup.openAtPicker(control, control.height)
        isOpen = true

        // Set wheel positions after popup opens 弹窗打开后设置滚轮位置
        _initializing = true
        initTimer.restart()
    }

    function _initWheelPositions() {
        if (!_popupLoader.item) return
        var popup = _popupLoader.item
        if (popup.hourWheelLoader.item) {
            if (_is12Hour && !_tempUse24H) {
                var h12 = _tempHour % 12
                if (h12 === 0) h12 = 12
                popup.hourWheelLoader.item.setCurrentIndex(h12 - 1)
            } else {
                popup.hourWheelLoader.item.setCurrentIndex(_tempHour)
            }
        }
        if (popup.ampmWheelLoader.item) popup.ampmWheelLoader.item.setCurrentIndex(_tempHour < 12 ? 0 : 1)
        if (popup.minuteWheelLoader.item) popup.minuteWheelLoader.item.setCurrentIndex(_tempMinute)
        if (popup.secondWheelLoader.item) popup.secondWheelLoader.item.setCurrentIndex(_tempSecond)
        _initializing = false
    }

    function closePopup() { pickerPopup.close(); isOpen = false }

    function reset() {
        if (_hasDate) { year = 0; month = 0; day = 0 }
        if (_hasTime) { hour = -1; minute = -1; second = -1 }
    }

    function _get24Hour(h12, isAm) { return Helpers.get24Hour(h12, isAm) }

    // ==================== Public Methods 公共方法 ====================
    // Set date 设置日期
    function setDate(y, m, d) {
        year = y
        month = m
        day = d
    }

    // Set time 设置时间
    function setTime(h, m, s) {
        hour = h !== undefined ? h : 0
        minute = m !== undefined ? m : 0
        second = s !== undefined ? s : 0
    }


    // Open popup (alias) 打开弹窗（别名）
    function open() {
        openPopup()
    }

    // Close popup (alias) 关闭弹窗（别名）
    function close() {
        closePopup()
    }

    // Get date 获取日期
    function getDate() {
        return new Date(year, month - 1, day, hour >= 0 ? hour : 0, minute >= 0 ? minute : 0, second >= 0 ? second : 0)
    }

    // Get time 获取时间
    function getTime() {
        return { hour: hour >= 0 ? hour : 0, minute: minute >= 0 ? minute : 0, second: second >= 0 ? second : 0 }
    }

    // ==================== Model Builders 模型构建 ====================
    function _buildYearModel() { return Helpers.buildYearModel(minYear, maxYear, _yearSuffix) }
    function _buildMonthModel() { return Helpers.buildMonthModel(_yearFirst, _monthSuffix, Translator) }
    function _buildDayModel() { return Helpers.buildDayModel(_tempYear, _tempMonth, _daySuffix) }
    function _buildHour24Model() { return Helpers.buildHour24Model(_hourSuffix) }
    function _buildHour12Model() { return Helpers.buildHour12Model(_hourSuffix) }
    function _buildMinuteModel() { return Helpers.buildMinuteModel(_minuteSuffix) }
    function _buildSecondModel() { return Helpers.buildSecondModel(_secondSuffix) }

    function _updateDayWheel() {
        var dayLoader = _yearFirst ? _popupLoader.item.col3Loader : _popupLoader.item.col2Loader
        if (!dayLoader || !dayLoader.item) return
        var maxDays = getDaysInMonth(_tempYear, _tempMonth)
        var arr = Helpers.buildDayModel(_tempYear, _tempMonth, _daySuffix)
        dayLoader.item.items = arr
        if (_tempDay > maxDays) {
            _tempDay = maxDays
            dayLoader.item.setCurrentIndex(maxDays - 1)
        }
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Math.max(200, _totalColCount * 70)
    implicitHeight: Enums.controlSize.inputHeight
    radius: Enums.radius.small

    layer.enabled: true
    layer.effect: OpacityMask {
        mask: Rectangle { width: control.width; height: control.height; radius: control.radius }
    }

    color: {
        if (pickerMouseArea && pickerMouseArea.pressed) return Enums.stateColor.controlBgPressed
        if (pickerMouseArea && pickerMouseArea.containsMouse) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }
    border.width: Enums.border.thin
    border.color: isOpen ? Enums.accentColor : Enums.stateColor.border

    // Focus line 聚焦底线
    FocusLine {
        showLine: isOpen
        lineColor: Enums.accentColor
        parentRadius: control.radius
    }

    // ==================== Display 显示 ====================
    Row {
        anchors.fill: parent

        Repeater {
            model: _buildDisplayModel()

            Item {
                width: parent.width / _totalColCount
                height: parent.height

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_body
                    text: modelData.text
                    color: modelData.hasValue ? Enums.textColor.primary : Enums.textColor.disabled
                }

                // Separator 分隔线
                Separator {
                    type: Enums.separator.vertical
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    lineLength: parent.height - Enums.spacing.m
                    lineColor: Enums.stateColor.border
                    visible: index < _totalColCount - 1
                }
            }
        }
    }

    // ==================== Interaction 交互 ====================
    MouseArea {
        id: pickerMouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: isOpen ? closePopup() : openPopup()
    }

    Timer {
        id: initTimer
        interval: 50  // Wait for components to fully load 等待组件完全加载
        onTriggered: control._initWheelPositions()
    }

    // ==================== Popup 弹窗 ====================
    PopupWindowCore {
        id: pickerPopup
        popupWidth: control.width
        popupHeight: 280
        popupRadius: Enums.radius.large
        onClosed: control.isOpen = false

        Loader {
            id: _popupLoader
            anchors.fill: parent
            sourceComponent: DateTimePickerPopup {}
            onLoaded: item.control = control
        }
    }
}
