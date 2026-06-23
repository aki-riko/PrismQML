// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../../effects"

// AudioWaveform - Audio waveform visualization 音频波形可视化
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var waveformData: []  // Waveform data array [0.0-1.0] 波形数据
    property color waveColor: Enums.accentColor
    property color waveColorEnd: Qt.lighter(waveColor, 1.2)  // Gradient end color 渐变结束色
    property color backgroundColor: Enums.cardColor
    property int barWidth: Enums.controlSize.topNavIndicatorHeight
    property int barSpacing: Enums.spacing.micro
    property real progress: 0  // Playback progress 0-1 播放进度
    property color progressColor: Enums.accentColorLight
    property color progressColorEnd: Qt.lighter(progressColor, 1.3)
    property bool animated: true  // Enable animations 启用动画
    property bool showProgressIndicator: true  // Show progress line 显示进度线
    
    // ==================== Signals 信号 ====================
    signal clicked(real position)  // Click position 0-1 点击位置
    signal progressUpdated(real newProgress)
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool _hovered: mouseArea.containsMouse
    readonly property bool _pressed: mouseArea.pressed
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: 80

    // ==================== Fluent Design Methods 方法 ====================
    // Set source (alias for setWaveformData) 设置音频源
    function setSource(src) { /* Use setWaveformData instead */ }

    // ==================== Demo Data Generator 示例数据生成 ====================
    function generateRandomWaveform(count) {
        var data = []
        var seed = Math.random() * 100
        for (var i = 0; i < count; i++) {
            // Generate smoother, more natural waveform 生成更平滑自然的波形
            var base = Math.sin(i * 0.3 + seed) * 0.3 + 0.5
            var noise = Math.random() * 0.3
            var value = Math.min(1.0, Math.max(0.1, base + noise))
            data.push(value)
        }
        waveformData = data
    }

    // ==================== Background Card 背景卡片 ====================
    ShadowedRectangle {
        id: background
        anchors.fill: parent
        color: control.backgroundColor
        radius: Enums.radius.large
        border.width: Enums.border.thin
        border.color: control._hovered ? Enums.accentColor : Enums.stateColor.cardBorder
        shadowLevel: control._hovered ? Enums.shadow.level4 : Enums.shadow.level2
        
        Behavior on border.color {
            enabled: control.animated
            ColorAnimation { duration: Enums.duration.fast }
        }
    }
    
    // ==================== Waveform Container 波形容器 ====================
    Item {
        id: waveformContainer
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        clip: true
        
        // Progress background overlay 进度背景遮罩
        Rectangle {
            id: progressOverlay
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: parent.width * control.progress
            color: Enums.isDark 
                ? Qt.rgba(Enums.accentColor.r, Enums.accentColor.g, Enums.accentColor.b, 0.15)
                : Qt.rgba(Enums.accentColor.r, Enums.accentColor.g, Enums.accentColor.b, 0.1)
            radius: Enums.radius.small
            
            Behavior on width {
                enabled: control.animated && !mouseArea.pressed
                NumberAnimation { duration: Enums.duration.fast }
            }
        }
        
        // Waveform bars 波形条
        Row {
            id: waveformRow
            anchors.centerIn: parent
            height: parent.height
            spacing: control.barSpacing
            
            Repeater {
                model: control.waveformData.length
                
                Rectangle {
                    id: bar
                    width: control.barWidth
                    height: Math.max(Enums.spacing.xs, control.waveformData[index] * waveformRow.height * 0.9)
                    radius: width / 2
                    anchors.verticalCenter: parent.verticalCenter
                    
                    // Gradient based on position and progress 基于位置和进度的渐变
                    gradient: Gradient {
                        orientation: Gradient.Vertical
                        GradientStop { 
                            position: 0.0 
                            color: {
                                var pos = index / control.waveformData.length
                                return pos < control.progress ? control.progressColorEnd : control.waveColorEnd
                            }
                        }
                        GradientStop { 
                            position: 1.0 
                            color: {
                                var pos = index / control.waveformData.length
                                return pos < control.progress ? control.progressColor : control.waveColor
                            }
                        }
                    }
                    
                    // Subtle glow effect for active bars 活跃条的微妙发光效果
                    opacity: {
                        var pos = index / control.waveformData.length
                        if (pos < control.progress) return 1.0
                        return control._hovered ? 0.85 : 0.7
                    }
                    
                    // Scale animation on hover 悬停时的缩放动画
                    transform: Scale {
                        origin.x: bar.width / 2
                        origin.y: bar.height / 2
                        xScale: control._hovered ? 1.05 : 1.0
                        yScale: control._hovered ? 1.02 : 1.0
                        
                        Behavior on xScale {
                            enabled: control.animated
                            NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic }
                        }
                        Behavior on yScale {
                            enabled: control.animated
                            NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic }
                        }
                    }
                    
                    Behavior on opacity {
                        enabled: control.animated
                        NumberAnimation { duration: Enums.duration.fast }
                    }
                }
            }
        }
        
        // Progress indicator line 进度指示线
        Rectangle {
            id: progressLine
            visible: control.showProgressIndicator && control.progress > 0
            x: parent.width * control.progress - 1
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.topMargin: Enums.spacing.xs
            anchors.bottomMargin: Enums.spacing.xs
            width: Enums.spacing.xxs
            radius: width / 2
            color: Enums.accentForeground
            
            // Glow effect 发光效果
            Rectangle {
                anchors.centerIn: parent
                width: Enums.spacing.s
                height: parent.height
                radius: width / 2
                color: Enums.accentColor
                opacity: 0.4
            }
            
            Behavior on x {
                enabled: control.animated && !mouseArea.pressed
                NumberAnimation { duration: Enums.duration.fast }
            }
        }
        
        // Hover position indicator 悬停位置指示器
        Rectangle {
            id: hoverIndicator
            visible: control._hovered && !control._pressed
            x: Math.max(0, Math.min(mouseArea.mouseX - parent.anchors.margins - 1, parent.width - 2))
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Enums.spacing.xxs
            radius: width / 2
            color: Enums.accentColor
            opacity: 0.5
        }
    }
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        
        onClicked: function(mouse) {
            var pos = (mouse.x - waveformContainer.anchors.margins) / waveformContainer.width
            pos = Math.max(0, Math.min(1, pos))
            control.progress = pos
            control.clicked(pos)
            control.progressUpdated(pos)
        }
        
        onPositionChanged: function(mouse) {
            if (pressed) {
                var pos = (mouse.x - waveformContainer.anchors.margins) / waveformContainer.width
                pos = Math.max(0, Math.min(1, pos))
                control.progress = pos
                control.progressUpdated(pos)
            }
        }
    }

    Component.onCompleted: {
        if (waveformData.length === 0) {
            generateRandomWaveform(50)
        }
    }
}
