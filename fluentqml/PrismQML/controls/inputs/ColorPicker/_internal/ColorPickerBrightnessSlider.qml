// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// ColorPickerBrightnessSlider - Brightness/Value slider 亮度/明度滑块
// Shows gradient from dark to light for current hue 显示当前色相的深色到浅色渐变
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property real hue: Enums.colorPickerMetrics.dialogHueDefault           // Current hue 当前色相
    property real saturation: Enums.colorPickerMetrics.dialogSaturationDefault    // Current saturation 当前饱和度
    property real value: Enums.colorPickerMetrics.brightnessValueDefault         // 0-1, brightness value 亮度值
    
    // ==================== Signals 信号 ====================
    signal valueModified(real newValue)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.brightnessSliderWidth
    implicitHeight: Enums.spacing.xxl
    
    // ==================== Brightness Track 亮度轨道 ====================
    Rectangle {
        id: track
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: Enums.colorPickerMetrics.brightnessTrackHeight
        radius: height / 2
        
        gradient: Gradient {
            orientation: Gradient.Horizontal
            // From dark (black) to light (saturated color) 从深色（黑色）到浅色（饱和色）

            GradientStop { 
                position: 0
                color: Qt.hsva(control.hue, control.saturation, Enums.opacityLevel.invisible, Enums.opacityLevel.visible)
            }
            GradientStop { 
                position: 1
                color: Qt.hsva(control.hue, control.saturation, Enums.opacityLevel.visible, Enums.opacityLevel.visible)
            }
        }
        
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
    }
    
    // ==================== Handle 手柄 ====================
    Rectangle {
        id: handle
        width: Enums.colorPickerMetrics.brightnessHandleSize
        height: Enums.colorPickerMetrics.brightnessHandleSize
        radius: width / 2
        x: control.value * (track.width - width)
        anchors.verticalCenter: parent.verticalCenter
        
        color: Enums.textColor.primary
        border.width: Enums.colorPickerMetrics.handleBorderWidth
        border.color: Enums.accentColor
        
        // Inner color indicator 内部颜色指示
        Rectangle {
            anchors.centerIn: parent
            width: parent.width - Enums.colorPickerMetrics.brightnessHandleInnerPadding
            height: parent.height - Enums.colorPickerMetrics.brightnessHandleInnerPadding
            radius: width / 2
            color: Qt.hsva(control.hue, control.saturation, control.value, Enums.opacityLevel.visible)
        }
        
        Behavior on x { NumberAnimation { duration: Enums.duration.fast } }
    }
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        anchors.fill: parent
        enabled: control.enabled
        preventStealing: true
        
        function updateValue(mouse) {
            var newValue = Math.max(0, Math.min(1, mouse.x / width))
            if (Math.abs(newValue - control.value) > Enums.colorPickerMetrics.brightnessUpdateEpsilon) {
                control.value = newValue
                control.valueModified(newValue)
            }
        }
        
        onPressed: (mouse) => updateValue(mouse)
        onPositionChanged: (mouse) => { if (pressed) updateValue(mouse) }
    }
}
