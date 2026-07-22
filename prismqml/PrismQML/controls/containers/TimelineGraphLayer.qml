// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// TimelineGraphLayer - Generic per-row graph renderer 通用时间线逐行图渲染器
Item {
    id: control

    required property var graphData
    required property bool showNode
    required property real nodeY
    required property bool selected
    property var palette: Enums.chartColors.extendedPalette
    property color nodeBackground: Enums.cardColor
    property color selectedColor: Enums.accentColor

    function _laneX(lane) {
        var safeLane = Math.max(0, Number(lane) || 0)
        return Enums.spacing.timelineGraphPadding
            + Enums.spacing.timelineGraphLane / 2
            + safeLane * Enums.spacing.timelineGraphLane
    }

    function _colorFor(index) {
        if (!palette || palette.length === 0) return Enums.accentColor
        var safeIndex = Math.abs(Math.floor(Number(index) || 0)) % palette.length
        return palette[safeIndex]
    }

    function _paintSegment(ctx, segment) {
        var fromX = _laneX(segment.fromLane)
        var toX = _laneX(segment.toLane)
        var startY = segment.startAtNode ? nodeY : 0
        var endY = segment.endAtNode ? nodeY : height
        var middleY = (startY + endY) / 2
        ctx.beginPath()
        ctx.moveTo(fromX, startY)
        if (fromX === toX) {
            ctx.lineTo(toX, endY)
        } else {
            ctx.bezierCurveTo(fromX, middleY, toX, middleY, toX, endY)
        }
        ctx.lineWidth = Enums.border.normal
        ctx.strokeStyle = _colorFor(segment.colorIndex)
        ctx.stroke()
    }

    function _paintNode(ctx, data) {
        var nodeX = _laneX(data.nodeLane)
        var nodeRadius = Enums.controlSize.timelineGraphNode / 2
        var outerRadius = nodeRadius + Enums.border.normal
        ctx.beginPath()
        ctx.arc(nodeX, nodeY, outerRadius, 0, Math.PI * 2)
        ctx.fillStyle = nodeBackground
        ctx.fill()
        ctx.beginPath()
        ctx.arc(nodeX, nodeY, nodeRadius, 0, Math.PI * 2)
        ctx.fillStyle = _colorFor(data.nodeColorIndex)
        ctx.fill()
        if (selected) {
            ctx.beginPath()
            ctx.arc(nodeX, nodeY, outerRadius + Enums.spacing.xxs, 0, Math.PI * 2)
            ctx.lineWidth = Enums.border.normal
            ctx.strokeStyle = selectedColor
            ctx.stroke()
        }
    }

    objectName: "timelineGraphLayer"

    onGraphDataChanged: graphCanvas.requestPaint()
    onShowNodeChanged: graphCanvas.requestPaint()
    onNodeYChanged: graphCanvas.requestPaint()
    onSelectedChanged: graphCanvas.requestPaint()
    onPaletteChanged: graphCanvas.requestPaint()
    onNodeBackgroundChanged: graphCanvas.requestPaint()
    onSelectedColorChanged: graphCanvas.requestPaint()
    onWidthChanged: graphCanvas.requestPaint()
    onHeightChanged: graphCanvas.requestPaint()

    Canvas {
        id: graphCanvas

        anchors.fill: parent
        antialiasing: true

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            var data = control.graphData || {}
            var segments = data.segments || []
            for (var index = 0; index < segments.length; index++)
                control._paintSegment(ctx, segments[index])
            if (control.showNode) control._paintNode(ctx, data)
        }
    }
}
