// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."

// RadarChartContent - Radar chart rendering component 雷达图渲染组件
// Fluent Design style: clean polygon grid, subtle filled areas
// Fluent Design 风格：简洁多边形网格、柔和填充区域

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var indicators     // [{name: "", max: 100}, ...]
    required property var series         // [{name: "", values: [], color: ""}, ...]
    required property bool animated      // Enable animation 启用动画
    required property bool showLabels    // Show indicator labels 显示指标标签
    required property int rings          // Number of rings 环数
    
    // ==================== Public Props 公开属性 ====================
    property int hoveredSeriesIndex: -1
    property int hoveredPointIndex: -1

    // ==================== Internal Props 内部属性 ====================
    property var pointPositions: []
    property real tooltipX: 0
    property real tooltipY: 0
    property var _axisGeometry: []
    property var _seriesPointGeometry: []
    property bool _pointGeometryDirty: true
    property int _pointGeometryBuildCount: 0
    property int _lastFramePointUpdateCount: 0
    property real _geometryCenterX: 0
    property real _geometryCenterY: 0
    property real _geometryRadius: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property real _hitRadius: 20

    // ==================== Signals 信号 ====================
    signal pointClicked(int pointIndex, var data)
    signal pointHovered(int seriesIndex, int pointIndex)

    // ==================== Internal Methods 内部方法 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }

    function _buildAxisGeometry() {
        var axes = []
        var count = indicators.length
        var angleStep = count > 0 ? Math.PI * 2 / count : 0
        var startAngle = -Math.PI / 2
        for (var index = 0; index < count; index++) {
            var indicator = indicators[index] || {}
            var angle = startAngle + index * angleStep
            var maximum = typeof indicator.max === "number" && isFinite(indicator.max) && indicator.max > 0
                          ? indicator.max : 100
            axes.push({
                angle: angle,
                unitX: Math.cos(angle), unitY: Math.sin(angle),
                maximum: maximum, label: indicator.name || ""
            })
        }
        return axes
    }

    function _buildSeriesPoints(seriesIndex, axes, radius) {
        var seriesData = series[seriesIndex] || {}
        var values = seriesData.values && typeof seriesData.values.length === "number"
                     ? seriesData.values : []
        var points = []
        for (var pointIndex = 0; pointIndex < axes.length; pointIndex++) {
            var value = typeof values[pointIndex] === "number" && isFinite(values[pointIndex])
                        ? values[pointIndex] : 0
            var pointRadius = radius * value / axes[pointIndex].maximum
            var offsetX = axes[pointIndex].unitX * pointRadius
            var offsetY = axes[pointIndex].unitY * pointRadius
            points.push({
                x: _geometryCenterX + offsetX, y: _geometryCenterY + offsetY,
                offsetX: offsetX, offsetY: offsetY,
                seriesIndex: seriesIndex, pointIndex: pointIndex, value: value
            })
        }
        return points
    }

    function _rebuildPointGeometry(canvasWidth, canvasHeight) {
        _geometryCenterX = canvasWidth / 2
        _geometryCenterY = canvasHeight / 2
        _geometryRadius = Math.min(canvasWidth, canvasHeight) / 2 - 40
        var axes = _buildAxisGeometry()
        var groupedPoints = []
        var flatPoints = []
        for (var seriesIndex = 0; seriesIndex < series.length; seriesIndex++) {
            var points = _buildSeriesPoints(seriesIndex, axes, _geometryRadius)
            groupedPoints.push(points)
            for (var pointIndex = 0; pointIndex < points.length; pointIndex++) {
                flatPoints.push(points[pointIndex])
            }
        }
        _axisGeometry = axes
        _seriesPointGeometry = groupedPoints
        pointPositions = flatPoints
        _pointGeometryDirty = false
        _pointGeometryBuildCount++
    }

    function _updateAnimatedPoints(progress) {
        if (_pointGeometryDirty) _rebuildPointGeometry(width, height)
        for (var index = 0; index < pointPositions.length; index++) {
            var point = pointPositions[index]
            point.x = _geometryCenterX + point.offsetX * progress
            point.y = _geometryCenterY + point.offsetY * progress
        }
        _lastFramePointUpdateCount = pointPositions.length
        if (_lastFramePointUpdateCount > 0) pointPositionsChanged()
    }

    function _invalidatePointGeometry() {
        _pointGeometryDirty = true
        canvas.requestPaint()
    }

    function _nearestPointIndex(x, y) {
        if (_pointGeometryDirty) {
            _rebuildPointGeometry(width, height)
            _updateAnimatedPoints(animated ? canvas.animProgress : 1)
        }
        var nearestIndex = -1
        var nearestDistanceSquared = _hitRadius * _hitRadius
        for (var index = 0; index < pointPositions.length; index++) {
            var point = pointPositions[index]
            var deltaX = x - point.x
            var deltaY = y - point.y
            var distanceSquared = deltaX * deltaX + deltaY * deltaY
            if (distanceSquared < nearestDistanceSquared) {
                nearestDistanceSquared = distanceSquared
                nearestIndex = index
            }
        }
        return nearestIndex
    }

    // Repaint on hover change 悬浮变化时重绘
    onHoveredSeriesIndexChanged: canvas.requestPaint()
    onHoveredPointIndexChanged: canvas.requestPaint()
    onSeriesChanged: _invalidatePointGeometry()
    onIndicatorsChanged: _invalidatePointGeometry()
    onShowLabelsChanged: canvas.requestPaint()
    onRingsChanged: canvas.requestPaint()

    // ==================== Content 内容 ====================
    // Canvas 画布
    Canvas {
        id: canvas

        property real animProgress: 0

        function drawGrid(ctx) {
            var axes = root._axisGeometry
            if (axes.length === 0) return
            ctx.strokeStyle = Enums.chartColors.gridLine
            ctx.lineWidth = 1
            for (var ring = 1; ring <= root.rings; ring++) {
                var ringRadius = root._geometryRadius * ring / root.rings
                ctx.beginPath()
                for (var index = 0; index < axes.length; index++) {
                    var x = root._geometryCenterX + axes[index].unitX * ringRadius
                    var y = root._geometryCenterY + axes[index].unitY * ringRadius
                    if (index === 0) ctx.moveTo(x, y)
                    else ctx.lineTo(x, y)
                }
                ctx.closePath()
                ctx.stroke()
            }
            for (var axisIndex = 0; axisIndex < axes.length; axisIndex++) {
                ctx.beginPath()
                ctx.moveTo(root._geometryCenterX, root._geometryCenterY)
                ctx.lineTo(root._geometryCenterX + axes[axisIndex].unitX * root._geometryRadius,
                           root._geometryCenterY + axes[axisIndex].unitY * root._geometryRadius)
                ctx.stroke()
            }
        }

        function drawLabels(ctx) {
            ctx.fillStyle = Enums.textColor.secondary
            ctx.font = "11px " + Enums.canvasFontFamily
            ctx.textBaseline = "middle"
            var labelRadius = root._geometryRadius + 20
            for (var index = 0; index < root._axisGeometry.length; index++) {
                var axis = root._axisGeometry[index]
                var x = root._geometryCenterX + axis.unitX * labelRadius
                var y = root._geometryCenterY + axis.unitY * labelRadius
                if (Math.abs(axis.angle + Math.PI / 2) < 0.1) {
                    ctx.textAlign = "center"
                    y -= 5
                } else if (Math.abs(axis.angle - Math.PI / 2) < 0.1) {
                    ctx.textAlign = "center"
                    y += 5
                } else if (axis.angle > -Math.PI / 2 && axis.angle < Math.PI / 2) {
                    ctx.textAlign = "left"
                    x += 5
                } else {
                    ctx.textAlign = "right"
                    x -= 5
                }
                ctx.fillText(axis.label, x, y)
            }
        }

        function drawSeriesArea(ctx, points, color, hovered) {
            if (points.length === 0) return
            ctx.beginPath()
            for (var index = 0; index < points.length; index++) {
                if (index === 0) ctx.moveTo(points[index].x, points[index].y)
                else ctx.lineTo(points[index].x, points[index].y)
            }
            ctx.closePath()
            var qColor = Qt.color(color)
            var fillAlpha = hovered ? Enums.stateColor.chartFillMedium + 0.05 : Enums.opacityLevel.medium
            ctx.fillStyle = Qt.rgba(qColor.r, qColor.g, qColor.b, fillAlpha)
            ctx.fill()
            ctx.strokeStyle = color
            ctx.lineWidth = hovered ? 2.5 : 2
            ctx.stroke()
        }

        function drawSeriesPoints(ctx, points, color, seriesIndex) {
            for (var index = 0; index < points.length; index++) {
                var point = points[index]
                var hovered = seriesIndex === root.hoveredSeriesIndex &&
                              point.pointIndex === root.hoveredPointIndex
                var dotSize = hovered ? 5 : 3
                ctx.beginPath()
                ctx.fillStyle = Enums.cardColor
                ctx.arc(point.x, point.y, dotSize, 0, Math.PI * 2)
                ctx.fill()
                ctx.beginPath()
                ctx.strokeStyle = color
                ctx.lineWidth = hovered ? 2 : 1.5
                ctx.arc(point.x, point.y, dotSize, 0, Math.PI * 2)
                ctx.stroke()
            }
        }

        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            if (root._pointGeometryDirty) root._rebuildPointGeometry(width, height)
            var progress = root.animated ? animProgress : 1
            root._updateAnimatedPoints(progress)
            drawGrid(ctx)
            if (root.showLabels) drawLabels(ctx)
            for (var seriesIndex = 0; seriesIndex < root._seriesPointGeometry.length; seriesIndex++) {
                var points = root._seriesPointGeometry[seriesIndex]
                var color = root.getSeriesColor(seriesIndex)
                var hovered = seriesIndex === root.hoveredSeriesIndex
                drawSeriesArea(ctx, points, color, hovered)
                drawSeriesPoints(ctx, points, color, seriesIndex)
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
            }
        }
        
        onExited: root.pointHovered(-1, -1)
        
        onClicked: {
            if (root.hoveredSeriesIndex >= 0 && root.hoveredPointIndex >= 0) {
                var clickedSeries = root.series[root.hoveredSeriesIndex] || {}
                var clickedIndicator = root.indicators[root.hoveredPointIndex] || {}
                var clickedValues = clickedSeries.values && typeof clickedSeries.values.length === "number"
                                    ? clickedSeries.values : []
                root.pointClicked(root.hoveredPointIndex, {
                    seriesIndex: root.hoveredSeriesIndex,
                    seriesName: clickedSeries.name || "",
                    indicatorName: clickedIndicator.name || "",
                    value: clickedValues[root.hoveredPointIndex] || 0
                })
            }
        }
    }
}
