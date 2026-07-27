// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// GradientSlider - Pure QtQuick implementation 颜色滑块
// Gradient background, smooth drag 渐变背景流畅拖动
Item {
    id: control
    
    // Use Singleton enum: Enums.gradientSlider.mode_hue/... 使用单例枚举
    
    property int mode: Enums.gradientSlider.mode_hue
    property real value: 0  // 0-1
    property color baseColor: Enums.colorPickerDefaults.baseRed

    // ==================== Readonly State 只读状态 ====================
    readonly property real _safeValue: isFinite(value) ? Math.max(0, Math.min(1, value)) : 0
    readonly property real _handleTravel: Math.max(0, track.width - handle.width)
    
    signal valueModified(real newValue)
    
    implicitWidth: 200
    implicitHeight: Enums.spacing.xxxl
    
    // Gradient track 渐变轨道
    Rectangle {
        id: track
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        height: Enums.controlSize.checkboxInner
        radius: Enums.radius.large
        
        gradient: Gradient {
            orientation: Gradient.Horizontal
            
            GradientStop { 
                position: Enums.colorPickerGradient.huePos0
                color: {
                    switch (control.mode) {
                        case Enums.gradientSlider.mode_hue: return Enums.colorPickerGradient.hueColor0
                        case Enums.gradientSlider.mode_saturation: return Qt.hsla(Qt.hsla(control.baseColor).h, 0, 0.5, 1)
                        case Enums.gradientSlider.mode_lightness: return Enums.colorPickerGradient.lightnessDark
                        case Enums.gradientSlider.mode_alpha: return Enums.transparent
                        default: return control.baseColor
                    }
                }
            }
            GradientStop { 
                position: Enums.colorPickerGradient.huePos1
                color: control.mode === Enums.gradientSlider.mode_hue ? Enums.colorPickerGradient.hueColor1 : undefined
            }
            GradientStop { 
                position: Enums.colorPickerGradient.huePos2
                color: control.mode === Enums.gradientSlider.mode_hue ? Enums.colorPickerGradient.hueColor2 : undefined
            }
            GradientStop { 
                position: Enums.colorPickerGradient.huePos3
                color: {
                    switch (control.mode) {
                        case Enums.gradientSlider.mode_hue: return Enums.colorPickerGradient.hueColor3
                        case Enums.gradientSlider.mode_lightness: return Enums.colorPickerGradient.lightnessMid
                        default: return undefined
                    }
                }
            }
            GradientStop { 
                position: Enums.colorPickerGradient.huePos4
                color: control.mode === Enums.gradientSlider.mode_hue ? Enums.colorPickerGradient.hueColor4 : undefined
            }
            GradientStop { 
                position: Enums.colorPickerGradient.huePos5
                color: control.mode === Enums.gradientSlider.mode_hue ? Enums.colorPickerGradient.hueColor5 : undefined
            }
            GradientStop { 
                position: Enums.colorPickerGradient.huePos6
                color: {
                    switch (control.mode) {
                        case Enums.gradientSlider.mode_hue: return Enums.colorPickerGradient.hueColor6
                        case Enums.gradientSlider.mode_saturation: return Qt.hsla(Qt.hsla(control.baseColor).h, 1, 0.5, 1)
                        case Enums.gradientSlider.mode_lightness: return Enums.colorPickerGradient.lightnessLight
                        case Enums.gradientSlider.mode_alpha: return control.baseColor
                        default: return control.baseColor
                    }
                }
            }
        }
        
        border.width: Enums.border.thin
        border.color: Enums.stateColor.closeHover
    }
    
    // Handle 手柄
    Rectangle {
        id: handle
        width: Enums.spacing.xxl
        height: Enums.spacing.xxl
        radius: width / 2
        x: control._safeValue * control._handleTravel
        anchors.verticalCenter: parent.verticalCenter
        
        border.width: Enums.border.normal
        border.color: Enums.stateColor.colorSliderThumbBorder
        
        Rectangle {
            anchors.centerIn: parent
            width: Enums.controlSize.checkboxInner
            height: Enums.controlSize.checkboxInner
            radius: width / 2
            color: {
                switch (control.mode) {
                    case Enums.gradientSlider.mode_hue: return Qt.hsla(control._safeValue, 1, 0.5, 1)
                    default: return control.baseColor
                }
            }
        }
        
        MouseArea {
            anchors.fill: parent
            anchors.margins: -Enums.spacing.xs
            enabled: control.enabled
            drag.target: parent
            drag.axis: Drag.XAxis
            drag.minimumX: 0
            drag.maximumX: control._handleTravel
            
            onPositionChanged: {
                if (pressed) {
                    var newValue = control._handleTravel > 0 ? handle.x / control._handleTravel : 0
                    control.value = Math.max(0, Math.min(1, newValue))
                    control.valueModified(control.value)
                }
            }
        }
    }
}
