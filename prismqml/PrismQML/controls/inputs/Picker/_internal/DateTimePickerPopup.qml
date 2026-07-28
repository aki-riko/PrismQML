// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../.."

// DateTimePickerPopup - Popup content for DateTimePicker 日期时间选择器弹窗内容
// Extracted from DateTimePicker for modularity 从DateTimePicker提取以模块化
Column {
    id: popupContent
    
    // ==================== Public Props 公开属性 ====================
    property var control  // Parent DateTimePicker 父日期时间选择器

    // Loader aliases for parent control 给父控件使用的 Loader 别名
    property alias col1Loader: col1Loader
    property alias col2Loader: col2Loader
    property alias col3Loader: col3Loader
    property alias hourWheelLoader: hourWheelLoader
    property alias minuteWheelLoader: minuteWheelLoader
    property alias secondWheelLoader: secondWheelLoader
    property alias ampmWheelLoader: ampmWheelLoader

    // ==================== Internal Props 内部属性 ====================
    readonly property color _selectionHighlightColor: Enums.stateColor.selected
    
    spacing: Enums.spacing.none
    
    // ==================== Content 内容 ====================
    // Wheel area 滚轮区域
    Item {
        readonly property real _wheelWidth: control ? width / control._totalColCount : 70

        width: parent.width
        height: Enums.controlSize.wheelPickerAreaHeight
        
        Row {
            anchors.fill: parent
            spacing: Enums.spacing.none
            z: Enums.zIndex.content
            
            // Date wheels (order depends on _yearFirst) 日期滚轮（顺序取决于_yearFirst）
            // Column 1: year when year-first, otherwise month 第1列：年优先时为年，否则为月
            Loader {
                id: col1Loader
                active: control ? (control._hasDate && (control._yearFirst ? control._showYear : control._showMonth)) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? (control._yearFirst ? control._buildYearModel() : control._buildMonthModel()) : []
                    currentIndex: control ? (control._yearFirst ? control._tempYear - control.minYear : control._tempMonth - 1) : 0
                    onCurrentIndexChanged: {
                        if (!control || control._initializing) return
                        if (control._yearFirst) { control._tempYear = control.minYear + currentIndex; control._updateDayWheel() }
                        else { control._tempMonth = currentIndex + 1; control._updateDayWheel() }
                    }
                }
            }
            
            // Column 2: month when year-first, otherwise day 第2列：年优先时为月，否则为日
            Loader {
                id: col2Loader
                active: control ? (control._hasDate && (control._yearFirst ? control._showMonth : control._showDay)) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? (control._yearFirst ? control._buildMonthModel() : control._buildDayModel()) : []
                    currentIndex: control ? (control._yearFirst ? control._tempMonth - 1 : control._tempDay - 1) : 0
                    onCurrentIndexChanged: {
                        if (!control || control._initializing) return
                        if (control._yearFirst) { control._tempMonth = currentIndex + 1; control._updateDayWheel() }
                        else control._tempDay = currentIndex + 1
                    }
                }
            }
            
            // Column 3: day when year-first, otherwise year 第3列：年优先时为日，否则为年
            Loader {
                id: col3Loader
                active: control ? (control._hasDate && (control._yearFirst ? control._showDay : control._showYear)) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? (control._yearFirst ? control._buildDayModel() : control._buildYearModel()) : []
                    currentIndex: control ? (control._yearFirst ? control._tempDay - 1 : control._tempYear - control.minYear) : 0
                    onCurrentIndexChanged: {
                        if (!control || control._initializing) return
                        if (control._yearFirst) control._tempDay = currentIndex + 1
                        else { control._tempYear = control.minYear + currentIndex; control._updateDayWheel() }
                    }
                }
            }
            
            // Time wheels 时间滚轮 (Hour-Min-Sec-AM/PM)
            Loader {
                id: hourWheelLoader
                active: control ? (control._hasTime && control._showHour) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? ((control._is12Hour && !control._tempUse24H) ? control._buildHour12Model() : control._buildHour24Model()) : []
                    onCurrentIndexChanged: {
                        if (!control || control._initializing) return
                        if (control._is12Hour && !control._tempUse24H) {
                            var h12 = currentIndex + 1
                            control._tempHour = control._get24Hour(h12, control._tempIsAm)
                        } else {
                            control._tempHour = currentIndex
                        }
                    }
                }
            }
            
            Loader {
                id: minuteWheelLoader
                active: control ? (control._hasTime && control._showMinute) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? control._buildMinuteModel() : []
                    onCurrentIndexChanged: { if (control) control._tempMinute = currentIndex }
                }
            }
            
            Loader {
                id: secondWheelLoader
                active: control ? (control._hasTime && control._showSecond) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? control._buildSecondModel() : []
                    onCurrentIndexChanged: { if (control) control._tempSecond = currentIndex }
                }
            }
            
            // AM/PM wheel (rightmost for 12h mode) AM/PM滚轮（12小时制在最右边）
            Loader {
                id: ampmWheelLoader
                active: control ? (control._hasTime && control._is12Hour) : false
                width: active ? parent.parent._wheelWidth : 0
                height: parent.height
                sourceComponent: CycleWheelPicker {
                    items: control ? [control._amText, control._pmText, control._24hText] : []
                    cycle: false
                    onCurrentIndexChanged: {
                        if (!control) return
                        if (currentIndex === 2) {
                            var savedHour = control._tempHour
                            control._tempUse24H = true
                            if (hourWheelLoader.item) {
                                hourWheelLoader.item.items = control._buildHour24Model()
                                hourWheelLoader.item.setCurrentIndex(savedHour)
                                control._tempHour = savedHour
                            }
                        } else {
                            var wasUsing24H = control._tempUse24H
                            var savedHour = control._tempHour
                            control._tempUse24H = false
                            control._tempIsAm = (currentIndex === 0)
                            if (hourWheelLoader.item) {
                                if (wasUsing24H) {
                                    hourWheelLoader.item.items = control._buildHour12Model()
                                    var h12 = savedHour % 12
                                    if (h12 === 0) h12 = 12
                                    hourWheelLoader.item.setCurrentIndex(h12 - 1)
                                    control._tempHour = control._get24Hour(h12, control._tempIsAm)
                                } else {
                                    var h12Val = hourWheelLoader.item.currentIndex + 1
                                    control._tempHour = control._get24Hour(h12Val, control._tempIsAm)
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Separators 分隔线
        Repeater {
            model: control ? control._totalColCount - 1 : 0
            Separator {
                type: Enums.separator.vertical
                lineLength: parent.height - Enums.spacing.xxxl
                anchors.verticalCenter: parent.verticalCenter
                x: parent._wheelWidth * (index + 1)
                z: Enums.zIndex.popup
            }
        }
        
        // Selection highlight 选中高亮
        // Keep the opaque theme token below wheel content so the selected text remains visible.
        // 将不透明主题令牌放在滚轮内容下方，确保选中文字可见。
        Rectangle {
            anchors.centerIn: parent
            width: parent.width - Enums.spacing.m
            height: Enums.controlSize.inputHeight
            radius: Enums.radius.small
            color: popupContent._selectionHighlightColor
            z: Enums.zIndex.base
        }
    }
    
    // Separator 分隔线
    Separator {
        width: parent.width
    }
    
    // Buttons 按钮区域
    DateTimeButtons {
        control: popupContent.control
    }
}
