// RadarChartGeometry - Radar chart dirty-region geometry 雷达图脏区几何
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function dirtyBounds(seriesPoints, seriesIndex, pointIndex,
                     canvasWidth, canvasHeight, padding) {
    var points = seriesPoints[seriesIndex]
    var point = points && points[pointIndex] ? points[pointIndex] : null
    if (!point) return null
    var left = Math.max(0, point.x - padding)
    var top = Math.max(0, point.y - padding)
    var right = Math.min(canvasWidth, point.x + padding)
    var bottom = Math.min(canvasHeight, point.y + padding)
    return {
        x: left, y: top, width: right - left, height: bottom - top
    }
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

function intersectsPoint(point, region, padding) {
    return point.x + padding >= region.x &&
           point.x - padding <= region.x + region.width &&
           point.y + padding >= region.y &&
           point.y - padding <= region.y + region.height
}
