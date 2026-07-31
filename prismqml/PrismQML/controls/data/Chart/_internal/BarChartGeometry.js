// BarChartGeometry - Cached multi-series bar geometry 多系列柱状图缓存几何
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function _valueToY(value, height, rangeMin, rangeMax) {
    var range = rangeMax - rangeMin
    if (range === 0) return height / 2
    return height - ((value - rangeMin) / range) * height
}

function _average(values) {
    if (!values || values.length === 0) return 0
    var sum = 0
    for (var index = 0; index < values.length; index++) sum += values[index]
    return sum / values.length
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
            _average(values), canvasHeight, rangeMin, rangeMax
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
