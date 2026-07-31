// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."

// ScatterChartContent - Scatter chart rendering component 散点图渲染组件
// Fluent Design style: clean scatter points with subtle hover effects
// Fluent Design 风格：简洁散点+微妙悬停效果

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var series         // [{name: "", data: [[x,y],...], color: "", symbolSize: 10, type: "scatter"|"effectScatter"}, ...]
    required property var dataRange      // {xMin, xMax, yMin, yMax}
    required property bool animated      // Enable animation 启用动画
    required property bool showGrid      // Show grid lines 显示网格线
    
    // ==================== Public Props 公开属性 ====================
    property int hoveredSeriesIndex: -1
    property int hoveredPointIndex: -1
    property int defaultSymbolSize: 10       // Default symbol size if not specified in series 默认点大小

    // ==================== Internal Props 内部属性 ====================
    property var pointPositions: []
    property real tooltipX: 0
    property real tooltipY: 0
    property real dataX: 0
    property real dataY: 0
    property var _pointBuckets: ({})
    property bool _pointGeometryDirty: true
    property int _pointGeometryBuildCount: 0
    property int _lastHoverCandidateCount: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property real _normalHitRadius: 15
    readonly property real _effectHitRadius: 20
    readonly property real _pointBucketSize: _effectHitRadius * 2
    readonly property real _defaultEffectSymbolSize: 16

    // ==================== Signals 信号 ====================
    signal pointClicked(int pointIndex, var data)
    signal pointHovered(int seriesIndex, int pointIndex)

    // ==================== Internal Methods 内部方法 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function isEffectScatter(seriesItem) {
        return seriesItem && seriesItem.type === "effectScatter"
    }

    function _bucketKey(x, y) {
        return Math.floor(x / _pointBucketSize) + ":" + Math.floor(y / _pointBucketSize)
    }

    function _addPointToBucket(buckets, pointIndex, x, y) {
        var key = _bucketKey(x, y)
        var bucket = buckets[key]
        if (!bucket) {
            bucket = []
            buckets[key] = bucket
        }
        bucket.push(pointIndex)
    }

    function _appendSeriesGeometry(points, buckets, seriesIndex, isEffect,
                                   canvasHeight, range, xScale, yScale) {
        var seriesData = series[seriesIndex] || {}
        var data = seriesData.data || []
        for (var pointIndex = 0; pointIndex < data.length; pointIndex++) {
            var dataPoint = data[pointIndex]
            var x = (dataPoint[0] - range.xMin) * xScale
            var y = canvasHeight - (dataPoint[1] - range.yMin) * yScale
            var flatIndex = points.length
            points.push({
                x: x, y: y,
                seriesIndex: seriesIndex, pointIndex: pointIndex,
                dataX: dataPoint[0], dataY: dataPoint[1],
                isEffect: isEffect
            })
            _addPointToBucket(buckets, flatIndex, x, y)
        }
    }

    function _rebuildPointGeometry(canvasWidth, canvasHeight) {
        var range = dataRange
        var xSpan = range.xMax - range.xMin
        var ySpan = range.yMax - range.yMin
        var points = []
        var buckets = {}
        if (xSpan > 0 && ySpan > 0 && isFinite(xSpan) && isFinite(ySpan)) {
            var xScale = canvasWidth / xSpan
            var yScale = canvasHeight / ySpan
            for (var pass = 0; pass < 2; pass++) {
                var wantEffect = pass === 1
                for (var seriesIndex = 0; seriesIndex < series.length; seriesIndex++) {
                    if (isEffectScatter(series[seriesIndex]) === wantEffect) {
                        _appendSeriesGeometry(points, buckets, seriesIndex, wantEffect,
                                              canvasHeight, range, xScale, yScale)
                    }
                }
            }
        }
        pointPositions = points
        _pointBuckets = buckets
        _pointGeometryDirty = false
        _pointGeometryBuildCount++
    }

    function _invalidatePointGeometry() {
        _pointGeometryDirty = true
        canvas.requestPaint()
    }

    function _nearbyPointIndices(x, y) {
        var column = Math.floor(x / _pointBucketSize)
        var row = Math.floor(y / _pointBucketSize)
        var candidates = []
        for (var dx = -1; dx <= 1; dx++) {
            for (var dy = -1; dy <= 1; dy++) {
                var bucket = _pointBuckets[(column + dx) + ":" + (row + dy)] || []
                for (var index = 0; index < bucket.length; index++) candidates.push(bucket[index])
            }
        }
        _lastHoverCandidateCount = candidates.length
        return candidates
    }

    function _nearestPointIndex(x, y) {
        if (_pointGeometryDirty) _rebuildPointGeometry(width, height)
        var candidates = _nearbyPointIndices(x, y)
        var nearestIndex = -1
        var nearestDistanceSquared = _effectHitRadius * _effectHitRadius
        for (var index = 0; index < candidates.length; index++) {
            var flatIndex = candidates[index]
            var point = pointPositions[flatIndex]
            var deltaX = x - point.x
            var deltaY = y - point.y
            var distanceSquared = deltaX * deltaX + deltaY * deltaY
            var hitRadius = point.isEffect ? _effectHitRadius : _normalHitRadius
            if (distanceSquared < hitRadius * hitRadius && distanceSquared < nearestDistanceSquared) {
                nearestDistanceSquared = distanceSquared
                nearestIndex = flatIndex
            }
        }
        return nearestIndex
    }

    // Repaint on hover change 悬浮变化时重绘
    onHoveredSeriesIndexChanged: canvas.requestPaint()
    onHoveredPointIndexChanged: canvas.requestPaint()
    onSeriesChanged: _invalidatePointGeometry()
    onDataRangeChanged: _invalidatePointGeometry()
    onDefaultSymbolSizeChanged: canvas.requestPaint()

    // ==================== Content 内容 ====================
    // Canvas 画布
    Canvas {
        id: canvas

        property real animProgress: 0

        function drawNormalPoint(ctx, point, color, symbolSize, hovered) {
            ctx.beginPath()
            ctx.fillStyle = color
            ctx.globalAlpha = hovered ? 1.0 : 0.8
            ctx.arc(point.x, point.y, symbolSize / 2, 0, Math.PI * 2)
            ctx.fill()
            ctx.globalAlpha = 1
        }

        function drawEffectPoint(ctx, point, color, symbolSize, hovered) {
            ctx.beginPath()
            ctx.strokeStyle = color
            ctx.lineWidth = 2
            ctx.globalAlpha = 0.4
            ctx.arc(point.x, point.y, symbolSize / 2 + 4, 0, Math.PI * 2)
            ctx.stroke()

            ctx.beginPath()
            ctx.fillStyle = color
            ctx.globalAlpha = hovered ? 1.0 : 0.9
            ctx.arc(point.x, point.y, symbolSize / 2, 0, Math.PI * 2)
            ctx.fill()
            ctx.globalAlpha = 1
        }

        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            if (root._pointGeometryDirty) root._rebuildPointGeometry(width, height)
            
            // Fluent Design: light grid lines 轻量网格线
            if (root.showGrid) {
                ctx.strokeStyle = Enums.chartColors.gridLine
                ctx.lineWidth = 1
                
                for (var i = 0; i <= 5; i++) {
                    var y = i * height / 5
                    ctx.beginPath()
                    ctx.moveTo(0, y)
                    ctx.lineTo(width, y)
                    ctx.stroke()
                }
                
                for (var j = 0; j <= 5; j++) {
                    var x = j * width / 5
                    ctx.beginPath()
                    ctx.moveTo(x, 0)
                    ctx.lineTo(x, height)
                    ctx.stroke()
                }
            }
            
            // Draw scatter points 绘制散点
            var progress = root.animated ? animProgress : 1
            var colorCache = []
            var sizeCache = []
            for (var index = 0; index < root.pointPositions.length; index++) {
                var point = root.pointPositions[index]
                var seriesIndex = point.seriesIndex
                if (colorCache[seriesIndex] === undefined) {
                    var seriesData = root.series[seriesIndex] || {}
                    colorCache[seriesIndex] = root.getSeriesColor(seriesIndex)
                    sizeCache[seriesIndex] = seriesData.symbolSize ||
                            (point.isEffect ? root._defaultEffectSymbolSize : root.defaultSymbolSize)
                }
                var hovered = seriesIndex === root.hoveredSeriesIndex &&
                              point.pointIndex === root.hoveredPointIndex
                var hoverScale = hovered && !point.isEffect ? 1.3 : 1
                var symbolSize = sizeCache[seriesIndex] * progress * hoverScale
                if (point.isEffect) {
                    drawEffectPoint(ctx, point, colorCache[seriesIndex], symbolSize, hovered)
                } else {
                    drawNormalPoint(ctx, point, colorCache[seriesIndex], symbolSize, hovered)
                }
            }
        }

        onWidthChanged: root._invalidatePointGeometry()
        onHeightChanged: root._invalidatePointGeometry()
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                chartAnimation.restart()
            } else {
                animProgress = 1
                requestPaint()
            }
        }
        onAnimProgressChanged: requestPaint()
        
        NumberAnimation {
            id: chartAnimation
            target: canvas
            property: "animProgress"
            from: 0
            to: 1
            duration: Enums.duration.chart
            easing.type: Easing.OutQuint
        }
    }

    // Mouse area 鼠标区域
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredSeriesIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onPositionChanged: (mouse) => {
            var flatIndex = root._nearestPointIndex(mouse.x, mouse.y)
            var point = flatIndex >= 0 ? root.pointPositions[flatIndex] : null
            var foundSeriesIndex = point ? point.seriesIndex : -1
            var foundPointIndex = point ? point.pointIndex : -1
            root.pointHovered(foundSeriesIndex, foundPointIndex)
            if (point) {
                root.tooltipX = point.x
                root.tooltipY = point.y
                root.dataX = point.dataX
                root.dataY = point.dataY
            }
        }
        
        onExited: root.pointHovered(-1, -1)
        
        onClicked: {
            if (root.hoveredSeriesIndex >= 0 && root.hoveredPointIndex >= 0) {
                root.pointClicked(root.hoveredPointIndex, {
                    seriesIndex: root.hoveredSeriesIndex,
                    seriesName: root.series[root.hoveredSeriesIndex].name,
                    x: root.dataX,
                    y: root.dataY,
                    isEffect: root.series[root.hoveredSeriesIndex].type === "effectScatter"
                })
            }
        }
    }
}
