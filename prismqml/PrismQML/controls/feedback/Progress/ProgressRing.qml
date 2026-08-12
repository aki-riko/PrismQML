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
    // Keep progress finite and bounded for degenerate or inverted ranges 对退化或反向范围保持有限且有界
    readonly property real position: {
        var range = to - from
        if (!isFinite(range) || range <= 0) return 0
        var ratio = (value - from) / range
        if (!isFinite(ratio)) return 0
        return Math.max(0, Math.min(1, ratio))
    }
    // Custom color props (per-theme) 颜色自定义属性（分主题）
    property color color: Enums.accentColor
    property color fillColorLight: color
    property color fillColorDark: color
    property color trackColorLight: Enums.stateColor.track
    property color trackColorDark: Enums.isVintageTicket
        ? Enums.stateColor.progressTrack : Enums.stateColor.whiteOverlay
    readonly property color progressColor: Enums.isDark ? fillColorDark : fillColorLight
    readonly property color backgroundColor: Enums.isDark ? trackColorDark : trackColorLight
    readonly property color trackColor: backgroundColor
    property int spinDuration: Enums.progressRingMetrics.spinDuration
    
    // ==================== Public Methods 公开方法 ====================
    function _requestCanvasPaint() {
        if (canvasLoader.item) canvasLoader.item.requestPaint()
    }
    function setRange(min, max) { from = min; to = max }
    function pause() { paused = true }
    function resume() { paused = false }
    function start() { indeterminate = true; paused = false }
    function stop() { indeterminate = false }
    function setFillColor(light, dark) { fillColorLight = light; fillColorDark = dark }
    function setTrackColor(light, dark) { trackColorLight = light; trackColorDark = dark }
    
    implicitWidth: Enums.controlSize.progressRingSize   // Default ring size 默认环形尺寸
    implicitHeight: Enums.controlSize.progressRingSize  // Default ring size 默认环形尺寸

    onValueChanged: _requestCanvasPaint()
    onPositionChanged: _requestCanvasPaint()
    onIndeterminateChanged: _requestCanvasPaint()
    onIndeterminateStyleChanged: _requestCanvasPaint()
    onStrokeWidthChanged: _requestCanvasPaint()
    onTrackColorChanged: _requestCanvasPaint()
    onProgressColorChanged: _requestCanvasPaint()

    Loader {
        id: canvasLoader

        anchors.fill: parent
        active: !control.indeterminate
        sourceComponent: canvasComponent
    }

    Component {
        id: canvasComponent

        Canvas {
            objectName: "progressRingCanvas"
            rotation: -90

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()

                var cx = width / 2
                var cy = height / 2
                var r = Math.min(cx, cy) - control.strokeWidth / 2

                if (control.trackColor.a > 0) {
                    ctx.beginPath()
                    ctx.arc(cx, cy, r, 0, Math.PI * 2)
                    ctx.strokeStyle = control.trackColor
                    ctx.lineWidth = control.strokeWidth
                    ctx.stroke()
                }

                // Progress arc 进度弧
                ctx.beginPath()
                ctx.arc(cx, cy, r, 0, Math.PI * 2 * control.position)
                ctx.strokeStyle = control.progressColor
                ctx.lineCap = "round"
                ctx.lineWidth = control.strokeWidth
                ctx.stroke()
            }

            Component.onCompleted: requestPaint()
        }
    }
    
    // Indeterminate animation 不确定进度动画(伸缩弧脉动)
    Loader {
        id: indeterminateArcLoader

        anchors.fill: parent
        active: control.indeterminate
        sourceComponent: indeterminateArcComponent
    }

    Component {
        id: indeterminateArcComponent

        IndeterminateArcImpl {
            id: indeterminateArc
            objectName: "progressRingIndeterminateArc"
            anchors.fill: parent
            running: !control.paused && control.visible
            color: control.progressColor
            trackColor: control.trackColor
            strokeWidth: control.strokeWidth
            style: control.indeterminateStyle
            fixedArcSweep: control.indeterminateFixedArcSweep
            dotSize: control.indeterminateDotSize
            dotRadius: control.indeterminateDotRadius
            dotTopMargin: control.indeterminateDotTopMargin
            spinDuration: control.spinDuration
        }
    }
}
