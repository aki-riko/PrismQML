// BarChartGeometry - Cached multi-series bar geometry 多系列柱状图缓存几何
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function _valueToY(value, height, rangeMin, rangeMax) {
    var range = rangeMax - rangeMin
    if (range === 0) return height / 2
    return height - ((value - rangeMin) / range) * height
}

function average(values) {
    if (!values || values.length === 0) return 0
    var sum = 0
    for (var index = 0; index < values.length; index++) sum += values[index]
    return sum / values.length
}

function findMinMaxIndices(values) {
    if (!values || values.length === 0) {
        return { minIdx: -1, maxIdx: -1, minVal: 0, maxVal: 0 }
    }
    var minIdx = 0
    var maxIdx = 0
    for (var index = 1; index < values.length; index++) {
        if (values[index] < values[minIdx]) minIdx = index
        if (values[index] > values[maxIdx]) maxIdx = index
    }
    return {
        minIdx: minIdx, maxIdx: maxIdx,
        minVal: values[minIdx], maxVal: values[maxIdx]
    }
}

function _lowerBoundBarX(positions, targetX) {
    var low = 0
    var high = positions.length
    while (low < high) {
        var middle = Math.floor((low + high) / 2)
        if (positions[middle].x < targetX) low = middle + 1
        else high = middle
    }
    return low
}

function nearestBarHit(seriesPositions, x, y, hoverRadius) {
    var nearestDistance = hoverRadius
    var foundIndex = -1
    var foundSeriesIndex = -1
    var candidateCount = 0
    for (var seriesIndex = 0; seriesIndex < seriesPositions.length; seriesIndex++) {
        var positions = seriesPositions[seriesIndex] || []
        var start = _lowerBoundBarX(positions, x - hoverRadius)
        for (var index = start; index < positions.length; index++) {
            var position = positions[index]
            if (position.x >= x + hoverRadius) break
            candidateCount++
            var distance = Math.abs(x - position.x)
            if (distance < nearestDistance &&
                    y >= position.barTop && y <= position.barBottom) {
                nearestDistance = distance
                foundIndex = index
                foundSeriesIndex = seriesIndex
            }
        }
    }
    return {
        barIndex: foundIndex,
        seriesIndex: foundSeriesIndex,
        candidateCount: candidateCount
    }
}

function barPosition(seriesPositions, seriesIndex, barIndex) {
    var positions = seriesPositions[seriesIndex]
    return positions && positions[barIndex] ? positions[barIndex] : null
}

function dirtyBounds(position, barWidth, canvasWidth, canvasHeight, padding) {
    if (!position) return null
    var left = Math.max(0, Math.floor(position.barX - padding))
    var top = Math.max(0, Math.floor(position.barTop - padding))
    var right = Math.min(canvasWidth, Math.ceil(position.barX + barWidth + padding))
    var bottom = Math.min(canvasHeight, Math.ceil(position.barBottom + padding))
    return { x: left, y: top, width: right - left, height: bottom - top }
}

function unitedBounds(first, second) {
    if (!first) return second
    if (!second) return first
    var left = Math.min(first.x, second.x)
    var top = Math.min(first.y, second.y)
    var right = Math.max(first.x + first.width, second.x + second.width)
    var bottom = Math.max(first.y + first.height, second.y + second.height)
    return { x: left, y: top, width: right - left, height: bottom - top }
}

function build(seriesData, dataLength, canvasWidth, canvasHeight,
               rangeMin, rangeMax) {
    if (dataLength === 0) {
        return {
            seriesPositions: [], averageYs: [], dataLength: 0,
            barWidth: 0, baseline: _valueToY(0, canvasHeight, rangeMin, rangeMax)
        }
    }
    var seriesCount = seriesData.length
    var groupWidth = canvasWidth / dataLength
    var barWidth = groupWidth * 0.7 / seriesCount
    var barSpacing = barWidth * 0.1
    var baseline = _valueToY(0, canvasHeight, rangeMin, rangeMax)
    var valueRange = rangeMax - rangeMin
    var allPositions = []
    var averageYs = []

    for (var seriesIndex = 0; seriesIndex < seriesCount; seriesIndex++) {
        var seriesItem = seriesData[seriesIndex]
        var values = seriesItem.values || []
        var positions = []
        for (var index = 0; index < values.length; index++) {
            var value = values[index]
            var barX = index * groupWidth +
                       (groupWidth - barWidth * seriesCount -
                        barSpacing * (seriesCount - 1)) / 2 +
                       seriesIndex * (barWidth + barSpacing)
            positions.push({
                x: barX + barWidth / 2,
                y: baseline,
                value: value,
                positive: value >= 0,
                barX: barX,
                barTop: baseline,
                barBottom: baseline,
                barHeight: 0,
                finalHeight: valueRange === 0
                             ? 0 : Math.abs(value) / valueRange * canvasHeight
            })
        }
        allPositions.push(positions)
        averageYs.push(_valueToY(
            average(values), canvasHeight, rangeMin, rangeMax
        ))
    }
    return {
        seriesPositions: allPositions,
        averageYs: averageYs,
        dataLength: dataLength,
        barWidth: barWidth,
        baseline: baseline
    }
}

function update(seriesPositions, progress, baseline) {
    var updateCount = 0
    for (var seriesIndex = 0; seriesIndex < seriesPositions.length; seriesIndex++) {
        var positions = seriesPositions[seriesIndex]
        for (var index = 0; index < positions.length; index++) {
            var position = positions[index]
            var barHeight = position.finalHeight * progress
            var barTop = position.positive ? baseline - barHeight : baseline
            position.barHeight = barHeight
            position.barTop = barTop
            position.barBottom = barTop + barHeight
            position.y = position.positive ? barTop : barTop + barHeight
            updateCount++
        }
    }
    return updateCount
}
