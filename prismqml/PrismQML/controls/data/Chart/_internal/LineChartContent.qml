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
    readonly property var valueRange: _calculateValueRange()

    // ==================== Signals 信号 ====================
    signal pointClicked(int index, var data)
    signal pointHovered(int index)
    signal seriesPointHovered(int seriesIndex, int pointIndex)
    // Positive delta zooms in; negative delta zooms out 正增量放大，负增量缩小
    // anchorRatio is the pointer position used as the zoom anchor anchorRatio 是鼠标缩放锚点的相对位置
    signal wheelZoomed(int delta, real anchorRatio)

    // ==================== Internal Methods 内部方法 ====================
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
                                   stacked, range.min, range.max)
            : Geometry.buildSingle(chartData, canvasWidth, canvasHeight,
                                   boundaryGap, Enums.spacing.m,
                                   range.min, range.max)
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
        canvas.markDirty(Qt.rect(dirty.x, dirty.y, dirty.width, dirty.height))
    }

    onHoveredIndexChanged: _requestHoverPaint()
    // hoveredSeriesIndex does not repaint because vertical movement between series is frequent
    // hoveredSeriesIndex 不触发重绘，因为在多个系列之间垂直移动时会频繁切换
    // It only anchors the tooltip and does not affect the painted line or points
    // 视觉上只用于 tooltip 锚定，不影响线条或折点绘制
    // onHoveredSeriesIndexChanged: canvas.requestPaint()
    onChartDataChanged: _invalidateLineGeometry()
    onSeriesChanged: _invalidateLineGeometry()
    onShowAverageChanged: canvas.requestPaint()
    onShowMinMaxChanged: canvas.requestPaint()
    onBoundaryGapChanged: _invalidateLineGeometry()
    onShowAreaGradientChanged: canvas.requestPaint()
    onStackedChanged: _invalidateLineGeometry()

    // ==================== Content 内容 ====================
    // Canvas 画布
    Canvas {
        id: canvas

        property real animProgress: 1.0

        function animatedY(targetY, baselineY) {
            return baselineY + (targetY - baselineY) * animProgress
        }

        function paintSingleSeries(ctx, region, fullPaint) {
            if (root.chartData.length < 2) return 0
            
            var padding = Enums.spacing.m
            var chartHeight = height - padding * 2
            var points = root.pointPositions
            var range = Geometry.paintRange(points, region, fullPaint, padding)
            var pathPoints = fullPaint ? points : points.slice(range.start, range.end)
            
            if (root.isArea || root.showAreaGradient) {
                Painter.drawAreaFill(ctx, pathPoints, root.primaryColor, padding + chartHeight,
                    root.smoothLine, Enums.stateColor.chartFillMedium, Enums.stateColor.chartFillSubtle)
            }
            Painter.drawLine(ctx, pathPoints, root.primaryColor, 2, root.smoothLine)
            
            for (var p = range.start; p < range.end; p++) {
                var hovered = (p === root.hoveredIndex)
                Painter.drawSolidPoint(ctx, points[p].x, points[p].y, root.primaryColor, hovered, Enums.cardColor)
            }
            return range.end - range.start
        }
        
        function paintMultiSeries(ctx, region, fullPaint) {
            var seriesData = root.series
            if (seriesData.length === 0) return 0
            
            var maxLen = root._lineGeometry.maxLength
            if (maxLen < 2) return 0
            var drawCount = 0
            
            var stepX = root.boundaryGap ? width / maxLen : width / (maxLen - 1)
            var startX = root.boundaryGap ? stepX / 2 : 0
            
            // Draw vertical indicator 绘制垂直指示线
            if (root.hoveredIndex >= 0 && root.hoveredIndex < maxLen) {
                var indicatorX = startX + root.hoveredIndex * stepX
                Painter.drawVerticalIndicator(ctx, indicatorX, height, Enums.chartColors.gridLine)
            }
            
            // Reuse cached points 复用缓存点位
            var allPoints = root.seriesPointPositions
            
            // Draw areas 绘制面积
            if (root.stacked || root.showAreaGradient) {
                for (var ai = seriesData.length - 1; ai >= 0; ai--) {
                    var areaPoints = allPoints[ai]
                    var areaColor = root.getSeriesColor(ai)
                    var areaRange = Geometry.paintRange(
                        areaPoints, region, fullPaint, Enums.spacing.m
                    )
                    var visibleArea = fullPaint ? areaPoints
                        : areaPoints.slice(areaRange.start, areaRange.end)
                    
                    if (root.stacked) {
                        var prevPoints = ai < seriesData.length - 1 ? allPoints[ai + 1] : null
                        var prevRange = Geometry.paintRange(
                            prevPoints, region, fullPaint, Enums.spacing.m
                        )
                        var visiblePrev = !prevPoints || fullPaint ? prevPoints
                            : prevPoints.slice(prevRange.start, prevRange.end)
                        Painter.drawStackedArea(ctx, visibleArea, visiblePrev, areaColor, height,
                            root.smoothLine, Enums.stateColor.chartFillStrong)
                    } else if (root.showAreaGradient) {
                        Painter.drawAreaGradient(ctx, visibleArea, areaColor, height, root.smoothLine,
                            Enums.stateColor.chartFillMedium, Enums.stateColor.chartFillLight, 
                            Enums.stateColor.chartFillFaint)
                    }
                }
            }
            
            // Draw lines and points 绘制线条和点
            for (var li = 0; li < seriesData.length; li++) {
                var lineSeriesItem = seriesData[li]
                var lineValues = lineSeriesItem && lineSeriesItem.values && typeof lineSeriesItem.values.length === "number"
                                 ? lineSeriesItem.values : []
                var lineColor = root.getSeriesColor(li)
                var linePoints = allPoints[li]
                var isLineSeriesHovered = (li === root.hoveredSeriesIndex)
                var lineRange = Geometry.paintRange(
                    linePoints, region, fullPaint, Enums.spacing.m
                )
                var visibleLine = fullPaint ? linePoints
                    : linePoints.slice(lineRange.start, lineRange.end)
                
                // Draw average line 绘制平均线
                if (root.showAverage && lineValues.length > 0) {
                    var avg = Painter.calculateAverage(lineValues)
                    var avgY = root.valueToY(avg)
                    Painter.drawAverageLine(ctx, avgY, width, lineColor, Enums.stateColor.chartLineAlpha)
                }
                
                Painter.drawLine(ctx, visibleLine, lineColor,
                                 isLineSeriesHovered ? 2.5 : 2, root.smoothLine)
                
                for (var p = lineRange.start; p < lineRange.end; p++) {
                    var hovered = (p === root.hoveredIndex)
                    Painter.drawHollowPoint(ctx, linePoints[p].x, linePoints[p].y, lineColor, hovered, Enums.cardColor)
                }
                drawCount += lineRange.end - lineRange.start
            }
            return drawCount
        }

        anchors.fill: parent

        onPaint: (region) => {
            var ctx = getContext("2d")
            var fullPaint = root._lineGeometryDirty || !region ||
                    (region.x <= 0 && region.y <= 0 &&
                     region.width >= width && region.height >= height)
            if (fullPaint) ctx.clearRect(0, 0, width, height)
            else ctx.clearRect(region.x, region.y, region.width, region.height)
            root._updateAnimatedLineGeometry(root.animated ? animProgress : 1)
            if (!fullPaint) {
                ctx.save()
                ctx.beginPath()
                ctx.rect(region.x, region.y, region.width, region.height)
                ctx.clip()
            }

            if (root.isMultiSeries) {
                root._lastFramePointDrawCount = paintMultiSeries(
                    ctx, region, fullPaint
                )
            } else {
                root._lastFramePointDrawCount = paintSingleSeries(
                    ctx, region, fullPaint
                )
            }
            if (!fullPaint) ctx.restore()
            root._paintedHoverIndex = root.hoveredIndex
            root._paintedHoverSeriesIndex = root.hoveredSeriesIndex
        }

        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                lineAnimation.restart()
            } else {
                requestPaint()
            }
        }
        onVisibleChanged: if (visible) requestPaint()
        onAnimProgressChanged: requestPaint()
        onWidthChanged: root._invalidateLineGeometry()
        onHeightChanged: root._invalidateLineGeometry()
        
        NumberAnimation {
            id: lineAnimation
            target: canvas
            property: "animProgress"
            from: 0
            to: 1
            duration: Enums.duration.chart
            easing.type: Easing.OutQuint
        }
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
}
