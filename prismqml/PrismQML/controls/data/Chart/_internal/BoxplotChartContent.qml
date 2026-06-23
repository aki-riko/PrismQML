// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// BoxplotChartContent - Boxplot chart rendering component 箱线图渲染组件
// Fluent Design style: clean boxes with subtle hover effects
// Fluent Design 风格：简洁箱体+微妙悬停效果

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    // boxplotData format 数据格式:
    // [{
    //     label: "Category",
    //     min: 10,        // Lower whisker 下须
    //     q1: 25,         // First quartile 第一四分位数
    //     median: 50,     // Median 中位数
    //     q3: 75,         // Third quartile 第三四分位数
    //     max: 90,        // Upper whisker 上须
    //     outliers: [5, 95, 100]  // Optional outliers 可选异常点
    // }, ...]
    required property var boxplotData
    required property bool animated
    required property bool showValues
    required property bool isHorizontal    // Horizontal or vertical 水平或垂直
    
    // ==================== Props 属性 ====================
    property int hoveredIndex: -1
    property color boxColor: Enums.accentColor
    
    // ==================== Signals 信号 ====================
    signal boxClicked(int index, var data)
    signal boxHovered(int index)
    
    // ==================== Computed Props 计算属性 ====================
    readonly property int dataLength: boxplotData.length
    readonly property var valueRange: {
        var min = Infinity, max = -Infinity
        for (var i = 0; i < boxplotData.length; i++) {
            var d = boxplotData[i]
            if (d.min < min) min = d.min
            if (d.max > max) max = d.max
            // Check outliers 检查异常点
            var outliers = d.outliers || []
            for (var j = 0; j < outliers.length; j++) {
                if (outliers[j] < min) min = outliers[j]
                if (outliers[j] > max) max = outliers[j]
            }
        }
        var padding = (max - min) * 0.1 || 1
        return { min: min - padding, max: max + padding }
    }

    // ==================== Helper Functions 辅助函数 ====================
    function valueToPosition(value) {
        var range = valueRange.max - valueRange.min
        if (range === 0) return isHorizontal ? width / 2 : height / 2
        var ratio = (value - valueRange.min) / range
        return isHorizontal ? ratio * width : height - ratio * height
    }
    
    function getBoxColor(index) {
        if (boxplotData[index] && boxplotData[index].color) return boxplotData[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }

    // ==================== Canvas 画布 ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        
        property real animProgress: root.animated ? 0 : 1
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            if (root.boxplotData.length === 0) return
            
            var dataLen = root.dataLength
            
            if (root.isHorizontal) {
                paintHorizontal(ctx, dataLen)
            } else {
                paintVertical(ctx, dataLen)
            }
        }
        
        function paintVertical(ctx, dataLen) {
            var groupWidth = width / dataLen
            var boxWidth = Math.min(groupWidth * 0.6, Enums.spacing.xxxl * 2)
            
            // Fluent Design: subtle vertical indicator line 微妙垂直指示线
            if (root.hoveredIndex >= 0 && root.hoveredIndex < dataLen) {
                var indicatorX = (root.hoveredIndex + 0.5) * groupWidth
                ctx.beginPath()
                ctx.strokeStyle = Enums.chartColors.gridLine
                ctx.lineWidth = 1
                ctx.moveTo(indicatorX, 0)
                ctx.lineTo(indicatorX, height)
                ctx.stroke()
            }
            
            for (var i = 0; i < dataLen; i++) {
                var d = root.boxplotData[i]
                var centerX = (i + 0.5) * groupWidth
                var hovered = (i === root.hoveredIndex)
                var color = root.getBoxColor(i)
                
                // Calculate positions 计算位置
                var minY = root.valueToPosition(d.min) * animProgress + height * (1 - animProgress)
                var q1Y = root.valueToPosition(d.q1) * animProgress + height * (1 - animProgress)
                var medianY = root.valueToPosition(d.median) * animProgress + height * (1 - animProgress)
                var q3Y = root.valueToPosition(d.q3) * animProgress + height * (1 - animProgress)
                var maxY = root.valueToPosition(d.max) * animProgress + height * (1 - animProgress)
                
                var halfBox = boxWidth / 2
                var whiskerWidth = boxWidth * 0.4
                
                // Draw lower whisker (min to Q1) 绘制下须线
                ctx.beginPath()
                ctx.strokeStyle = color
                ctx.lineWidth = hovered ? 2 : 1.5
                ctx.moveTo(centerX, q1Y)
                ctx.lineTo(centerX, minY)
                ctx.stroke()
                
                // Draw lower whisker cap 绘制下须端点
                ctx.beginPath()
                ctx.moveTo(centerX - whiskerWidth, minY)
                ctx.lineTo(centerX + whiskerWidth, minY)
                ctx.stroke()
                
                // Draw upper whisker (Q3 to max) 绘制上须线
                ctx.beginPath()
                ctx.moveTo(centerX, q3Y)
                ctx.lineTo(centerX, maxY)
                ctx.stroke()
                
                // Draw upper whisker cap 绘制上须端点
                ctx.beginPath()
                ctx.moveTo(centerX - whiskerWidth, maxY)
                ctx.lineTo(centerX + whiskerWidth, maxY)
                ctx.stroke()
                
                // Draw box (Q1 to Q3) 绘制箱体
                var boxHeight = Math.abs(q1Y - q3Y)
                var boxTop = Math.min(q1Y, q3Y)
                
                // Fluent Design: simple box with subtle hover lightening 简洁箱体+微妙悬停提亮
                ctx.fillStyle = hovered ? Qt.lighter(color, 1.1) : Qt.lighter(color, 1.2)
                ctx.fillRect(centerX - halfBox, boxTop, boxWidth, boxHeight)
                
                // Box border 箱体边框
                ctx.strokeStyle = color
                ctx.lineWidth = hovered ? 2 : 1.5
                ctx.strokeRect(centerX - halfBox, boxTop, boxWidth, boxHeight)
                
                // Draw median line 绘制中位线
                ctx.beginPath()
                ctx.strokeStyle = hovered ? Enums.textColor.primary : color
                ctx.lineWidth = 2
                ctx.moveTo(centerX - halfBox, medianY)
                ctx.lineTo(centerX + halfBox, medianY)
                ctx.stroke()
                
                // Fluent Design: simple outlier points 简洁异常点
                var outliers = d.outliers || []
                for (var j = 0; j < outliers.length; j++) {
                    var outlierY = root.valueToPosition(outliers[j]) * animProgress + height * (1 - animProgress)
                    var outlierSize = hovered ? 4 : 3
                    
                    // Solid point 实心点
                    ctx.beginPath()
                    ctx.fillStyle = color
                    ctx.arc(centerX, outlierY, outlierSize, 0, Math.PI * 2)
                    ctx.fill()
                    
                    // Hollow center 空心中心
                    ctx.beginPath()
                    ctx.fillStyle = Enums.cardColor
                    ctx.arc(centerX, outlierY, outlierSize * 0.5, 0, Math.PI * 2)
                    ctx.fill()
                }
                
                // Draw value labels 绘制数值标签
                if (root.showValues && animProgress >= 1) {
                    ctx.fillStyle = Enums.textColor.secondary
                    ctx.font = Enums.typography.caption + "px " + Enums.canvasFontFamily
                    ctx.textAlign = "left"
                    ctx.textBaseline = "middle"
                    
                    var labelX = centerX + halfBox + Enums.spacing.xs
                    ctx.fillText(d.max.toString(), labelX, maxY)
                    ctx.fillText(d.q3.toString(), labelX, q3Y)
                    ctx.fillText(d.median.toString(), labelX, medianY)
                    ctx.fillText(d.q1.toString(), labelX, q1Y)
                    ctx.fillText(d.min.toString(), labelX, minY)
                }
            }
        }

        function paintHorizontal(ctx, dataLen) {
            var groupHeight = height / dataLen
            var boxHeight = Math.min(groupHeight * 0.6, Enums.spacing.xxxl * 2)
            
            // Fluent Design: subtle horizontal indicator line 微妙水平指示线
            if (root.hoveredIndex >= 0 && root.hoveredIndex < dataLen) {
                var indicatorY = (root.hoveredIndex + 0.5) * groupHeight
                ctx.beginPath()
                ctx.strokeStyle = Enums.chartColors.gridLine
                ctx.lineWidth = 1
                ctx.moveTo(0, indicatorY)
                ctx.lineTo(width, indicatorY)
                ctx.stroke()
            }
            
            for (var i = 0; i < dataLen; i++) {
                var d = root.boxplotData[i]
                var centerY = (i + 0.5) * groupHeight
                var hovered = (i === root.hoveredIndex)
                var color = root.getBoxColor(i)
                
                // Calculate positions 计算位置
                var minX = root.valueToPosition(d.min) * animProgress
                var q1X = root.valueToPosition(d.q1) * animProgress
                var medianX = root.valueToPosition(d.median) * animProgress
                var q3X = root.valueToPosition(d.q3) * animProgress
                var maxX = root.valueToPosition(d.max) * animProgress
                
                var halfBox = boxHeight / 2
                var whiskerHeight = boxHeight * 0.4
                
                // Draw left whisker (min to Q1) 绘制左须线
                ctx.beginPath()
                ctx.strokeStyle = color
                ctx.lineWidth = hovered ? 2 : 1.5
                ctx.moveTo(minX, centerY)
                ctx.lineTo(q1X, centerY)
                ctx.stroke()
                
                // Draw left whisker cap 绘制左须端点
                ctx.beginPath()
                ctx.moveTo(minX, centerY - whiskerHeight)
                ctx.lineTo(minX, centerY + whiskerHeight)
                ctx.stroke()
                
                // Draw right whisker (Q3 to max) 绘制右须线
                ctx.beginPath()
                ctx.moveTo(q3X, centerY)
                ctx.lineTo(maxX, centerY)
                ctx.stroke()
                
                // Draw right whisker cap 绘制右须端点
                ctx.beginPath()
                ctx.moveTo(maxX, centerY - whiskerHeight)
                ctx.lineTo(maxX, centerY + whiskerHeight)
                ctx.stroke()
                
                // Draw box (Q1 to Q3) 绘制箱体
                var boxWidth = Math.abs(q3X - q1X)
                var boxLeft = Math.min(q1X, q3X)
                
                // Fluent Design: simple box with subtle hover lightening 简洁箱体+微妙悬停提亮
                ctx.fillStyle = hovered ? Qt.lighter(color, 1.1) : Qt.lighter(color, 1.2)
                ctx.fillRect(boxLeft, centerY - halfBox, boxWidth, boxHeight)
                
                // Box border 箱体边框
                ctx.strokeStyle = color
                ctx.lineWidth = hovered ? 2 : 1.5
                ctx.strokeRect(boxLeft, centerY - halfBox, boxWidth, boxHeight)
                
                // Draw median line 绘制中位线
                ctx.beginPath()
                ctx.strokeStyle = hovered ? Enums.textColor.primary : color
                ctx.lineWidth = 2
                ctx.moveTo(medianX, centerY - halfBox)
                ctx.lineTo(medianX, centerY + halfBox)
                ctx.stroke()
                
                // Fluent Design: simple outlier points 简洁异常点
                var outliers = d.outliers || []
                for (var j = 0; j < outliers.length; j++) {
                    var outlierX = root.valueToPosition(outliers[j]) * animProgress
                    var outlierSize = hovered ? 4 : 3
                    
                    // Solid point 实心点
                    ctx.beginPath()
                    ctx.fillStyle = color
                    ctx.arc(outlierX, centerY, outlierSize, 0, Math.PI * 2)
                    ctx.fill()
                    
                    // Hollow center 空心中心
                    ctx.beginPath()
                    ctx.fillStyle = Enums.cardColor
                    ctx.arc(outlierX, centerY, outlierSize * 0.5, 0, Math.PI * 2)
                    ctx.fill()
                }
            }
        }
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                animTimer.start()
            } else {
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
    
    // Repaint triggers 重绘触发
    onHoveredIndexChanged: canvas.requestPaint()
    onBoxplotDataChanged: canvas.requestPaint()
    onIsHorizontalChanged: canvas.requestPaint()

    // ==================== Mouse Area 鼠标区域 ====================
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onPositionChanged: (mouse) => {
            var dataLen = root.dataLength
            if (dataLen === 0) return
            
            var foundIndex = -1
            
            if (root.isHorizontal) {
                var groupHeight = height / dataLen
                foundIndex = Math.floor(mouse.y / groupHeight)
            } else {
                var groupWidth = width / dataLen
                foundIndex = Math.floor(mouse.x / groupWidth)
            }
            
            if (foundIndex >= 0 && foundIndex < dataLen) {
                root.boxHovered(foundIndex)
            } else {
                root.boxHovered(-1)
            }
        }
        
        onExited: root.boxHovered(-1)
        
        onClicked: {
            if (root.hoveredIndex >= 0) {
                root.boxClicked(root.hoveredIndex, root.boxplotData[root.hoveredIndex])
            }
        }
    }
}
