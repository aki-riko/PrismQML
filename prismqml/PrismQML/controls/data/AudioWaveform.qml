// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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

    // ==================== Internal Props 内部属性 ====================
    property real _hoverScaleProgress: _hovered ? 1.0 : 0.0
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool _hovered: mouseArea.containsMouse
    readonly property bool _pressed: mouseArea.pressed
    readonly property int _waveformRadius: Enums.radius.large
    readonly property int _waveformInnerRadius: Enums.radius.small
    readonly property color _waveformBorderColor: control._hovered ? Enums.accentColor : Enums.stateColor.cardBorder
    readonly property color _progressOverlayColor: Enums.stateColor.accentSubtle
    readonly property var _safeWaveformData: _normalizeWaveformData(waveformData)
    readonly property real _safeProgress: isFinite(progress) ? Math.max(0, Math.min(1, progress)) : 0
    readonly property int _safeBarWidth: Math.max(1, barWidth)
    readonly property int _safeBarSpacing: Math.max(0, barSpacing)
    readonly property real _barBaseScale: 1.0
    readonly property real _barHoverXScale: 1.05
    readonly property real _barHoverYScale: 1.02
    readonly property Gradient _playedGradient: Gradient {
        orientation: Gradient.Vertical
        GradientStop { position: 0.0; color: control.progressColorEnd }
        GradientStop { position: 1.0; color: control.progressColor }
    }
    readonly property Gradient _unplayedGradient: Gradient {
        orientation: Gradient.Vertical
        GradientStop { position: 0.0; color: control.waveColorEnd }
        GradientStop { position: 1.0; color: control.waveColor }
    }

    // ==================== Signals 信号 ====================
    signal clicked(real position)  // Click position 0-1 点击位置
    signal progressUpdated(real newProgress)
    
    // ==================== Public Methods 公开方法 ====================
    // Set source (alias for setWaveformData) 设置音频源
    function setSource(src) { /* Use setWaveformData instead */ }

    // Demo data generator 示例数据生成
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

    // ==================== Internal Methods 内部方法 ====================
    function _normalizeWaveformData(value) {
        if (!value || typeof value.length !== "number") return []
        var normalized = []
        for (var i = 0; i < value.length; i++) {
            var sample = value[i]
            normalized.push(typeof sample === "number" && isFinite(sample)
                            ? Math.max(0, Math.min(1, sample)) : 0)
        }
        return normalized
    }

    function _positionAt(mouseX) {
        var span = waveformContainer.width
        if (!(span > 0) || !isFinite(span)) return 0
        var position = (mouseX - waveformContainer.anchors.margins) / span
        return isFinite(position) ? Math.max(0, Math.min(1, position)) : 0
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: 80

    Component.onCompleted: {
        if (_safeWaveformData.length === 0) {
            generateRandomWaveform(50)
        }
    }

    // ==================== Content 内容 ====================
    // Background card 背景卡片
    ShadowedRectangle {
        id: background
        anchors.fill: parent
        color: control.backgroundColor
        radius: control._waveformRadius
        border.width: Enums.border.thin
        border.color: control._waveformBorderColor
        shadowLevel: control._hovered ? Enums.shadow.level4 : Enums.shadow.level2
        
        Behavior on border.color {
            enabled: control.animated
            ColorAnimation { duration: Enums.duration.fast }
        }
    }
    
    // Waveform container 波形容器
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
            width: parent.width * control._safeProgress
            color: control._progressOverlayColor
            radius: control._waveformInnerRadius
            
            Behavior on width {
                enabled: control.animated && !mouseArea.pressed
                NumberAnimation { duration: Enums.duration.fast }
            }
        }
        
        // Waveform bars 波形条
        Item {
            id: waveformBars

            readonly property int _sampleCount: control._safeWaveformData.length
            readonly property real _pitch: control._safeBarWidth + control._safeBarSpacing
            readonly property real _contentWidth:
                _sampleCount > 0
                    ? _sampleCount * control._safeBarWidth
                      + (_sampleCount - 1) * control._safeBarSpacing
                    : 0
            readonly property real _viewportLeft:
                Math.max(0, (width - waveformContainer.width) / 2)
            readonly property real _viewportRight:
                Math.min(width, _viewportLeft + waveformContainer.width)
            readonly property int _firstVisibleIndex:
                _sampleCount > 0
                    ? Math.max(0, Math.min(
                        _sampleCount - 1, Math.floor(_viewportLeft / _pitch)
                    )) : 0
            readonly property int _visibleCount:
                _sampleCount > 0
                    ? Math.min(
                        _sampleCount - _firstVisibleIndex,
                        Math.max(0, Math.ceil(
                            (_viewportRight - _firstVisibleIndex * _pitch) / _pitch
                        ) + 1)
                    ) : 0

            objectName: "waveformBars"
            anchors.centerIn: parent
            width: _contentWidth
            height: parent.height
            
            Repeater {
                model: waveformBars._visibleCount
                
                Rectangle {
                    id: bar

                    readonly property int _dataIndex:
                        waveformBars._firstVisibleIndex + index
                    readonly property real _positionRatio:
                        control._safeWaveformData.length > 0
                            ? _dataIndex / control._safeWaveformData.length : 0
                    readonly property bool _played: bar._positionRatio < control._safeProgress

                    x: _dataIndex * waveformBars._pitch
                    width: control._safeBarWidth
                    height: Math.max(
                        Enums.spacing.xs,
                        control._safeWaveformData[_dataIndex] * waveformBars.height * 0.9
                    )
                    radius: width / 2
                    anchors.verticalCenter: parent.verticalCenter
                    
                    // Gradient based on position and progress 基于位置和进度的渐变
                    gradient: Enums.isVintageTicket ? null
                        : (bar._played ? control._playedGradient : control._unplayedGradient)
                    color: _played ? control.progressColor : control.waveColor
                    
                    // Subtle glow effect for active bars 活跃条的微妙发光效果
                    opacity: bar._played ? 1.0 : (control._hovered ? 0.85 : 0.7)
                    
                    // Scale animation on hover 悬停时的缩放动画
                    transform: Scale {
                        origin.x: bar.width / 2
                        origin.y: bar.height / 2
                        xScale: control._barBaseScale
                            + (control._barHoverXScale - control._barBaseScale)
                              * control._hoverScaleProgress
                        yScale: control._barBaseScale
                            + (control._barHoverYScale - control._barBaseScale)
                              * control._hoverScaleProgress
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
            visible: control.showProgressIndicator && control._safeProgress > 0
            x: parent.width * control._safeProgress - 1
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
    
    // Interaction 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        
        onClicked: function(mouse) {
            var pos = control._positionAt(mouse.x)
            control.progress = pos
            control.clicked(pos)
            control.progressUpdated(pos)
        }
        
        onPositionChanged: function(mouse) {
            if (pressed) {
                var pos = control._positionAt(mouse.x)
                control.progress = pos
                control.progressUpdated(pos)
            }
        }
    }

    Behavior on _hoverScaleProgress {
        enabled: control.animated
        NumberAnimation {
            duration: Enums.duration.medium
            easing.type: Easing.OutCubic
        }
    }

}
