// BarChartPainter - Multi-series bar Canvas drawing 多系列柱状图 Canvas 绘制
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function _drawRoundedRect(ctx, x, y, width, height, radius) {
    if (width < 2 * radius) radius = width / 2
    if (height < 2 * radius) radius = height / 2
    ctx.beginPath()
    ctx.moveTo(x + radius, y)
    ctx.lineTo(x + width - radius, y)
    ctx.arcTo(x + width, y, x + width, y + radius, radius)
    ctx.lineTo(x + width, y + height)
    ctx.lineTo(x, y + height)
    ctx.lineTo(x, y + radius)
    ctx.arcTo(x, y, x + radius, y, radius)
    ctx.closePath()
}

function _intersects(position, barWidth, region) {
    return position.barX + barWidth >= region.x &&
           position.barX <= region.x + region.width &&
           position.barBottom >= region.y &&
           position.barTop <= region.y + region.height
}

function drawSeriesBars(ctx, positions, values, seriesIndex, color, barWidth,
                        region, fullPaint, hoveredSeriesIndex, hoveredIndex,
                        radius) {
    var drawCount = 0
    for (var index = 0; index < values.length; index++) {
        var position = positions[index]
        if (!fullPaint && !_intersects(position, barWidth, region)) continue
        var hovered = seriesIndex === hoveredSeriesIndex && index === hoveredIndex
        ctx.fillStyle = hovered ? Qt.lighter(color, 1.1) : color
        _drawRoundedRect(ctx, position.barX, position.barTop,
                         barWidth, position.barHeight, radius)
        ctx.fill()
        drawCount++
    }
    return drawCount
}

function drawAverageLine(ctx, averageY, color, canvasWidth, strokeAlpha) {
    ctx.beginPath()
    var chartColor = Qt.color(color)
    ctx.strokeStyle = Qt.rgba(
        chartColor.r, chartColor.g, chartColor.b, strokeAlpha
    )
    ctx.lineWidth = 1
    ctx.setLineDash([4, 4])
    ctx.moveTo(0, averageY)
    ctx.lineTo(canvasWidth, averageY)
    ctx.stroke()
    ctx.setLineDash([])
}
