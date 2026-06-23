// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../data"
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
    
    // ==================== Props 属性 ====================
    property var series: []              // [{name: "", values: [], color: "", stack: ""}, ...] - multi series 多系列
    property bool showAverage: false     // Show average line (markLine) 显示平均线
    property bool showMinMax: false      // Show min/max markers (markPoint) 显示最大最小值标记
    property int hoveredIndex: -1
    property int hoveredSeriesIndex: -1
    property bool boundaryGap: true      // Gap at edges 边缘间距
    property bool showAreaGradient: false // Show gradient fill under line 渐变填充
    property bool stacked: false         // Stacked area chart 堆叠面积图
    property bool animated: false        // Line drawing animation 折线绘制动画
    // 是否启用鼠标悬停检测; 数据点过密时关闭可消掉 onPositionChanged 重型计算导致的掉帧
    property bool hoverDetectEnabled: true
    
    // ==================== Signals 信号 ====================
    signal pointClicked(int index, var data)
    signal pointHovered(int index)
    signal seriesPointHovered(int seriesIndex, int pointIndex)
    // delta > 0 = 放大 (缩小范围); delta < 0 = 缩小 (扩大范围)
    // anchorRatio: 鼠标位于 chart 内 0..1 (用于以鼠标位置为锚缩放)
    signal wheelZoomed(int delta, real anchorRatio)
    
    // ==================== Internal 内部属性 ====================
    property var pointPositions: []       // For single series 单系列点位置
    property var seriesPointPositions: [] // For multi series 多系列点位置
    property real tooltipX: 0
    property real tooltipY: 0
    property real mouseX: 0
    property real mouseY: 0
    
    // ==================== Computed Props 计算属性 ====================
    readonly property bool isMultiSeries: series.length > 0
    readonly property var valueRange: _calculateValueRange()
    
    function _calculateValueRange() {
        var min = Infinity, max = -Infinity
        if (isMultiSeries) {
            if (stacked) {
                var maxLen = 0
                for (var s = 0; s < series.length; s++) {
                    var vals = series[s].values || []
                    if (vals.length > maxLen) maxLen = vals.length
                }
                for (var i = 0; i < maxLen; i++) {
                    var sum = 0
                    for (var ss = 0; ss < series.length; ss++) {
                        var v = (series[ss].values || [])[i] || 0
                        sum += v
                    }
                    if (sum > max) max = sum
                }
                min = 0
            } else {
                for (var s2 = 0; s2 < series.length; s2++) {
                    var vals2 = series[s2].values || []
                    for (var j = 0; j < vals2.length; j++) {
                        if (vals2[j] < min) min = vals2[j]
                        if (vals2[j] > max) max = vals2[j]
                    }
                }
            }
        } else {
            for (var k = 0; k < chartData.length; k++) {
                var v2 = chartData[k].value
                if (v2 < min) min = v2
                if (v2 > max) max = v2
            }
        }
        var padding = (max - min) * 0.15 || 1
        return { min: stacked ? 0 : min - padding, max: max + padding }
    }

    // ==================== Helper Functions 辅助函数 ====================
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

    // ==================== Canvas 画布 ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        property real animProgress: 1.0
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            if (root.isMultiSeries) {
                paintMultiSeries(ctx)
            } else {
                paintSingleSeries(ctx)
            }
        }
        
        function paintSingleSeries(ctx) {
            if (root.chartData.length < 2) return
            
            var padding = Enums.spacing.m
            var chartHeight = height - padding * 2
            var chartWidth = width - padding * 2
            var dataCount = root.chartData.length
            var stepX = root.boundaryGap ? chartWidth / dataCount : chartWidth / (dataCount - 1)
            var startX = root.boundaryGap ? padding + stepX / 2 : padding
            var points = []
            
            for (var i = 0; i < root.chartData.length; i++) {
                var x = startX + i * stepX
                var y = padding + root.valueToY(root.chartData[i].value) * (chartHeight / height)
                points.push({x: x, y: y})
            }
            root.pointPositions = points
            
            if (root.isArea || root.showAreaGradient) {
                Painter.drawAreaFill(ctx, points, root.primaryColor, padding + chartHeight, 
                    root.smoothLine, Enums.stateColor.chartFillMedium, Enums.stateColor.chartFillSubtle)
            }
            Painter.drawLine(ctx, points, root.primaryColor, 2, root.smoothLine)
            
            for (var p = 0; p < points.length; p++) {
                var hovered = (p === root.hoveredIndex)
                Painter.drawSolidPoint(ctx, points[p].x, points[p].y, root.primaryColor, hovered, Enums.cardColor)
            }
        }
        
        function paintMultiSeries(ctx) {
            var seriesData = root.series
            if (seriesData.length === 0) return
            
            var maxLen = 0
            for (var s = 0; s < seriesData.length; s++) {
                var vals = seriesData[s].values || []
                if (vals.length > maxLen) maxLen = vals.length
            }
            if (maxLen < 2) return
            
            var stepX = root.boundaryGap ? width / maxLen : width / (maxLen - 1)
            var startX = root.boundaryGap ? stepX / 2 : 0
            
            // Draw vertical indicator 绘制垂直指示线
            if (root.hoveredIndex >= 0 && root.hoveredIndex < maxLen) {
                var indicatorX = startX + root.hoveredIndex * stepX
                Painter.drawVerticalIndicator(ctx, indicatorX, height, Enums.chartColors.gridLine)
            }
            
            // Calculate all points 计算所有点
            var allPoints = []
            var stackedCumulative = []
            for (var sci = 0; sci < maxLen; sci++) stackedCumulative.push(0)
            
            for (var si = 0; si < seriesData.length; si++) {
                var seriesItem = seriesData[si]
                var values = seriesItem.values || []
                var points = []
                
                for (var i = 0; i < values.length; i++) {
                    var x = startX + i * stepX
                    var val = values[i] || 0
                    var y
                    if (root.stacked) {
                        stackedCumulative[i] += val
                        y = root.valueToY(stackedCumulative[i])
                    } else {
                        y = root.valueToY(val)
                    }
                    points.push({x: x, y: y, value: val, stackedValue: stackedCumulative[i]})
                }
                allPoints.push(points)
            }
            
            // Draw areas 绘制面积
            if (root.stacked || root.showAreaGradient) {
                for (var ai = seriesData.length - 1; ai >= 0; ai--) {
                    var areaPoints = allPoints[ai]
                    var areaColor = root.getSeriesColor(ai)
                    
                    if (root.stacked) {
                        var prevPoints = ai < seriesData.length - 1 ? allPoints[ai + 1] : null
                        Painter.drawStackedArea(ctx, areaPoints, prevPoints, areaColor, height, 
                            root.smoothLine, Enums.stateColor.chartFillStrong)
                    } else if (root.showAreaGradient) {
                        Painter.drawAreaGradient(ctx, areaPoints, areaColor, height, root.smoothLine,
                            Enums.stateColor.chartFillMedium, Enums.stateColor.chartFillLight, 
                            Enums.stateColor.chartFillFaint)
                    }
                }
            }
            
            // Draw lines and points 绘制线条和点
            var allSeriesPoints = []
            for (var li = 0; li < seriesData.length; li++) {
                var lineSeriesItem = seriesData[li]
                var lineValues = lineSeriesItem.values || []
                var lineColor = root.getSeriesColor(li)
                var linePoints = allPoints[li]
                var isLineSeriesHovered = (li === root.hoveredSeriesIndex)
                
                allSeriesPoints.push(linePoints)
                
                // Draw average line 绘制平均线
                if (root.showAverage && lineValues.length > 0) {
                    var avg = Painter.calculateAverage(lineValues)
                    var avgY = root.valueToY(avg)
                    Painter.drawAverageLine(ctx, avgY, width, lineColor, Enums.stateColor.chartLineAlpha)
                }
                
                Painter.drawLine(ctx, linePoints, lineColor, isLineSeriesHovered ? 2.5 : 2, root.smoothLine)
                
                for (var p = 0; p < linePoints.length; p++) {
                    var hovered = (p === root.hoveredIndex)
                    Painter.drawHollowPoint(ctx, linePoints[p].x, linePoints[p].y, lineColor, hovered, Enums.cardColor)
                }
            }
            root.seriesPointPositions = allSeriesPoints
        }
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                lineAnimTimer.start()
            } else {
                requestPaint()
            }
        }
        onVisibleChanged: if (visible) requestPaint()
        
        Timer {
            id: lineAnimTimer
            interval: Enums.duration.tick
            repeat: true
            property real t: 0
            onTriggered: {
                t += 0.04
                if (t >= 1) {
                    t = 1
                    canvas.animProgress = 1
                    stop()
                } else {
                    canvas.animProgress = 1 - Math.pow(1 - t, 5)
                }
                canvas.requestPaint()
            }
        }
    }
    
    // Repaint triggers 重绘触发
    onHoveredIndexChanged: canvas.requestPaint()
    // hoveredSeriesIndex 不触发重绘 — 鼠标在多 series 间垂直移动时频繁切换会卡帧
    // 视觉上只用于 tooltip 锚定, 不影响线条/折点 paint
    // onHoveredSeriesIndexChanged: canvas.requestPaint()
    onChartDataChanged: canvas.requestPaint()
    onSeriesChanged: canvas.requestPaint()
    onShowAverageChanged: canvas.requestPaint()
    onShowMinMaxChanged: canvas.requestPaint()
    onBoundaryGapChanged: canvas.requestPaint()
    onShowAreaGradientChanged: canvas.requestPaint()
    onStackedChanged: canvas.requestPaint()

    // ==================== Markers 标记组件 ====================
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

    // ==================== Mouse Area 鼠标区域 ====================
    MouseArea {
        anchors.fill: parent
        hoverEnabled: root.hoverDetectEnabled
        cursorShape: Qt.ArrowCursor
        acceptedButtons: Qt.LeftButton
        propagateComposedEvents: true

        // 滚轮缩放: emit wheelZoomed 信号给应用层处理 (改 startDate/endDate)
        onWheel: (wheel) => {
            var ratio = root.width > 0 ? Math.max(0, Math.min(1, wheel.x / root.width)) : 0.5
            // wheel.angleDelta.y 通常 +120 / -120 (一格)
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
                    var firstSeriesPts = root.seriesPointPositions[0] || []
                    var closestX = Infinity
                    for (var i = 0; i < firstSeriesPts.length; i++) {
                        var pt = firstSeriesPts[i]
                        if (!pt) continue
                        var dx = Math.abs(mouse.x - pt.x)
                        if (dx < closestX) {
                            closestX = dx
                            foundIndex = i
                        }
                    }
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
                var minDist = 30
                for (var j = 0; j < root.pointPositions.length; j++) {
                    var p = root.pointPositions[j]
                    var d = Math.sqrt(Math.pow(mouse.x - p.x, 2) + Math.pow(mouse.y - p.y, 2))
                    if (d < minDist) {
                        minDist = d
                        foundIndex = j
                    }
                }
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
