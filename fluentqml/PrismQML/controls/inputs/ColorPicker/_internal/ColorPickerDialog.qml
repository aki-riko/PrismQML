// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../dialogs"
import "../../../data"

// ColorPickerDialog - Modal color dialog based on MessageBox 基于MessageBox的模态颜色对话框
MessageBox {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property color selectedColor: Enums.accentColor
    property color initialColor: Enums.accentColor       // Old color for preview 旧颜色预览
    property string title: qsTr("Choose Background Color")
    property string editColorText: qsTr("Custom Color")
    property bool enableAlpha: false
    
    // ==================== Internal HSV State 内部HSV状态 ====================
    property real _hue: Enums.colorPickerMetrics.dialogHueDefault
    property real _saturation: Enums.colorPickerMetrics.dialogSaturationDefault
    property real _brightness: Enums.colorPickerMetrics.dialogBrightnessDefault
    property int _alpha: Enums.colorPickerMetrics.dialogAlphaDefault
    
    // ==================== Signals 信号 ====================
    signal colorAccepted(color value)
    signal colorUpdated(color value)
    
    // ==================== Override DialogBoxCore 重写基类 ====================
    dismissOnScrimClick: true
    
    onAccepted: colorAccepted(selectedColor)

    // ==================== Functions 函数 ====================
    function updateColor() {
        selectedColor = Qt.hsva(_hue, _saturation, _brightness, _alpha / Enums.colorPickerMetrics.dialogAlphaMaxValue)
        colorUpdated(selectedColor)
    }

    function updateHsvFromColor() {
        _hue = selectedColor.hsvHue >= 0 ? selectedColor.hsvHue : 0
        _saturation = selectedColor.hsvSaturation
        _brightness = selectedColor.hsvValue
        _alpha = Math.round(selectedColor.a * Enums.colorPickerMetrics.dialogAlphaMaxValue)
    }

    function setColor(color) {
        selectedColor = color
        initialColor = color
        updateHsvFromColor()
    }

    // Override open to init HSV 重写open以初始化HSV
    function open() {
        initialColor = selectedColor
        updateHsvFromColor()

        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Use overlayTarget if set 如果设置了overlayTarget则使用
        var target = overlayTarget
        if (target && target !== control.parent) {
            control.parent = target
        }

        _isOpen = true
    }

    // ==================== Content 内容 ====================
    Column {
        id: contentColumn
        width: Enums.colorPickerMetrics.dialogContentWidth
        spacing: Enums.spacing.l
        
        // Title 标题
        Label {
            type: Enums.label.type_body_strong
            text: control.title
            font.pixelSize: Enums.typography.title
        }
        
        // Main content 主内容
        Row {
            spacing: Enums.spacing.xxxl
            
            // Left: Panel + Brightness 左侧：面板+亮度
            Column {
                spacing: Enums.spacing.l
                
                // Hue/Saturation Panel 色相/饱和度面板
                ColorPickerPanel {
                    id: panel
                    width: Enums.colorPickerMetrics.dialogPanelSize
                    height: Enums.colorPickerMetrics.dialogPanelSize
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
                
                // Brightness Slider 亮度滑块
                Item {
                    width: Enums.colorPickerMetrics.dialogPanelSize
                    height: Enums.colorPickerMetrics.dialogBrightnessHeight
                    
                    Rectangle {
                        anchors.fill: parent
                        radius: height / 2
                        
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: Qt.hsva(control._hue, control._saturation, 0, 1) }
                            GradientStop { position: 1; color: Qt.hsva(control._hue, control._saturation, 1, 1) }
                        }
                        
                        border.width: Enums.border.thin
                        border.color: Enums.stateColor.border
                    }
                    
                    // Handle 手柄
                    Rectangle {
                        x: control._brightness * (parent.width - width)
                        anchors.verticalCenter: parent.verticalCenter
                        width: Enums.colorPickerMetrics.dialogBrightnessHandleSize
                        height: Enums.colorPickerMetrics.dialogBrightnessHandleSize
                        radius: width / 2
                        color: Enums.textColor.primary
                        border.width: Enums.colorPickerMetrics.handleBorderWidth
                        border.color: Enums.accentColor
                        
                        Behavior on x { NumberAnimation { duration: Enums.duration.fast } }
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        enabled: control.enabled
                        
                        function updateBrightness(mouse) {
                            control._brightness = Math.max(0, Math.min(1, mouse.x / width))
                            control.updateColor()
                        }
                        
                        onPressed: (mouse) => updateBrightness(mouse)
                        onPositionChanged: (mouse) => { if (pressed) updateBrightness(mouse) }
                    }
                }
            }
            
            // Right: Color Preview 右侧：颜色预览
            Column {
                spacing: Enums.spacing.micro
                
                // New color 新颜色
                Rectangle {
                    width: Enums.colorPickerMetrics.dialogPreviewWidth
                    height: Enums.colorPickerMetrics.dialogPreviewHeight
                    radius: Enums.radius.small
                    color: control.selectedColor
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.border
                }
                
                // Old color 旧颜色
                Rectangle {
                    width: Enums.colorPickerMetrics.dialogPreviewWidth
                    height: Enums.colorPickerMetrics.dialogPreviewHeight
                    radius: Enums.radius.small
                    color: control.initialColor
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.border
                }
            }
        }
        
        // Custom Color Section 编辑颜色区域
        Column {
            spacing: Enums.spacing.m
            
            // Custom Color + Hex 编辑颜色 + HEX
            Row {
                spacing: Enums.spacing.xxxl * 2 + Enums.spacing.l  // 60px
                
                Label {
                    type: Enums.label.type_body
                    text: control.editColorText
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Rectangle {
                    width: Enums.colorPickerMetrics.dialogInputWidth
                    height: Enums.colorPickerMetrics.dialogInputHeight
                    radius: Enums.radius.small
                    color: Enums.stateColor.controlBg
                    border.width: hexInput.activeFocus ? Enums.colorPickerMetrics.channelInputFocusedBorderWidth : Enums.colorPickerMetrics.channelInputBorderWidth
                    border.color: hexInput.activeFocus ? Enums.accentColor : Enums.stateColor.border
                    
                    Label {
                        x: Enums.colorPickerMetrics.dialogHexPrefixX
                        anchors.verticalCenter: parent.verticalCenter
                        type: Enums.label.type_caption
                        text: Enums.colorPickerMetrics.dialogHexPrefix
                        color: Enums.textColor.secondary
                    }
                    
                    TextInput {
                        id: hexInput
                        anchors.fill: parent
                        anchors.leftMargin: Enums.colorPickerMetrics.dialogHexInputLeftMargin
                        anchors.rightMargin: Enums.spacing.m
                        verticalAlignment: Text.AlignVCenter
                        text: control.selectedColor.toString().slice(Enums.colorPickerMetrics.dialogHexStartIndex, Enums.colorPickerMetrics.dialogHexStartIndex + Enums.colorPickerMetrics.dialogHexSubstringLength)
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        color: Enums.textColor.primary
                        selectByMouse: true
                        enabled: control.enabled
                        maximumLength: Enums.colorPickerMetrics.dialogHexMaxLength
                        validator: RegularExpressionValidator {
                            regularExpression: new RegExp("[0-9A-Fa-f]{0," + Enums.colorPickerMetrics.dialogHexRegexMaxLen + "}")
                        }
                        
                        onEditingFinished: {
                            if (new RegExp("^[0-9A-Fa-f]{" + Enums.colorPickerMetrics.dialogHexRegexExactLen + "}$").test(text)) {
                                control.selectedColor = Enums.colorPickerMetrics.dialogHexPrefix + text
                                control.updateHsvFromColor()
                            }
                        }
                    }
                }
            }
            
            // RGB Inputs RGB输入
            Repeater {
                model: [
                    { label: qsTr("Red"), getValue: () => Math.round(control.selectedColor.r * Enums.colorPickerMetrics.channelMaxValue), channel: Enums.colorPickerMetrics.dialogRgbChannelR },
                    { label: qsTr("Green"), getValue: () => Math.round(control.selectedColor.g * Enums.colorPickerMetrics.channelMaxValue), channel: Enums.colorPickerMetrics.dialogRgbChannelG },
                    { label: qsTr("Blue"), getValue: () => Math.round(control.selectedColor.b * Enums.colorPickerMetrics.channelMaxValue), channel: Enums.colorPickerMetrics.dialogRgbChannelB }
                ]
                
                Row {
                    spacing: Enums.spacing.m
                    
                    Rectangle {
                        width: Enums.colorPickerMetrics.dialogInputWidth
                        height: Enums.colorPickerMetrics.dialogInputHeight
                        radius: Enums.radius.small
                        color: Enums.stateColor.controlBg
                        border.width: rgbInput.activeFocus ? Enums.colorPickerMetrics.channelInputFocusedBorderWidth : Enums.colorPickerMetrics.channelInputBorderWidth
                        border.color: rgbInput.activeFocus ? Enums.accentColor : Enums.stateColor.border
                        
                        TextInput {
                            id: rgbInput
                            anchors.fill: parent
                            anchors.margins: Enums.spacing.m
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.getValue()
                            font.family: Enums.fontFamily
                            font.pixelSize: Enums.typography.body
                            color: Enums.textColor.primary
                            selectByMouse: true
                            validator: IntValidator { bottom: 0; top: Enums.colorPickerMetrics.channelMaxValue }
                            enabled: control.enabled
                            
                            property int ch: modelData.channel
                            onEditingFinished: {
                                var val = parseInt(text) / Enums.colorPickerMetrics.channelMaxValue
                                var c = control.selectedColor
                                if (ch === Enums.colorPickerMetrics.dialogRgbChannelR) control.selectedColor = Qt.rgba(val, c.g, c.b, c.a)
                                else if (ch === Enums.colorPickerMetrics.dialogRgbChannelG) control.selectedColor = Qt.rgba(c.r, val, c.b, c.a)
                                else control.selectedColor = Qt.rgba(c.r, c.g, val, c.a)
                                control.updateHsvFromColor()
                            }
                        }
                    }
                    
                    Label {
                        type: Enums.label.type_body
                        text: modelData.label
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }
}
