// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    
    // ==================== Public Props 公开属性 ====================
    property int hoveredIndex: -1
    property color boxColor: Enums.accentColor

    // ==================== Internal Props 内部属性 ====================
    property var _boxGeometry: []
    property bool _boxGeometryDirty: true
    property int _boxGeometryBuildCount: 0
    property int _lastFramePointUpdateCount: 0
    property real _boxGeometryGroupSize: 0
    property real _boxGeometrySize: 0
    property real _lastGeometryProgress: -1

    // ==================== Readonly State 只读状态 ====================
    readonly property int dataLength: boxplotData.length
    readonly property var valueRange: {
        var min = Infinity, max = -Infinity
        for (var i = 0; i < boxplotData.length; i++) {
            var d = boxplotData[i]
            if (!d || typeof d.min !== "number" || typeof d.q1 !== "number" ||
                    typeof d.median !== "number" || typeof d.q3 !== "number" ||
                    typeof d.max !== "number" || !isFinite(d.min) || !isFinite(d.q1) ||
                    !isFinite(d.median) || !isFinite(d.q3) || !isFinite(d.max)) continue
            if (d.min < min) min = d.min
            if (d.max > max) max = d.max
            // Check outliers 检查异常点
            var outliers = d.outliers || []
            for (var j = 0; j < outliers.length; j++) {
                if (typeof outliers[j] !== "number" || !isFinite(outliers[j])) continue
                if (outliers[j] < min) min = outliers[j]
                if (outliers[j] > max) max = outliers[j]
            }
        }
        if (!isFinite(min) || !isFinite(max)) return { min: 0, max: 1 }
        var padding = (max - min) * 0.1 || 1
        return { min: min - padding, max: max + padding }
    }

    // ==================== Signals 信号 ====================
    signal boxClicked(int index, var data)
    signal boxHovered(int index)

    // ==================== Internal Methods 内部方法 ====================
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

    function _isValidBoxplot(item) {
        return item && typeof item.min === "number" && typeof item.q1 === "number" &&
               typeof item.median === "number" && typeof item.q3 === "number" &&
               typeof item.max === "number" && isFinite(item.min) && isFinite(item.q1) &&
               isFinite(item.median) && isFinite(item.q3) && isFinite(item.max)
    }

    function _buildBoxGeometryItem(index) {
        var item = boxplotData[index]
        if (!_isValidBoxplot(item)) return null
        var outlierFinalPositions = []
        var outlierPositions = []
        var outliers = item.outliers || []
        for (var outlierIndex = 0; outlierIndex < outliers.length; outlierIndex++) {
            outlierFinalPositions.push(valueToPosition(outliers[outlierIndex]))
            outlierPositions.push(0)
        }
        return {
            center: (index + 0.5) * _boxGeometryGroupSize,
            minFinal: valueToPosition(item.min), q1Final: valueToPosition(item.q1),
            medianFinal: valueToPosition(item.median), q3Final: valueToPosition(item.q3),
            maxFinal: valueToPosition(item.max),
            minPosition: 0, q1Position: 0, medianPosition: 0,
            q3Position: 0, maxPosition: 0,
            outlierFinalPositions: outlierFinalPositions,
            outlierPositions: outlierPositions
        }
    }

    function _rebuildBoxGeometry(canvasWidth, canvasHeight) {
        var dataLen = dataLength
        var crossSize = isHorizontal ? canvasHeight : canvasWidth
        _boxGeometryGroupSize = dataLen > 0 ? crossSize / dataLen : 0
        _boxGeometrySize = Math.min(_boxGeometryGroupSize * 0.6, Enums.spacing.xxxl * 2)
        var geometry = []
        for (var index = 0; index < dataLen; index++) {
            geometry.push(_buildBoxGeometryItem(index))
        }
        _boxGeometry = geometry
        _boxGeometryDirty = false
        _lastGeometryProgress = -1
        _boxGeometryBuildCount++
    }

    function _updateBoxGeometryItem(geometry, progress, baseline) {
        geometry.minPosition = geometry.minFinal * progress + baseline
        geometry.q1Position = geometry.q1Final * progress + baseline
        geometry.medianPosition = geometry.medianFinal * progress + baseline
        geometry.q3Position = geometry.q3Final * progress + baseline
        geometry.maxPosition = geometry.maxFinal * progress + baseline
        for (var index = 0; index < geometry.outlierFinalPositions.length; index++) {
            geometry.outlierPositions[index] = geometry.outlierFinalPositions[index] * progress + baseline
        }
        return 5 + geometry.outlierFinalPositions.length
    }

    function _updateAnimatedGeometry(progress) {
        if (_boxGeometryDirty) _rebuildBoxGeometry(width, height)
        if (progress === _lastGeometryProgress) {
            _lastFramePointUpdateCount = 0
            return
        }
        var baseline = isHorizontal ? 0 : height * (1 - progress)
        var updateCount = 0
        for (var index = 0; index < _boxGeometry.length; index++) {
            var geometry = _boxGeometry[index]
            if (geometry) updateCount += _updateBoxGeometryItem(geometry, progress, baseline)
        }
        _lastFramePointUpdateCount = updateCount
        _lastGeometryProgress = progress
    }

    function _invalidateBoxGeometry() {
        _boxGeometryDirty = true
        canvas.requestPaint()
    }

    onHoveredIndexChanged: canvas.requestPaint()
    onBoxplotDataChanged: _invalidateBoxGeometry()
    onIsHorizontalChanged: _invalidateBoxGeometry()

    // ==================== Content 内容 ====================
    // Canvas 画布
    Canvas {
        id: canvas

        property real animProgress: root.animated ? 0 : 1

        function paintVertical(ctx, dataLen) {
            var groupWidth = root._boxGeometryGroupSize
            var boxWidth = root._boxGeometrySize
            
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
                var geometry = root._boxGeometry[i]
                if (!geometry) continue
                var d = root.boxplotData[i]
                var centerX = geometry.center
                var hovered = (i === root.hoveredIndex)
                var color = root.getBoxColor(i)
                
                // Reuse animated positions 复用动画坐标
                var minY = geometry.minPosition
                var q1Y = geometry.q1Position
                var medianY = geometry.medianPosition
                var q3Y = geometry.q3Position
                var maxY = geometry.maxPosition
                
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
                var outlierPositions = geometry.outlierPositions
                for (var j = 0; j < outlierPositions.length; j++) {
                    var outlierY = outlierPositions[j]
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
            var groupHeight = root._boxGeometryGroupSize
            var boxHeight = root._boxGeometrySize
            
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
                var geometry = root._boxGeometry[i]
                if (!geometry) continue
                var centerY = geometry.center
                var hovered = (i === root.hoveredIndex)
                var color = root.getBoxColor(i)
                
                // Reuse animated positions 复用动画坐标
                var minX = geometry.minPosition
                var q1X = geometry.q1Position
                var medianX = geometry.medianPosition
                var q3X = geometry.q3Position
                var maxX = geometry.maxPosition
                
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
                var outlierPositions = geometry.outlierPositions
                for (var j = 0; j < outlierPositions.length; j++) {
                    var outlierX = outlierPositions[j]
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

        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            if (root.boxplotData.length === 0) return

            var dataLen = root.dataLength
            root._updateAnimatedGeometry(root.animated ? animProgress : 1)

            if (root.isHorizontal) {
                paintHorizontal(ctx, dataLen)
            } else {
                paintVertical(ctx, dataLen)
            }
        }

        onWidthChanged: root._invalidateBoxGeometry()
        onHeightChanged: root._invalidateBoxGeometry()

        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                chartAnimation.restart()
            } else {
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
