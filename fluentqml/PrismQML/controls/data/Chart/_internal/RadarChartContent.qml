// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    // ==================== Props 属性 ====================
    property int hoveredSeriesIndex: -1
    property int hoveredPointIndex: -1
    
    // ==================== Signals 信号 ====================
    signal pointClicked(int pointIndex, var data)
    signal pointHovered(int seriesIndex, int pointIndex)
    
    // ==================== Internal 内部属性 ====================
    property var pointPositions: []
    property real tooltipX: 0
    property real tooltipY: 0
    
    // ==================== Helper Functions 辅助函数 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    // ==================== Canvas 画布 ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        
        property real animProgress: 0
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            var centerX = width / 2
            var centerY = height / 2
            var radius = Math.min(width, height) / 2 - 40  // More padding for labels 更多标签空间
            var angleStep = Math.PI * 2 / root.indicators.length
            var startAngle = -Math.PI / 2  // Start from top 从顶部开始
            
            // Draw grid rings (polygon style) 绘制网格环（多边形样式）
            ctx.strokeStyle = Enums.chartColors.gridLine
            ctx.lineWidth = 1
            
            for (var r = 1; r <= root.rings; r++) {
                var ringRadius = radius * r / root.rings
                ctx.beginPath()
                for (var i = 0; i <= root.indicators.length; i++) {
                    var angle = startAngle + i * angleStep
                    var x = centerX + Math.cos(angle) * ringRadius
                    var y = centerY + Math.sin(angle) * ringRadius
                    if (i === 0) ctx.moveTo(x, y)
                    else ctx.lineTo(x, y)
                }
                ctx.closePath()
                ctx.stroke()
            }
            
            // Draw axis lines 绘制轴线
            for (var j = 0; j < root.indicators.length; j++) {
                var axisAngle = startAngle + j * angleStep
                ctx.beginPath()
                ctx.strokeStyle = Enums.chartColors.gridLine
                ctx.lineWidth = 1
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX + Math.cos(axisAngle) * radius,
                          centerY + Math.sin(axisAngle) * radius)
                ctx.stroke()
            }
            
            // Draw indicator labels 绘制指标标签
            if (root.showLabels) {
                ctx.fillStyle = Enums.textColor.secondary
                ctx.font = "11px " + Enums.canvasFontFamily
                ctx.textBaseline = "middle"
                
                for (var k = 0; k < root.indicators.length; k++) {
                    var labelAngle = startAngle + k * angleStep
                    var labelRadius = radius + 20
                    var lx = centerX + Math.cos(labelAngle) * labelRadius
                    var ly = centerY + Math.sin(labelAngle) * labelRadius
                    
                    // Adjust text alignment based on position 根据位置调整文本对齐
                    var labelText = root.indicators[k].name || ""
                    if (Math.abs(labelAngle + Math.PI / 2) < 0.1) {
                        // Top 顶部
                        ctx.textAlign = "center"
                        ly -= 5
                    } else if (Math.abs(labelAngle - Math.PI / 2) < 0.1) {
                        // Bottom 底部
                        ctx.textAlign = "center"
                        ly += 5
                    } else if (labelAngle > -Math.PI / 2 && labelAngle < Math.PI / 2) {
                        // Right side 右侧
                        ctx.textAlign = "left"
                        lx += 5
                    } else {
                        // Left side 左侧
                        ctx.textAlign = "right"
                        lx -= 5
                    }
                    ctx.fillText(labelText, lx, ly)
                }
            }
            
            // Draw data series 绘制数据系列
            var progress = root.animated ? animProgress : 1
            var allPoints = []
            
            for (var s = 0; s < root.series.length; s++) {
                var seriesData = root.series[s]
                var seriesColor = root.getSeriesColor(s)
                var isSeriesHovered = (s === root.hoveredSeriesIndex)
                
                // Draw filled area 绘制填充区域
                ctx.beginPath()
                var seriesPoints = []
                for (var p = 0; p < root.indicators.length; p++) {
                    var indicator = root.indicators[p]
                    var value = seriesData.values[p] || 0
                    var normalizedValue = (value / (indicator.max || 100)) * progress
                    var pointRadius = radius * normalizedValue
                    var pointAngle = startAngle + p * angleStep
                    var px = centerX + Math.cos(pointAngle) * pointRadius
                    var py = centerY + Math.sin(pointAngle) * pointRadius
                    
                    seriesPoints.push({x: px, y: py, seriesIndex: s, pointIndex: p, value: value})
                    
                    if (p === 0) ctx.moveTo(px, py)
                    else ctx.lineTo(px, py)
                }
                allPoints = allPoints.concat(seriesPoints)
                ctx.closePath()
                
                // Fluent Design: subtle fill 柔和填充
                var fillAlpha = isSeriesHovered ? Enums.stateColor.chartFillMedium + 0.05 : Enums.opacityLevel.medium
                ctx.fillStyle = Qt.rgba(Qt.color(seriesColor).r, Qt.color(seriesColor).g, 
                                       Qt.color(seriesColor).b, fillAlpha)
                ctx.fill()
                
                // Fluent Design: clean border line 简洁边框线
                ctx.strokeStyle = seriesColor
                ctx.lineWidth = isSeriesHovered ? 2.5 : 2
                ctx.stroke()
                
                // Fluent Design: simple data points 简洁数据点
                for (var q = 0; q < root.indicators.length; q++) {
                    var ind = root.indicators[q]
                    var val = seriesData.values[q] || 0
                    var normVal = (val / (ind.max || 100)) * progress
                    var dotRadius = radius * normVal
                    var dotAngle = startAngle + q * angleStep
                    var dx = centerX + Math.cos(dotAngle) * dotRadius
                    var dy = centerY + Math.sin(dotAngle) * dotRadius
                    
                    var isPointHovered = (s === root.hoveredSeriesIndex && q === root.hoveredPointIndex)
                    var dotSize = isPointHovered ? 5 : 3
                    
                    // White fill 白色填充
                    ctx.beginPath()
                    ctx.fillStyle = Enums.cardColor
                    ctx.arc(dx, dy, dotSize, 0, Math.PI * 2)
                    ctx.fill()
                    
                    // Color border 彩色边框
                    ctx.beginPath()
                    ctx.strokeStyle = seriesColor
                    ctx.lineWidth = isPointHovered ? 2 : 1.5
                    ctx.arc(dx, dy, dotSize, 0, Math.PI * 2)
                    ctx.stroke()
                }
            }
            
            root.pointPositions = allPoints
        }
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                animTimer.start()
            } else {
                animProgress = 1
                requestPaint()
            }
        }
        
        Timer {
            id: animTimer
            interval: Enums.duration.tick  // High-refresh tick 高刷定时器
            repeat: true
            property real t: 0  // Normalized time 归一化时间
            onTriggered: {
                t += 0.04  // ~400ms total duration 总时长约400ms
                if (t >= 1) {
                    t = 1
                    canvas.animProgress = 1
                    stop()
                } else {
                    // Fluent Design: OutQuint easing for smooth deceleration 平滑减速
                    canvas.animProgress = 1 - Math.pow(1 - t, 5)
                }
                canvas.requestPaint()
            }
        }
    }
    
    // Repaint on hover change 悬浮变化时重绘
    onHoveredSeriesIndexChanged: canvas.requestPaint()
    onHoveredPointIndexChanged: canvas.requestPaint()
    onSeriesChanged: canvas.requestPaint()
    
    // ==================== Mouse Area 鼠标区域 ====================
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredSeriesIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onPositionChanged: (mouse) => {
            var minDist = 20
            var foundSeriesIndex = -1
            var foundPointIndex = -1
            
            for (var i = 0; i < root.pointPositions.length; i++) {
                var pt = root.pointPositions[i]
                var dist = Math.sqrt(Math.pow(mouse.x - pt.x, 2) + Math.pow(mouse.y - pt.y, 2))
                if (dist < minDist) {
                    minDist = dist
                    foundSeriesIndex = pt.seriesIndex
                    foundPointIndex = pt.pointIndex
                }
            }
            
            root.pointHovered(foundSeriesIndex, foundPointIndex)
            
            if (foundSeriesIndex >= 0 && foundPointIndex >= 0) {
                for (var j = 0; j < root.pointPositions.length; j++) {
                    var p = root.pointPositions[j]
                    if (p.seriesIndex === foundSeriesIndex && p.pointIndex === foundPointIndex) {
                        root.tooltipX = p.x
                        root.tooltipY = p.y
                        break
                    }
                }
            }
        }
        
        onExited: root.pointHovered(-1, -1)
        
        onClicked: {
            if (root.hoveredSeriesIndex >= 0 && root.hoveredPointIndex >= 0) {
                root.pointClicked(root.hoveredPointIndex, {
                    seriesIndex: root.hoveredSeriesIndex,
                    seriesName: root.series[root.hoveredSeriesIndex].name,
                    indicatorName: root.indicators[root.hoveredPointIndex].name,
                    value: root.series[root.hoveredSeriesIndex].values[root.hoveredPointIndex]
                })
            }
        }
    }
}
