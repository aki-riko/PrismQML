// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../buttons/Button"
import "../../../data"

// ColorPickerDropdown - Full dropdown picker content 完整下拉选择器内容
// Layout: HSV Panel + Brightness slider + Mode selector + Hex + RGBA sliders + Buttons
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property color selectedColor: Enums.accentColor
    property int colorMode: Enums.colorPicker.mode_rgb
    property bool enableAlpha: true
    
    // ==================== Internal HSV 内部HSV ====================
    property real _hue: Enums.colorPickerMetrics.dialogHueDefault
    property real _saturation: Enums.colorPickerMetrics.dialogSaturationDefault
    property real _brightness: Enums.colorPickerMetrics.dialogBrightnessDefault
    property int _alpha: Enums.colorPickerMetrics.dialogAlphaDefault
    
    // ==================== Signals 信号 ====================
    signal accepted(color value)
    signal rejected()
    signal colorChanged(color value)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.dropdownWidth
    implicitHeight: contentColumn.implicitHeight + Enums.spacing.xl * 2

    // ==================== Functions 函数 ====================
    function updateColor() {
        selectedColor = Qt.hsva(_hue, _saturation, _brightness, _alpha / Enums.colorPickerMetrics.dialogAlphaMaxValue)
        colorChanged(selectedColor)
    }

    function updateHsvFromColor() {
        _hue = selectedColor.hsvHue >= 0 ? selectedColor.hsvHue : 0
        _saturation = selectedColor.hsvSaturation
        _brightness = selectedColor.hsvValue
    }

    function _formatHex() {
        var r = Math.round(selectedColor.r * Enums.colorPickerMetrics.channelMaxValue).toString(16).padStart(Enums.colorPickerMetrics.hexByteLen, '0')
        var g = Math.round(selectedColor.g * Enums.colorPickerMetrics.channelMaxValue).toString(16).padStart(Enums.colorPickerMetrics.hexByteLen, '0')
        var b = Math.round(selectedColor.b * Enums.colorPickerMetrics.channelMaxValue).toString(16).padStart(Enums.colorPickerMetrics.hexByteLen, '0')
        var a = _alpha.toString(16).padStart(Enums.colorPickerMetrics.hexByteLen, '0')
        return Enums.colorPickerMetrics.dialogHexPrefix + (enableAlpha ? a : "") + r + g + b
    }

    function _parseHex(text) {
        var hex = text.replace(Enums.colorPickerMetrics.dialogHexPrefix, "").toLowerCase()
        // Support formats: RGB, RRGGBB, AARRGGBB
        if (new RegExp("^[0-9a-f]{" + Enums.colorPickerMetrics.hexRgbLen + "}$").test(hex)) {
            selectedColor = Enums.colorPickerMetrics.dialogHexPrefix + hex
            updateHsvFromColor()
        } else if (new RegExp("^[0-9a-f]{" + Enums.colorPickerMetrics.hexRgbaLen + "}$").test(hex)) {
            _alpha = parseInt(hex.slice(0, Enums.colorPickerMetrics.hexByteLen), 16)
            selectedColor = Enums.colorPickerMetrics.dialogHexPrefix + hex.slice(Enums.colorPickerMetrics.hexAlphaOffset, Enums.colorPickerMetrics.hexAlphaOffset + Enums.colorPickerMetrics.hexRgbLen)
            updateHsvFromColor()
        }
    }

    // ==================== Content 内容 ====================
    Column {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        spacing: Enums.spacing.m
        
        // HSV Panel 色相/饱和度面板
        ColorPickerPanel {
            id: panel
            width: parent.width
            height: Enums.colorPickerMetrics.dropdownPanelHeight
            hue: control._hue
            saturation: control._saturation
            brightness: control._brightness
            enabled: control.enabled
            onColorChanged: (h, s) => {
                control._hue = h
                control._saturation = s
                control.updateColor()
            }
        }
        
        // Brightness slider 亮度滑块
        ColorPickerBrightnessSlider {
            width: parent.width
            hue: control._hue
            saturation: control._saturation
            value: control._brightness
            enabled: control.enabled
            onValueModified: (val) => {
                control._brightness = val
                control.updateColor()
            }
        }
        
        // Mode selector + Hex input 模式选择+Hex输入
        Row {
            width: parent.width
            spacing: Enums.spacing.m
            
            // Mode selector 模式选择器
            Rectangle {
                width: Enums.colorPickerMetrics.dropdownModeWidth
                height: Enums.controlSize.inputHeightCompact
                radius: Enums.radius.small
                color: modeArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.stateColor.controlBg
                border.width: Enums.border.thin
                border.color: Enums.stateColor.border
                
                Row {
                    anchors.centerIn: parent
                    spacing: Enums.spacing.s
                    
                    Label {
                        type: Enums.label.type_body
                        text: control.colorMode === Enums.colorPicker.mode_rgb ? "RGB" :
                              control.colorMode === Enums.colorPicker.mode_hsv ? "HSV" : "HSL"
                    }
                    
                    Label {
                        type: Enums.label.type_caption
                        text: Enums.colorPickerMetrics.dropdownArrowText
                        color: Enums.textColor.secondary
                    }
                }
                
                MouseArea {
                    id: modeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: control.enabled
                    onClicked: control.colorMode = (control.colorMode + 1) % Enums.colorPickerMetrics.dropdownModeCycleCount
                }
            }
            
            // Hex input Hex输入
            Rectangle {
                width: parent.width - Enums.colorPickerMetrics.dropdownHexGap
                height: Enums.controlSize.inputHeightCompact
                radius: Enums.radius.small
                color: Enums.stateColor.controlBg
                border.width: hexInput.activeFocus ? Enums.colorPickerMetrics.channelInputFocusedBorderWidth : Enums.colorPickerMetrics.channelInputBorderWidth
                border.color: hexInput.activeFocus ? Enums.accentColor : Enums.stateColor.border
                
                TextInput {
                    id: hexInput
                    anchors.fill: parent
                    anchors.leftMargin: Enums.spacing.m
                    anchors.rightMargin: Enums.spacing.m
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: control._formatHex()
                    font.family: Enums.colorPickerMetrics.monospaceFontFamily
                    font.pixelSize: Enums.typography.body
                    color: Enums.textColor.primary
                    selectByMouse: true
                    enabled: control.enabled
                    
                    onEditingFinished: control._parseHex(text)
                }
            }
        }
        
        // RGBA sliders RGBA滑块
        Column {
            width: parent.width
            spacing: Enums.spacing.s
            
            ColorPickerChannelSlider {
                width: parent.width
                label: Translator.tr("rgb_r")
                channel: Enums.colorPickerMetrics.dialogRgbChannelR
                value: Math.round(control.selectedColor.r * Enums.colorPickerMetrics.channelMaxValue)
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control.selectedColor = Qt.rgba(val / Enums.colorPickerMetrics.channelMaxValue, control.selectedColor.g, control.selectedColor.b, control._alpha / Enums.colorPickerMetrics.dialogAlphaMaxValue)
                    control.updateHsvFromColor()
                    control.colorChanged(control.selectedColor)
                }
            }
            
            ColorPickerChannelSlider {
                width: parent.width
                label: Translator.tr("rgb_g")
                channel: Enums.colorPickerMetrics.dialogRgbChannelG
                value: Math.round(control.selectedColor.g * Enums.colorPickerMetrics.channelMaxValue)
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control.selectedColor = Qt.rgba(control.selectedColor.r, val / Enums.colorPickerMetrics.channelMaxValue, control.selectedColor.b, control._alpha / Enums.colorPickerMetrics.dialogAlphaMaxValue)
                    control.updateHsvFromColor()
                    control.colorChanged(control.selectedColor)
                }
            }
            
            ColorPickerChannelSlider {
                width: parent.width
                label: Translator.tr("rgb_b")
                channel: Enums.colorPickerMetrics.dialogRgbChannelB
                value: Math.round(control.selectedColor.b * Enums.colorPickerMetrics.channelMaxValue)
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control.selectedColor = Qt.rgba(control.selectedColor.r, control.selectedColor.g, val / Enums.colorPickerMetrics.channelMaxValue, control._alpha / Enums.colorPickerMetrics.dialogAlphaMaxValue)
                    control.updateHsvFromColor()
                    control.colorChanged(control.selectedColor)
                }
            }
            
            ColorPickerChannelSlider {
                visible: control.enableAlpha
                width: parent.width
                label: Translator.tr("rgb_a")
                channel: Enums.colorPickerMetrics.channelAlphaIndex
                value: control._alpha
                baseColor: control.selectedColor
                enabled: control.enabled
                onValueModified: (val) => {
                    control._alpha = val
                    control.updateColor()
                    control.colorChanged(control.selectedColor)
                }
            }
        }
        
        // Separator 分隔线
        Separator {
            width: parent.width
            lineWidth: Enums.colorPickerMetrics.dropdownSeparatorHeight
        }
        
        // Buttons 按钮（撑满宽度）
        Row {
            width: parent.width
            spacing: Enums.spacing.m
            
            // Confirm 确认
            ButtonCore {
                width: (parent.width - parent.spacing) / 2
                style: Enums.button.style_transparent
                icon: Enums.icon.checkmark
                enabled: control.enabled
                onClicked: control.accepted(control.selectedColor)
            }
            
            // Cancel 取消
            ButtonCore {
                width: (parent.width - parent.spacing) / 2
                style: Enums.button.style_transparent
                icon: Enums.icon.dismiss
                enabled: control.enabled
                onClicked: control.rejected()
            }
        }
    }

    Component.onCompleted: updateHsvFromColor()
}
