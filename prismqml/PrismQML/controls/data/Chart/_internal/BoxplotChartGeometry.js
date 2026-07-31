// BoxplotChartGeometry - Boxplot dirty-region geometry 箱线图脏区几何
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function dirtyRect(index, dataLength, isHorizontal, width, height, padding) {
    if (index < 0 || index >= dataLength || dataLength === 0) return null
    var groupSize = isHorizontal ? height / dataLength : width / dataLength
    var start = Math.max(0, index * groupSize - padding)
    var axisSize = isHorizontal ? height : width
    var end = Math.min(axisSize, (index + 1) * groupSize + padding)
    return isHorizontal
        ? { x: 0, y: start, width: width, height: end - start }
        : { x: start, y: 0, width: end - start, height: height }
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

function paintRange(region, fullPaint, dataLength, groupSize,
                    isHorizontal, padding) {
    if (fullPaint || groupSize <= 0) return { start: 0, end: dataLength }
    var regionStart = isHorizontal ? region.y : region.x
    var regionSize = isHorizontal ? region.height : region.width
    return {
        start: Math.max(0, Math.floor((regionStart - padding) / groupSize)),
        end: Math.min(
            dataLength, Math.ceil((regionStart + regionSize + padding) / groupSize)
        )
    }
}
