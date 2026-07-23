// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"

// CircularGauge - Circular gauge with theme support 仪表盘
Item {
    id: control
    
    property real value: 0
    property real minValue: 0
    property real maxValue: 100
    property string unit: ""
    property alias title: control.unit
    property int startAngle: -135
    property int endAngle: 135
    // Keep gauge progress finite and bounded for degenerate ranges 对退化范围保持有限且有界
    readonly property real progress: {
        var range = maxValue - minValue
        if (!isFinite(range) || range <= 0) return 0
        var ratio = (value - minValue) / range
        if (!isFinite(ratio)) return 0
        return Math.max(0, Math.min(1, ratio))
    }
    readonly property color _gaugeTrackColor: Enums.stateColor.sliderTrack
    readonly property color _gaugeValueColor: Enums.accentColor
    readonly property color _gaugeLabelColor: Enums.textColor.tertiary
    readonly property int _gaugeStrokeWidth: Enums.spacing.l

    // ==================== Public Methods 公开方法 ====================
    function getValue() { return value }

    onValueChanged: gauge.requestPaint()
    onProgressChanged: gauge.requestPaint()
    Component.onCompleted: gauge.requestPaint()

    implicitWidth: 150
    implicitHeight: 150
    
    Canvas {
        id: gauge
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            
            var cx = width / 2
            var cy = height / 2
            var r = Math.min(cx, cy) - 10
            
            var startRad = startAngle * Math.PI / 180
            var endRad = endAngle * Math.PI / 180
            var progressRad = startRad + (endRad - startRad) * progress
            
            // Background arc 背景弧
            ctx.beginPath()
            ctx.arc(cx, cy, r, startRad, endRad)
            ctx.strokeStyle = control._gaugeTrackColor
            ctx.lineWidth = control._gaugeStrokeWidth
            ctx.lineCap = "round"
            ctx.stroke()
            
            // Progress arc 进度弧
            ctx.beginPath()
            ctx.arc(cx, cy, r, startRad, progressRad)
            ctx.strokeStyle = control._gaugeValueColor
            ctx.lineWidth = control._gaugeStrokeWidth
            ctx.lineCap = "round"
            ctx.stroke()
        }
    }
    
    Column {
        anchors.centerIn: parent
        spacing: Enums.spacing.xxs
        
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            type: Enums.label.type_body_strong
            text: Math.round(value)
            font.pixelSize: Enums.typography.metric
            color: control._gaugeValueColor
        }
        
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            type: Enums.label.type_caption
            text: unit
            color: control._gaugeLabelColor
            visible: text !== ""
        }
    }
}
