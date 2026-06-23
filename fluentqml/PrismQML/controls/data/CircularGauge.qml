// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    readonly property real progress: (value - minValue) / (maxValue - minValue)

    // ==================== Public Methods 公共方法 ====================
    function getValue() { return value }

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
            ctx.strokeStyle = Enums.stateColor.border
            ctx.lineWidth = 12
            ctx.lineCap = "round"
            ctx.stroke()
            
            // Progress arc 进度弧
            ctx.beginPath()
            ctx.arc(cx, cy, r, startRad, progressRad)
            ctx.strokeStyle = Enums.accentColor
            ctx.lineWidth = 12
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
            color: Enums.accentColor
        }
        
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            type: Enums.label.type_caption
            text: unit
            color: Enums.textColor.tertiary
            visible: text !== ""
        }
    }
    
    onValueChanged: gauge.requestPaint()
    onProgressChanged: gauge.requestPaint()
    Component.onCompleted: gauge.requestPaint()
}
