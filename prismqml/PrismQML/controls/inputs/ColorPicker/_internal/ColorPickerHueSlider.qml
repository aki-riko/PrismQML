// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// ColorPickerHueSlider - Horizontal hue slider 水平色相滑块
// Shows full spectrum: red→yellow→green→cyan→blue→magenta→red
Item {
    id: control
    
    // ==================== Properties 属性 ====================
    property real value: Enums.colorPickerMetrics.hueValueDefault         // 0-1, maps to hue 0-360°
    
    // ==================== Signals 信号 ====================
    signal valueModified(real newValue)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.hueSliderWidth
    implicitHeight: Enums.spacing.xxl
    
    // ==================== Hue Track 色相轨道 ====================
    Rectangle {
        id: track
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: Enums.colorPickerMetrics.hueTrackHeight
        radius: height / 2
        
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: Enums.colorPickerGradient.huePos0; color: Enums.colorPickerGradient.hueColor0 }
            GradientStop { position: Enums.colorPickerGradient.huePos1; color: Enums.colorPickerGradient.hueColor1 }
            GradientStop { position: Enums.colorPickerGradient.huePos2; color: Enums.colorPickerGradient.hueColor2 }
            GradientStop { position: Enums.colorPickerGradient.huePos3; color: Enums.colorPickerGradient.hueColor3 }
            GradientStop { position: Enums.colorPickerGradient.huePos4; color: Enums.colorPickerGradient.hueColor4 }
            GradientStop { position: Enums.colorPickerGradient.huePos5; color: Enums.colorPickerGradient.hueColor5 }
            GradientStop { position: Enums.colorPickerGradient.huePos6; color: Enums.colorPickerGradient.hueColor6 }
        }
        
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
    }
    
    // ==================== Handle 手柄 ====================
    Rectangle {
        id: handle
        width: Enums.colorPickerMetrics.hueHandleSize
        height: Enums.colorPickerMetrics.hueHandleSize
        radius: width / 2
        x: control.value * (track.width - width)
        anchors.verticalCenter: parent.verticalCenter
        
        color: Enums.textColor.primary
        border.width: Enums.colorPickerMetrics.hueHandleBorderWidth
        border.color: Enums.accentColor
        
        // Inner color indicator 内部颜色指示
        Rectangle {
            anchors.centerIn: parent
            width: parent.width - Enums.colorPickerMetrics.hueHandleInnerPadding
            height: parent.height - Enums.colorPickerMetrics.hueHandleInnerPadding
            radius: width / 2
            color: Qt.hsva(control.value, Enums.opacityLevel.visible, Enums.opacityLevel.visible, Enums.opacityLevel.visible)
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
            if (Math.abs(newValue - control.value) > Enums.colorPickerMetrics.hueUpdateEpsilon) {
                control.value = newValue
                control.valueModified(newValue)
            }
        }
        
        onPressed: (mouse) => updateValue(mouse)
        onPositionChanged: (mouse) => { if (pressed) updateValue(mouse) }
    }
}
