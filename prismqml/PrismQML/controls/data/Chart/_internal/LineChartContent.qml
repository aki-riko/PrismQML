// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../data"
import "LineChartGeometry.js" as Geometry
import "LineChartPainter.js" as Painter

// LineChartContent - Multi-series line chart rendering component 多系列折线图渲染组件
// Modular design: uses LineChartPainter.js for drawing, LineChartMarkers.qml for markers 模块化设计：使用 LineChartPainter.js 绘制，LineChartMarkers.qml 标记


Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var chartData      // [{label: "", value: 0}, ...] - single series 单系列
    required property real maxValue      // Maximum value Y轴最大值
    required property color primaryColor // Line color 线条颜色
    required property bool smoothLine    // Use bezier curve 使用贝塞尔曲线
    required property bool isArea        // Is area chart 是否面积图
    
    // ==================== Public Props 公开属性 ====================
    property var series: []              // [{name: "", values: [], color: "", stack: ""}, ...] - multi series 多系列
    property bool showAverage: false     // Show average line (markLine) 显示平均线
    property bool showMinMax: false      // Show min/max markers (markPoint) 显示最大最小值标记
    property int hoveredIndex: -1
    property int hoveredSeriesIndex: -1
    property bool boundaryGap: true      // Gap at edges 边缘间距
    property bool showAreaGradient: false // Show gradient fill under line 渐变填充
    property bool stacked: false         // Stacked area chart 堆叠面积图
    property bool animated: false        // Line drawing animation 折线绘制动画
    // Enable pointer hover detection; disable it for dense data to reduce frame drops 启用鼠标悬停检测，密集数据可关闭以减少掉帧
    property bool hoverDetectEnabled: true
    // Source projection metadata keeps sliced points on original X coordinates 源投影元数据保证切片前后的点保持原始X坐标
    property var chartDataProjection: ({ sourceLength: chartData.length,
                                         sourceOffset: 0, sourceIndices: [] })
    property var seriesValueSources: []
    property real renderViewportStart: 0
    property real renderViewportEnd: 1

    // ==================== Internal Props 内部属性 ====================
    property var pointPositions: []       // For single series 单系列点位置
    property var seriesPointPositions: [] // For multi series 多系列点位置
    property real tooltipX: 0
    property real tooltipY: 0
    property real mouseX: 0
    property real mouseY: 0
    property int _lastHoverCandidateCount: 0
    property int _lastSeriesHoverCandidateCount: 0
    property var _lineGeometry: null
    property bool _lineGeometryDirty: true
    property int _lineGeometryBuildCount: 0
    property int _lastFramePointUpdateCount: 0
    property real _lineGeometryBaseline: 0
    property real _lastGeometryProgress: -1
    property int _lastFramePointDrawCount: 0
    property int _paintedHoverIndex: -1
    property int _paintedHoverSeriesIndex: -1

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isMultiSeries: series.length > 0
    readonly property int _dirtyPixelQuantum: _calculateDirtyPixelQuantum(
        Screen.devicePixelRatio
    )
    readonly property var _calculatedValueRange: _calculateValueRange()
    property real _displayRangeMin: _calculatedValueRange.min
    property real _displayRangeMax: _calculatedValueRange.max
    readonly property var valueRange: ({
        min: _displayRangeMin,
        max: _displayRangeMax
    })

    // ==================== Signals 信号 ====================
    signal pointClicked(int index, var data)
    signal pointHovered(int index)
    signal seriesPointHovered(int seriesIndex, int pointIndex)
    // Positive delta zooms in; negative delta zooms out 正增量放大，负增量缩小
    // anchorRatio is the pointer position used as the zoom anchor anchorRatio 是鼠标缩放锚点的相对位置
    signal wheelZoomed(int delta, real anchorRatio)

    // ==================== Internal Methods 内部方法 ====================
    function _calculateDirtyPixelQuantum(devicePixelRatio) {
        // Canvas rounds dirty regions to integer DIPs; find a whole-physical-pixel DIP grid
        // Canvas会把脏区取整到整数DIP；计算同时落在完整物理像素上的DIP网格
        var ratio = devicePixelRatio > 0 ? devicePixelRatio : 1
        for (var quantum = 1; quantum <= 16; quantum++) {
            var physicalPixels = ratio * quantum
            if (Math.abs(physicalPixels - Math.round(physicalPixels)) < 0.000001) {
                return quantum
            }
        }
        return 1
    }

    function _calculateValueRange() {
        var min = Infinity, max = -Infinity
        if (isMultiSeries) {
            if (stacked) {
                var maxLen = 0
                for (var s = 0; s < series.length; s++) {
                    var vals = series[s] && series[s].values && typeof series[s].values.length === "number"
                               ? series[s].values : []
                    if (vals.length > maxLen) maxLen = vals.length
                }
                for (var i = 0; i < maxLen; i++) {
                    var sum = 0
                    for (var ss = 0; ss < series.length; ss++) {
                        var stackedValues = series[ss] && series[ss].values && typeof series[ss].values.length === "number"
                                            ? series[ss].values : []
                        var v = stackedValues[i]
                        if (typeof v === "number" && isFinite(v)) sum += v
                    }
                    if (sum > max) max = sum
                }
                min = 0
            } else {
                for (var s2 = 0; s2 < series.length; s2++) {
                    var vals2 = series[s2] && series[s2].values && typeof series[s2].values.length === "number"
                                 ? series[s2].values : []
                    for (var j = 0; j < vals2.length; j++) {
                        if (typeof vals2[j] !== "number" || !isFinite(vals2[j])) continue
                        if (vals2[j] < min) min = vals2[j]
                        if (vals2[j] > max) max = vals2[j]
                    }
                }
            }
        } else {
            for (var k = 0; k < chartData.length; k++) {
                if (!chartData[k]) continue
                var v2 = chartData[k].value
                if (typeof v2 !== "number" || !isFinite(v2)) continue
                if (v2 < min) min = v2
                if (v2 > max) max = v2
            }
        }
        if (!isFinite(min) || !isFinite(max)) return { min: 0, max: 1 }
        var padding = (max - min) * 0.15 || 1
        return { min: stacked ? 0 : min - padding, max: max + padding }
    }

    function valueToY(value) {
        var range = valueRange.max - valueRange.min
        if (range === 0) return height / 2
        return height - ((value - valueRange.min) / range) * height
    }
    
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function getTooltipPosition(index) {
        if (index < 0 || index >= pointPositions.length) return { x: 0, y: 0 }
        return pointPositions[index]
    }

    function _lowerBoundPointX(value) {
        var low = 0
        var high = pointPositions.length
        while (low < high) {
            var middle = Math.floor((low + high) / 2)
            if (pointPositions[middle].x < value) low = middle + 1
            else high = middle
        }
        return low
    }

    function _nearestPointIndex(pointerX, pointerY, maxDistance) {
        var first = _lowerBoundPointX(pointerX - maxDistance)
        var last = _lowerBoundPointX(pointerX + maxDistance)
        var minimumSquared = maxDistance * maxDistance
        var foundIndex = -1
        _lastHoverCandidateCount = last - first
        for (var index = first; index < last; index++) {
            var point = pointPositions[index]
            var dx = pointerX - point.x
            var dy = pointerY - point.y
            var distanceSquared = dx * dx + dy * dy
            if (distanceSquared < minimumSquared) {
                minimumSquared = distanceSquared
                foundIndex = index
            }
        }
        return foundIndex
    }

    function _nearestSeriesPointIndexByX(pointerX) {
        var points = seriesPointPositions.length > 0 ? (seriesPointPositions[0] || []) : []
        if (points.length === 0) {
            _lastSeriesHoverCandidateCount = 0
            return -1
        }
        var low = 0
        var high = points.length
        while (low < high) {
            var middle = Math.floor((low + high) / 2)
            if (points[middle].x < pointerX) low = middle + 1
            else high = middle
        }
        var first = Math.max(0, low - 1)
        var last = Math.min(points.length - 1, low)
        var foundIndex = -1
        var closestX = Infinity
        _lastSeriesHoverCandidateCount = last - first + 1
        for (var index = first; index <= last; index++) {
            var distance = Math.abs(pointerX - points[index].x)
            if (distance < closestX) {
                closestX = distance
                foundIndex = index
            }
        }
        return foundIndex
    }

    function _rebuildLineGeometry(canvasWidth, canvasHeight) {
        var range = valueRange
        var geometry = isMultiSeries
            ? Geometry.buildSeries(series, canvasWidth, canvasHeight, boundaryGap,
                                   stacked, range.min, range.max,
                                   seriesValueSources,
                                   renderViewportStart, renderViewportEnd)
            : Geometry.buildSingle(chartData, canvasWidth, canvasHeight,
                                   boundaryGap, Enums.spacing.m,
                                   range.min, range.max,
                                   chartDataProjection,
                                   renderViewportStart, renderViewportEnd)
        _lineGeometry = geometry
        _lineGeometryBaseline = geometry.baseline
        if (isMultiSeries) {
            if (geometry.maxLength >= 2) seriesPointPositions = geometry.seriesPoints
        } else if (geometry.maxLength >= 2) {
            pointPositions = geometry.points
        }
        _lineGeometryDirty = false
        _lastGeometryProgress = -1
        _lineGeometryBuildCount++
    }

    function _updateAnimatedLineGeometry(progress) {
        if (_lineGeometryDirty) _rebuildLineGeometry(width, height)
        if (progress === _lastGeometryProgress) {
            _lastFramePointUpdateCount = 0
            return
        }
        _lastFramePointUpdateCount = isMultiSeries
            ? Geometry.updateSeries(_lineGeometry.seriesPoints, progress,
                                    _lineGeometryBaseline)
            : Geometry.updatePoints(_lineGeometry.points, progress,
                                    _lineGeometryBaseline)
        _lastGeometryProgress = progress
        if (_lastFramePointUpdateCount > 0) {
            if (isMultiSeries) seriesPointPositionsChanged()
            else pointPositionsChanged()
        }
    }

    function _invalidateLineGeometry() {
        _lineGeometryDirty = true
        canvas.requestPaint()
    }

    function _requestHoverPaint() {
        if (_lineGeometryDirty || (animated && canvas.animProgress < 1) ||
                (isMultiSeries && hoveredSeriesIndex !== _paintedHoverSeriesIndex)) {
            canvas.requestPaint()
            return
        }
        var points = isMultiSeries
            ? Geometry.firstNonEmpty(seriesPointPositions) : pointPositions
        var padding = Enums.spacing.m
        var previous = Geometry.dirtyBounds(
            points, _paintedHoverIndex, width, height, padding
        )
        var current = Geometry.dirtyBounds(
            points, hoveredIndex, width, height, padding
        )
        if (!previous && !current) return
        var dirty = Geometry.unitedBounds(previous, current)
        var quantum = _dirtyPixelQuantum
        var left = Math.max(0, Math.floor(dirty.x / quantum) * quantum)
        var right = Math.min(
            width,
            Math.ceil((dirty.x + dirty.width) / quantum) * quantum
        )
        canvas.markDirty(Qt.rect(left, dirty.y, right - left, dirty.height))
    }

    onHoveredIndexChanged: _requestHoverPaint()
    // hoveredSeriesIndex does not repaint because vertical movement between series is frequent
    // hoveredSeriesIndex 不触发重绘，因为在多个系列之间垂直移动时会频繁切换
    // It only anchors the tooltip and does not affect the painted line or points
    // 视觉上只用于 tooltip 锚定，不影响线条或折点绘制
    // onHoveredSeriesIndexChanged: canvas.requestPaint()
    onChartDataChanged: _invalidateLineGeometry()
    onSeriesChanged: _invalidateLineGeometry()
    onChartDataProjectionChanged: _invalidateLineGeometry()
    onSeriesValueSourcesChanged: _invalidateLineGeometry()
    onRenderViewportStartChanged: _invalidateLineGeometry()
    onRenderViewportEndChanged: _invalidateLineGeometry()
    on_DisplayRangeMinChanged: _invalidateLineGeometry()
    on_DisplayRangeMaxChanged: _invalidateLineGeometry()
    onShowAverageChanged: canvas.requestPaint()
    onShowMinMaxChanged: canvas.requestPaint()
    onBoundaryGapChanged: _invalidateLineGeometry()
    onShowAreaGradientChanged: canvas.requestPaint()
    onStackedChanged: _invalidateLineGeometry()

    // ==================== Content 内容 ====================
    // Canvas 画布
    LineChartCanvas {
        id: canvas

        lineControl: root
    }

    // Markers 标记组件
    LineChartMarkers {
        anchors.fill: parent
        series: root.series
        seriesPointPositions: root.seriesPointPositions
        showMinMax: root.showMinMax
        showAverage: root.showAverage
        chartWidth: root.width
        getSeriesColor: root.getSeriesColor
        valueToY: root.valueToY
        findMinMaxIndices: Painter.findMinMaxIndices
        calculateAverage: Painter.calculateAverage
    }

    // Mouse area 鼠标区域
    MouseArea {
        anchors.fill: parent
        hoverEnabled: root.hoverDetectEnabled
        cursorShape: Qt.ArrowCursor
        acceptedButtons: Qt.LeftButton
        propagateComposedEvents: true

        // Emit pointer-anchored wheel zoom to the parent 向父级发送鼠标锚定滚轮缩放
        onWheel: (wheel) => {
            var ratio = root.width > 0
                ? Math.max(0, Math.min(1, wheel.x / root.width))
                : Enums.chart.default_anchor_ratio
            // angleDelta.y is normally one wheel step angleDelta.y 通常表示一个滚轮刻度
            root.wheelZoomed(wheel.angleDelta.y, ratio)
            wheel.accepted = true
        }
        
        onPositionChanged: (mouse) => {
            root.mouseX = mouse.x
            root.mouseY = mouse.y

            var foundIndex = -1
            var foundSeriesIndex = -1

            if (root.isMultiSeries) {
                // 直接在 seriesPointPositions 缓存里找鼠标最近的 X — 不再用 stepX 公式
                // (公式跟 paint 函数计算细节走偏后会错位; 直接对画面位置最稳)
                if (root.seriesPointPositions.length > 0) {
                    foundIndex = root._nearestSeriesPointIndexByX(mouse.x)
                    // 在该 X 索引上找 Y 最近的 series
                    if (foundIndex >= 0) {
                        var closestDist = Infinity
                        for (var si = 0; si < root.seriesPointPositions.length; si++) {
                            var pts = root.seriesPointPositions[si]
                            if (pts && pts[foundIndex]) {
                                var dist = Math.abs(mouse.y - pts[foundIndex].y)
                                if (dist < closestDist) {
                                    closestDist = dist
                                    foundSeriesIndex = si
                                    root.tooltipX = pts[foundIndex].x
                                    root.tooltipY = pts[foundIndex].y
                                }
                            }
                        }
                    }
                }
                root.hoveredSeriesIndex = foundSeriesIndex
                root.seriesPointHovered(foundSeriesIndex, foundIndex)
            } else {
                foundIndex = root._nearestPointIndex(mouse.x, mouse.y, 30)
            }
            root.pointHovered(foundIndex)
        }
        
        onExited: {
            root.pointHovered(-1)
            root.hoveredSeriesIndex = -1
            root.seriesPointHovered(-1, -1)
        }
        
        onClicked: {
            if (root.hoveredIndex >= 0) {
                if (root.isMultiSeries && root.hoveredSeriesIndex >= 0) {
                    root.pointClicked(root.hoveredIndex, {
                        seriesIndex: root.hoveredSeriesIndex,
                        pointIndex: root.hoveredIndex,
                        value: root.series[root.hoveredSeriesIndex].values[root.hoveredIndex]
                    })
                } else {
                    root.pointClicked(root.hoveredIndex, root.chartData[root.hoveredIndex])
                }
            }
        }
    }

    Behavior on _displayRangeMin {
        enabled: root.animated

        NumberAnimation {
            duration: Enums.duration.normal
            easing.type: Easing.InOutCubic
        }
    }

    Behavior on _displayRangeMax {
        enabled: root.animated

        NumberAnimation {
            duration: Enums.duration.normal
            easing.type: Easing.InOutCubic
        }
    }
}
