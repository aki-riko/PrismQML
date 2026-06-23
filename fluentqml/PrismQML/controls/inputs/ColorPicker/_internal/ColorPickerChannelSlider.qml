// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// ColorPickerChannelSlider - RGB/Alpha channel slider RGB/透明度通道滑块
// Shows gradient from 0 to 255 for each channel
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property string label: "R"       // R/G/B/A (default, will be overridden)
    property int channel: 0          // 0=R, 1=G, 2=B, 3=A
    property int value: 0            // 0-255
    property color baseColor: Enums.colorPalette.automaticColor  // Current color (for gradient calculation)
    property bool showInput: true    // Show input field 显示输入框
    
    // ==================== Signals 信号 ====================
    signal valueModified(int newValue)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.channelSliderWidth
    implicitHeight: Enums.spacing.xxxl
    
    // ==================== Layout 布局 ====================
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
                validator: IntValidator { bottom: 0; top: Enums.colorPickerMetrics.channelMaxValue }
                
                onEditingFinished: {
                    var val = parseInt(text)
                    if (!isNaN(val) && val >= 0 && val <= Enums.colorPickerMetrics.channelMaxValue && val !== control.value) {
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
                            ctx.fillStyle = ((x / size + y / size) % 2 === 0) ? Enums.gray.border : Enums.textColor.primary
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
                        position: 0
                        color: {
                            var c = control.baseColor
                            switch (control.channel) {
                                case 0: return Qt.rgba(Enums.opacityLevel.invisible, c.g, c.b, Enums.opacityLevel.visible)
                                case 1: return Qt.rgba(c.r, Enums.opacityLevel.invisible, c.b, Enums.opacityLevel.visible)
                                case 2: return Qt.rgba(c.r, c.g, Enums.opacityLevel.invisible, Enums.opacityLevel.visible)
                                case 3: return Qt.rgba(c.r, c.g, c.b, Enums.opacityLevel.invisible)
                            }
                        }
                    }
                    GradientStop { 
                        position: 1
                        color: {
                            var c = control.baseColor
                            switch (control.channel) {
                                case 0: return Qt.rgba(Enums.opacityLevel.visible, c.g, c.b, Enums.opacityLevel.visible)
                                case 1: return Qt.rgba(c.r, Enums.opacityLevel.visible, c.b, Enums.opacityLevel.visible)
                                case 2: return Qt.rgba(c.r, c.g, Enums.opacityLevel.visible, Enums.opacityLevel.visible)
                                case 3: return Qt.rgba(c.r, c.g, c.b, Enums.opacityLevel.visible)
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
                x: (control.value / Enums.colorPickerMetrics.channelMaxValue) * (track.width - width)
                anchors.verticalCenter: parent.verticalCenter
                
                color: Enums.textColor.primary
                border.width: Enums.colorPickerMetrics.handleBorderWidth
                border.color: Enums.accentColor
                
                Behavior on x { NumberAnimation { duration: Enums.duration.fast } }
            }
            
            // Interaction 交互
            MouseArea {
                anchors.fill: parent
                enabled: control.enabled
                preventStealing: true
                
                function updateValue(mouse) {
                    var ratio = Math.max(0, Math.min(1, mouse.x / width))
                    var newValue = Math.round(ratio * Enums.colorPickerMetrics.channelMaxValue)
                    if (newValue !== control.value) {
                        control.value = newValue
                        control.valueModified(newValue)
                    }
                }
                
                onPressed: (mouse) => updateValue(mouse)
                onPositionChanged: (mouse) => { if (pressed) updateValue(mouse) }
            }
        }
    }
}
