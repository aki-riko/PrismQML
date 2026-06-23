// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
                position: 0.0
                color: {
                    switch (control.mode) {
                        case Enums.gradientSlider.mode_hue: return "red"
                        case Enums.gradientSlider.mode_saturation: return Qt.hsla(Qt.hsla(control.baseColor).h, 0, 0.5, 1)
                        case Enums.gradientSlider.mode_lightness: return "black"
                        case Enums.gradientSlider.mode_alpha: return Enums.transparent
                        default: return control.baseColor
                    }
                }
            }
            GradientStop { 
                position: 0.166
                color: control.mode === Enums.gradientSlider.mode_hue ? "yellow" : undefined
            }
            GradientStop { 
                position: 0.333
                color: control.mode === Enums.gradientSlider.mode_hue ? "lime" : undefined
            }
            GradientStop { 
                position: 0.5
                color: {
                    switch (control.mode) {
                        case Enums.gradientSlider.mode_hue: return "cyan"
                        case Enums.gradientSlider.mode_lightness: return "gray"
                        default: return undefined
                    }
                }
            }
            GradientStop { 
                position: 0.666
                color: control.mode === Enums.gradientSlider.mode_hue ? "blue" : undefined
            }
            GradientStop { 
                position: 0.833
                color: control.mode === Enums.gradientSlider.mode_hue ? "magenta" : undefined
            }
            GradientStop { 
                position: 1.0
                color: {
                    switch (control.mode) {
                        case Enums.gradientSlider.mode_hue: return "red"
                        case Enums.gradientSlider.mode_saturation: return Qt.hsla(Qt.hsla(control.baseColor).h, 1, 0.5, 1)
                        case Enums.gradientSlider.mode_lightness: return "white"
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
        x: control.value * (track.width - width)
        anchors.verticalCenter: parent.verticalCenter
        
        color: "white"
        border.width: Enums.border.normal
        border.color: Enums.stateColor.colorSliderThumbBorder
        
        Rectangle {
            anchors.centerIn: parent
            width: Enums.controlSize.checkboxInner
            height: Enums.controlSize.checkboxInner
            radius: width / 2
            color: {
                switch (control.mode) {
                    case Enums.gradientSlider.mode_hue: return Qt.hsla(control.value, 1, 0.5, 1)
                    default: return control.baseColor
                }
            }
        }
        
        MouseArea {
            anchors.fill: parent
            anchors.margins: -4
            enabled: control.enabled
            drag.target: parent
            drag.axis: Drag.XAxis
            drag.minimumX: 0
            drag.maximumX: track.width - handle.width
            
            onPositionChanged: {
                if (pressed) {
                    control.value = handle.x / (track.width - handle.width)
                    control.valueModified(control.value)
                }
            }
        }
    }
}
