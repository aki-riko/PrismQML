// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// ColorPickerInputs - RGB/Hex input fields RGB/Hex输入区
// Layout: Mode selector + Hex input + RGB inputs
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property color selectedColor: Enums.accentColor
    property int colorMode: Enums.colorPicker.mode_rgb  // RGB/HSV/HSL
    property bool showModeSelector: true
    
    // ==================== Signals 信号 ====================
    signal colorChanged(color newColor)
    signal modeChanged(int newMode)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.inputsWidth
    implicitHeight: contentColumn.implicitHeight
    
    // ==================== Internal 内部属性 ====================
    property int _r: Math.round(selectedColor.r * Enums.colorPickerMetrics.channelMaxValue)
    property int _g: Math.round(selectedColor.g * Enums.colorPickerMetrics.channelMaxValue)
    property int _b: Math.round(selectedColor.b * Enums.colorPickerMetrics.channelMaxValue)
    property string _hex: selectedColor.toString().slice(Enums.colorPickerMetrics.dialogHexStartIndex, Enums.colorPickerMetrics.dialogHexStartIndex + Enums.colorPickerMetrics.dialogHexSubstringLength).toUpperCase()
    
    // ==================== Content 内容 ====================
    Column {
        id: contentColumn
        anchors.fill: parent
        spacing: Enums.spacing.m
        
        // Mode selector + Hex input 模式选择+Hex输入
        Row {
            width: parent.width
            spacing: Enums.spacing.m
            
            // Mode selector 模式选择器
            Rectangle {
                visible: control.showModeSelector
                width: Enums.colorPickerMetrics.inputsModeWidth
                height: Enums.controlSize.inputHeightCompact
                radius: Enums.radius.small
                color: Enums.stateColor.controlBg
                border.width: Enums.border.thin
                border.color: Enums.stateColor.border
                
                Row {
                    anchors.centerIn: parent
                    spacing: Enums.spacing.xs
                    
                    Label {
                        type: Enums.label.type_caption
                        text: control.colorMode === Enums.colorPicker.mode_rgb ? "RGB" :
                              control.colorMode === Enums.colorPicker.mode_hsv ? "HSV" : "HSL"
                    }
                    
                    Label {
                        type: Enums.label.type_caption
                        text: Enums.colorPickerMetrics.dropdownArrowText
                        font.pixelSize: Enums.typography.caption - Enums.colorPickerMetrics.inputsModeArrowFontOffset
                        color: Enums.textColor.secondary
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    enabled: control.enabled
                    onClicked: {
                        // Cycle through modes 循环切换模式
                        var nextMode = (control.colorMode + 1) % Enums.colorPickerMetrics.dropdownModeCycleCount
                        control.colorMode = nextMode
                        control.modeChanged(nextMode)
                    }
                }
            }
            
            // Hex input Hex输入
            Row {
                spacing: Enums.spacing.xs
                
                Label {
                    type: Enums.label.type_caption
                    text: Enums.colorPickerMetrics.dialogHexPrefix
                    font.family: Enums.colorPickerMetrics.monospaceFontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Rectangle {
                    width: Enums.colorPickerMetrics.inputsHexWidth
                    height: Enums.controlSize.inputHeightCompact
                    radius: Enums.radius.small
                    color: Enums.stateColor.controlBg
                    border.width: hexInput.activeFocus ? Enums.colorPickerMetrics.channelInputFocusedBorderWidth : Enums.colorPickerMetrics.channelInputBorderWidth
                    border.color: hexInput.activeFocus ? Enums.accentColor : Enums.stateColor.border
                    
                    TextInput {
                        id: hexInput
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.s
                        verticalAlignment: Text.AlignVCenter
                        text: control._hex
                        font.family: Enums.colorPickerMetrics.monospaceFontFamily
                        font.pixelSize: Enums.typography.bodySmall
                        color: Enums.textColor.primary
                        maximumLength: Enums.colorPickerMetrics.dialogHexMaxLength
                        selectByMouse: true
                        enabled: control.enabled
                        
                        onEditingFinished: {
                            if (new RegExp("^[0-9A-Fa-f]{" + Enums.colorPickerMetrics.dialogHexRegexExactLen + "}$").test(text)) {
                                control.selectedColor = Enums.colorPickerMetrics.dialogHexPrefix + text
                                control.colorChanged(control.selectedColor)
                            }
                        }
                    }
                }
            }
        }
        
        // RGB inputs RGB输入
        Column {
            width: parent.width
            spacing: Enums.spacing.s
            
            // Red 红色
            ColorPickerChannelSlider {
                width: parent.width
                label: Translator.tr("rgb_r")
                channel: Enums.colorPickerMetrics.dialogRgbChannelR
                value: control._r
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control.selectedColor = Qt.rgba(val / Enums.colorPickerMetrics.channelMaxValue, control.selectedColor.g, control.selectedColor.b, control.selectedColor.a)
                    control.colorChanged(control.selectedColor)
                }
            }
            
            // Green 绿色
            ColorPickerChannelSlider {
                width: parent.width
                label: Translator.tr("rgb_g")
                channel: Enums.colorPickerMetrics.dialogRgbChannelG
                value: control._g
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control.selectedColor = Qt.rgba(control.selectedColor.r, val / Enums.colorPickerMetrics.channelMaxValue, control.selectedColor.b, control.selectedColor.a)
                    control.colorChanged(control.selectedColor)
                }
            }
            
            // Blue 蓝色
            ColorPickerChannelSlider {
                width: parent.width
                label: Translator.tr("rgb_b")
                channel: Enums.colorPickerMetrics.dialogRgbChannelB
                value: control._b
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control.selectedColor = Qt.rgba(control.selectedColor.r, control.selectedColor.g, val / Enums.colorPickerMetrics.channelMaxValue, control.selectedColor.a)
                    control.colorChanged(control.selectedColor)
                }
            }
        }
    }
    
    // Update internal values when color changes 颜色变化时更新内部值
    onSelectedColorChanged: {
        _r = Math.round(selectedColor.r * Enums.colorPickerMetrics.channelMaxValue)
        _g = Math.round(selectedColor.g * Enums.colorPickerMetrics.channelMaxValue)
        _b = Math.round(selectedColor.b * Enums.colorPickerMetrics.channelMaxValue)
        _hex = selectedColor.toString().slice(Enums.colorPickerMetrics.dialogHexStartIndex, Enums.colorPickerMetrics.dialogHexStartIndex + Enums.colorPickerMetrics.dialogHexSubstringLength).toUpperCase()
    }
}
