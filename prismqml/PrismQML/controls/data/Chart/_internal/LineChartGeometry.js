// LineChartGeometry - Cached line chart geometry 折线图缓存几何
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function _valueToY(value, height, rangeMin, rangeMax) {
    var range = rangeMax - rangeMin
    if (range === 0) return height / 2
    return height - ((value - rangeMin) / range) * height
}

function buildSingle(chartData, canvasWidth, canvasHeight, boundaryGap,
                     padding, rangeMin, rangeMax) {
    var chartHeight = canvasHeight - padding * 2
    var chartWidth = canvasWidth - padding * 2
    var dataCount = chartData.length
    var stepX = boundaryGap ? chartWidth / dataCount : chartWidth / (dataCount - 1)
    var startX = boundaryGap ? padding + stepX / 2 : padding
    var yScale = canvasHeight > 0 ? chartHeight / canvasHeight : 0
    var baseline = padding + chartHeight
    var points = []
    for (var index = 0; index < dataCount; index++) {
        var targetY = padding + _valueToY(
            chartData[index].value, canvasHeight, rangeMin, rangeMax
        ) * yScale
        points.push({
            x: startX + index * stepX,
            y: baseline,
            finalY: targetY
        })
    }
    return {
        points: points,
        seriesPoints: [],
        maxLength: dataCount,
        baseline: baseline
    }
}

function buildSeries(seriesData, canvasWidth, canvasHeight, boundaryGap,
                     stacked, rangeMin, rangeMax) {
    var maxLength = 0
    var seriesIndex
    for (seriesIndex = 0; seriesIndex < seriesData.length; seriesIndex++) {
        var candidate = seriesData[seriesIndex]
        var candidateValues = candidate && candidate.values &&
                              typeof candidate.values.length === "number"
                              ? candidate.values : []
        if (candidateValues.length > maxLength) maxLength = candidateValues.length
    }
    var stepX = boundaryGap ? canvasWidth / maxLength : canvasWidth / (maxLength - 1)
    var startX = boundaryGap ? stepX / 2 : 0
    var cumulative = []
    for (var index = 0; index < maxLength; index++) cumulative.push(0)

    var allPoints = []
    for (seriesIndex = 0; seriesIndex < seriesData.length; seriesIndex++) {
        var seriesItem = seriesData[seriesIndex]
        var values = seriesItem && seriesItem.values &&
                     typeof seriesItem.values.length === "number"
                     ? seriesItem.values : []
        var points = []
        for (index = 0; index < values.length; index++) {
            var value = values[index] || 0
            if (stacked) cumulative[index] += value
            var mappedValue = stacked ? cumulative[index] : value
            points.push({
                x: startX + index * stepX,
                y: canvasHeight,
                finalY: _valueToY(
                    mappedValue, canvasHeight, rangeMin, rangeMax
                ),
                value: value,
                stackedValue: cumulative[index]
            })
        }
        allPoints.push(points)
    }
    return {
        points: [],
        seriesPoints: allPoints,
        maxLength: maxLength,
        baseline: canvasHeight
    }
}

function updatePoints(points, progress, baseline) {
    for (var index = 0; index < points.length; index++) {
        var point = points[index]
        point.y = baseline + (point.finalY - baseline) * progress
    }
    return points.length
}

function updateSeries(seriesPoints, progress, baseline) {
    var updateCount = 0
    for (var seriesIndex = 0; seriesIndex < seriesPoints.length; seriesIndex++) {
        updateCount += updatePoints(seriesPoints[seriesIndex], progress, baseline)
    }
    return updateCount
}

function _lowerBoundX(points, targetX) {
    var low = 0
    var high = points.length
    while (low < high) {
        var middle = Math.floor((low + high) / 2)
        if (points[middle].x < targetX) low = middle + 1
        else high = middle
    }
    return low
}

function dirtyBounds(points, index, canvasWidth, canvasHeight, padding) {
    if (!points || index < 0 || index >= points.length) return null
    var left = Math.max(0, points[index].x - padding)
    var right = Math.min(canvasWidth, points[index].x + padding)
    return { x: left, y: 0, width: right - left, height: canvasHeight }
}

function unitedBounds(first, second) {
    if (!first) return second
    if (!second) return first
    var left = Math.min(first.x, second.x)
    var right = Math.max(first.x + first.width, second.x + second.width)
    return {
        x: left, y: 0, width: right - left,
        height: Math.max(first.height, second.height)
    }
}

function firstNonEmpty(seriesPoints) {
    for (var index = 0; index < seriesPoints.length; index++) {
        if (seriesPoints[index] && seriesPoints[index].length > 0) {
            return seriesPoints[index]
        }
    }
    return []
}

function paintRange(points, region, fullPaint, pathPadding) {
    if (!points || fullPaint) {
        return { start: 0, end: points ? points.length : 0 }
    }
    var start = _lowerBoundX(points, region.x - pathPadding)
    var end = Math.min(
        points.length,
        _lowerBoundX(points, region.x + region.width + pathPadding)
    )
    return { start: start, end: end }
}
