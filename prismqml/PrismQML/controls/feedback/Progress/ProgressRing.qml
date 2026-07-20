// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"

// ProgressRing - 环形进度条（支持主题）
Item {
    id: control
    
    property real value: 0
    property real from: 0
    property real to: 100
    property bool indeterminate: false
    property bool paused: false
    property int strokeWidth: Enums.controlSize.progressRingStroke
    property int indeterminateStyle: Enums.progress.indeterminate_style_pulse
    property real indeterminateFixedArcSweep: Enums.progressRingMetrics.fixedArcSweep
    property real indeterminateDotSize: Enums.progressRingMetrics.orbitDotSize
    property real indeterminateDotRadius: Enums.progressRingMetrics.orbitDotRadius
    property real indeterminateDotTopMargin: Enums.progressRingMetrics.orbitDotTopMargin
    readonly property real position: (value - from) / (to - from)
    // Custom color props (per-theme) 颜色自定义属性（分主题）
    property color color: Enums.accentColor
    property color fillColorLight: color
    property color fillColorDark: color
    property color trackColorLight: Enums.stateColor.track
    property color trackColorDark: Enums.isPrismDesign ? Enums.stateColor.track : Enums.stateColor.whiteOverlay
    readonly property color progressColor: Enums.isDark ? fillColorDark : fillColorLight
    readonly property color backgroundColor: Enums.isDark ? trackColorDark : trackColorLight
    readonly property color trackColor: backgroundColor
    property alias spinDuration: indeterminateArc.spinDuration
    
    // ==================== Public Methods 公开方法 ====================
    function setRange(min, max) { from = min; to = max }
    function pause() { paused = true }
    function resume() { paused = false }
    function start() { indeterminate = true; paused = false }
    function stop() { indeterminate = false }
    function setFillColor(light, dark) { fillColorLight = light; fillColorDark = dark }
    function setTrackColor(light, dark) { trackColorLight = light; trackColorDark = dark }
    
    implicitWidth: Enums.controlSize.progressRingSize   // Default ring size 默认环形尺寸
    implicitHeight: Enums.controlSize.progressRingSize  // Default ring size 默认环形尺寸

    onValueChanged: canvas.requestPaint()
    onPositionChanged: canvas.requestPaint()
    onIndeterminateChanged: canvas.requestPaint()
    onIndeterminateStyleChanged: canvas.requestPaint()
    onStrokeWidthChanged: canvas.requestPaint()
    onTrackColorChanged: canvas.requestPaint()
    onProgressColorChanged: canvas.requestPaint()
    Component.onCompleted: canvas.requestPaint()
    
    Canvas {
        id: canvas
        anchors.fill: parent
        rotation: -90
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            var cx = width / 2
            var cy = height / 2
            var r = Math.min(cx, cy) - strokeWidth / 2
            
            // Orbit-dot mode uses its legacy Rectangle track. 绕圈圆点模式使用原有 Rectangle 底环。
            if (trackColor.a > 0 && (!indeterminate ||
                    indeterminateStyle !== Enums.progress.indeterminate_style_orbit_dot)) {
                ctx.beginPath()
                ctx.arc(cx, cy, r, 0, Math.PI * 2)
                ctx.strokeStyle = trackColor
                ctx.lineWidth = strokeWidth
                ctx.stroke()
            }
            
            // Progress arc 进度弧
            if (!indeterminate) {
                ctx.beginPath()
                ctx.arc(cx, cy, r, 0, Math.PI * 2 * position)
                ctx.strokeStyle = control.progressColor
                ctx.lineCap = "round"
                ctx.lineWidth = strokeWidth
                ctx.stroke()
            }
        }
    }
    
    // Indeterminate animation 不确定进度动画(伸缩弧脉动)
    IndeterminateArcImpl {
        id: indeterminateArc
        anchors.fill: parent
        visible: indeterminate
        running: indeterminate && !paused
        color: control.progressColor
        trackColor: control.trackColor
        strokeWidth: control.strokeWidth
        style: control.indeterminateStyle
        fixedArcSweep: control.indeterminateFixedArcSweep
        dotSize: control.indeterminateDotSize
        dotRadius: control.indeterminateDotRadius
        dotTopMargin: control.indeterminateDotTopMargin
    }
}
