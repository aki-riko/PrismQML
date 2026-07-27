// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// ColorPickerChannelSlider - RGB/Alpha channel slider RGB/透明度通道滑块
// Shows gradient from 0 to 255 for each channel
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string label: "R"       // R/G/B/A (default, will be overridden)
    property int channel: Enums.colorPickerMetrics.dialogRgbChannelR
    property int value: Enums.colorPickerMetrics.channelMinValue
    property color baseColor: Enums.colorPalette.automaticColor  // Current color (for gradient calculation)
    property bool showInput: true    // Show input field 显示输入框

    // ==================== Readonly State 只读状态 ====================
    readonly property int _safeValue: Math.max(Enums.colorPickerMetrics.channelMinValue,
                                               Math.min(Enums.colorPickerMetrics.channelMaxValue, value))
    readonly property real _handleTravel: Math.max(0, track.width - handle.width)
    
    // ==================== Signals 信号 ====================
    signal valueModified(int newValue)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.channelSliderWidth
    implicitHeight: Enums.spacing.xxxl
    
    // ==================== Content 内容 ====================
    Row {
        anchors.fill: parent
        spacing: Enums.spacing.m
        
        // Label 标签
        Label {
            width: Enums.colorPickerMetrics.channelLabelWidth
            type: Enums.label.type_body
            text: control.label
            anchors.verticalCenter: parent.verticalCenter
        }
        
        // Input field 输入框
        Rectangle {
            id: inputBox
            visible: control.showInput
            width: Enums.colorPickerMetrics.channelInputWidth
            height: Enums.controlSize.inputHeightCompact
            radius: Enums.radius.small
            color: Enums.stateColor.controlBg
            border.width: inputField.activeFocus ? Enums.colorPickerMetrics.channelInputFocusedBorderWidth : Enums.colorPickerMetrics.channelInputBorderWidth
            border.color: inputField.activeFocus ? Enums.accentColor : Enums.stateColor.border
            anchors.verticalCenter: parent.verticalCenter
            
            TextInput {
                id: inputField
                anchors.fill: parent
                anchors.margins: Enums.spacing.xs
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                text: control.value.toString()
                font.family: Enums.fontFamily
                font.pixelSize: Enums.typography.bodySmall
                color: Enums.textColor.primary
                selectByMouse: true
                validator: IntValidator { bottom: Enums.colorPickerMetrics.channelMinValue; top: Enums.colorPickerMetrics.channelMaxValue }
                
                onEditingFinished: {
                    var val = parseInt(text)
                    if (!isNaN(val) && val >= Enums.colorPickerMetrics.channelMinValue && val <= Enums.colorPickerMetrics.channelMaxValue && val !== control.value) {
                        control.value = val
                        control.valueModified(val)
                    }
                }
            }
        }
        
        // Slider track 滑块轨道
        Item {
            width: parent.width - (control.showInput ? Enums.colorPickerMetrics.channelShowInputWidth : Enums.colorPickerMetrics.channelHideInputWidth)
            height: Enums.colorPickerMetrics.channelSliderHeight
            anchors.verticalCenter: parent.verticalCenter
            
            // Checkerboard background for alpha 透明度棋盘背景
            Canvas {
                id: checkerboard
                anchors.fill: track
                visible: control.channel === Enums.colorPickerMetrics.channelAlphaIndex
                
                onPaint: {
                    var ctx = getContext("2d")
                    var size = Enums.colorPickerMetrics.checkerboardCellSize
                    for (var y = 0; y < height; y += size) {
                        for (var x = 0; x < width; x += size) {
                            ctx.fillStyle = ((x / size + y / size) % Enums.colorPickerMetrics.checkerboardParity === Enums.colorPickerMetrics.channelMinValue) ? Enums.gray.border : Enums.textColor.primary
                            ctx.fillRect(x, y, size, size)
                        }
                    }
                }
                Component.onCompleted: requestPaint()
            }
            
            Rectangle {
                id: track
                anchors.fill: parent
                radius: height / 2
                
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { 
                        position: Enums.opacityLevel.invisible
                        color: {
                            var c = control.baseColor
                            switch (control.channel) {
                                case Enums.colorPickerMetrics.dialogRgbChannelR: return Qt.rgba(Enums.opacityLevel.invisible, c.g, c.b, Enums.opacityLevel.visible)
                                case Enums.colorPickerMetrics.dialogRgbChannelG: return Qt.rgba(c.r, Enums.opacityLevel.invisible, c.b, Enums.opacityLevel.visible)
                                case Enums.colorPickerMetrics.dialogRgbChannelB: return Qt.rgba(c.r, c.g, Enums.opacityLevel.invisible, Enums.opacityLevel.visible)
                                case Enums.colorPickerMetrics.channelAlphaIndex: return Qt.rgba(c.r, c.g, c.b, Enums.opacityLevel.invisible)
                            }
                        }
                    }
                    GradientStop { 
                        position: Enums.opacityLevel.visible
                        color: {
                            var c = control.baseColor
                            switch (control.channel) {
                                case Enums.colorPickerMetrics.dialogRgbChannelR: return Qt.rgba(Enums.opacityLevel.visible, c.g, c.b, Enums.opacityLevel.visible)
                                case Enums.colorPickerMetrics.dialogRgbChannelG: return Qt.rgba(c.r, Enums.opacityLevel.visible, c.b, Enums.opacityLevel.visible)
                                case Enums.colorPickerMetrics.dialogRgbChannelB: return Qt.rgba(c.r, c.g, Enums.opacityLevel.visible, Enums.opacityLevel.visible)
                                case Enums.colorPickerMetrics.channelAlphaIndex: return Qt.rgba(c.r, c.g, c.b, Enums.opacityLevel.visible)
                            }
                        }
                    }
                }
                
                border.width: Enums.border.thin
                border.color: Enums.stateColor.border
            }
            
            // Handle 手柄
            Rectangle {
                id: handle
                width: Enums.spacing.xl
                height: Enums.spacing.xl
                radius: width / 2
                x: (control._safeValue / Enums.colorPickerMetrics.channelMaxValue) * control._handleTravel
                anchors.verticalCenter: parent.verticalCenter
                
                color: Enums.textColor.primary
                border.width: Enums.colorPickerMetrics.handleBorderWidth
                border.color: Enums.accentColor
                
                Behavior on x {
                    enabled: !pointerArea.pressed
                    NumberAnimation { duration: Enums.duration.fast }
                }
            }
            
            // Interaction 交互
            MouseArea {
                id: pointerArea

                function updateValue(mouse) {
                    if (!(width > 0)) return
                    var ratio = Math.max(Enums.opacityLevel.invisible, Math.min(Enums.opacityLevel.visible, mouse.x / width))
                    var newValue = Math.round(ratio * Enums.colorPickerMetrics.channelMaxValue)
                    if (newValue !== control.value) {
                        control.value = newValue
                        control.valueModified(newValue)
                    }
                }

                anchors.fill: parent
                enabled: control.enabled
                preventStealing: true
                
                onPressed: (mouse) => updateValue(mouse)
                onPositionChanged: (mouse) => { if (pressed) updateValue(mouse) }
            }
        }
    }
}
