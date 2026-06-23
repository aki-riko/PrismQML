// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    // ==================== Props 属性 ====================
    property int hoveredSeriesIndex: -1
    property int hoveredPointIndex: -1
    property int defaultSymbolSize: 10       // Default symbol size if not specified in series 默认点大小
    
    // ==================== Signals 信号 ====================
    signal pointClicked(int pointIndex, var data)
    signal pointHovered(int seriesIndex, int pointIndex)
    
    // ==================== Internal 内部属性 ====================
    property var pointPositions: []
    property real tooltipX: 0
    property real tooltipY: 0
    property real dataX: 0
    property real dataY: 0
    
    // ==================== Helper Functions 辅助函数 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function isEffectScatter(seriesItem) {
        return seriesItem && seriesItem.type === "effectScatter"
    }
    
    // ==================== Canvas 画布 ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        
        property real animProgress: 0
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            var range = root.dataRange
            var xScale = width / (range.xMax - range.xMin)
            var yScale = height / (range.yMax - range.yMin)
            
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
            var allPoints = []
            
            // First pass: draw normal scatter 第一遍：绘制普通散点
            for (var s = 0; s < root.series.length; s++) {
                var seriesData = root.series[s]
                if (root.isEffectScatter(seriesData)) continue
                
                var data = seriesData.data || []
                var color = root.getSeriesColor(s)
                var baseSymbolSize = (seriesData.symbolSize || root.defaultSymbolSize) * progress
                var isSeriesHovered = (s === root.hoveredSeriesIndex)
                
                for (var k = 0; k < data.length; k++) {
                    var px = (data[k][0] - range.xMin) * xScale
                    var py = height - (data[k][1] - range.yMin) * yScale
                    
                    allPoints.push({
                        x: px, y: py,
                        seriesIndex: s, pointIndex: k,
                        dataX: data[k][0], dataY: data[k][1],
                        isEffect: false
                    })
                    
                    var isPointHovered = (s === root.hoveredSeriesIndex && k === root.hoveredPointIndex)
                    var symbolSize = isPointHovered ? baseSymbolSize * 1.3 : baseSymbolSize
                    
                    // Fluent Design: simple solid point 简洁实心点
                    ctx.beginPath()
                    ctx.fillStyle = color
                    ctx.globalAlpha = isPointHovered ? 1.0 : 0.8
                    ctx.arc(px, py, symbolSize / 2, 0, Math.PI * 2)
                    ctx.fill()
                    ctx.globalAlpha = 1
                }
            }
            
            // Second pass: draw effectScatter (highlighted points) 第二遍：绘制高亮点
            for (var es = 0; es < root.series.length; es++) {
                var effectSeriesData = root.series[es]
                if (!root.isEffectScatter(effectSeriesData)) continue
                
                var effectData = effectSeriesData.data || []
                var effectColor = root.getSeriesColor(es)
                var effectSymbolSize = (effectSeriesData.symbolSize || 16) * progress
                
                for (var ek = 0; ek < effectData.length; ek++) {
                    var epx = (effectData[ek][0] - range.xMin) * xScale
                    var epy = height - (effectData[ek][1] - range.yMin) * yScale
                    
                    allPoints.push({
                        x: epx, y: epy,
                        seriesIndex: es, pointIndex: ek,
                        dataX: effectData[ek][0], dataY: effectData[ek][1],
                        isEffect: true
                    })
                    
                    var isEffectHovered = (es === root.hoveredSeriesIndex && ek === root.hoveredPointIndex)
                    
                    // Fluent Design: subtle outer ring for emphasis 微妙外环强调
                    ctx.beginPath()
                    ctx.strokeStyle = effectColor
                    ctx.lineWidth = 2
                    ctx.globalAlpha = 0.4
                    ctx.arc(epx, epy, effectSymbolSize / 2 + 4, 0, Math.PI * 2)
                    ctx.stroke()
                    
                    // Solid point 实心点
                    ctx.beginPath()
                    ctx.fillStyle = effectColor
                    ctx.globalAlpha = isEffectHovered ? 1.0 : 0.9
                    ctx.arc(epx, epy, effectSymbolSize / 2, 0, Math.PI * 2)
                    ctx.fill()
                    
                    ctx.globalAlpha = 1
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
                var hitRadius = pt.isEffect ? 20 : 15
                if (dist < hitRadius && dist < minDist) {
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
                        root.dataX = p.dataX
                        root.dataY = p.dataY
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
                    x: root.dataX,
                    y: root.dataY,
                    isEffect: root.series[root.hoveredSeriesIndex].type === "effectScatter"
                })
            }
        }
    }
}
