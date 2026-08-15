// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as DataInternal

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
    readonly property bool _hovered: contentLayer.hovered
    readonly property bool _pressed: contentLayer.pressed
    readonly property int _waveformRadius: Enums.surfaceRadius(Enums.radius.large)
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
        var span = contentLayer.waveformContainer.width
        if (!(span > 0) || !isFinite(span)) return 0
        var position = (mouseX - contentLayer.waveformContainer.anchors.margins) / span
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
    DataInternal.AudioWaveformContent {
        id: contentLayer
        waveformControl: control
    }

    HoverBehavior on _hoverScaleProgress {
        active: control._hovered && !control._pressed
        animationEnabled: control.animated
        enterDuration: Enums.duration.medium
        easingType: Easing.OutCubic
    }
}
