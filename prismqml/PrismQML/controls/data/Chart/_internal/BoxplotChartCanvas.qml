// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "BoxplotChartGeometry.js" as Geometry

// BoxplotChartCanvas - Boxplot canvas renderer 箱线图画布渲染器
Canvas {
    id: canvas

    // ==================== Required Props 必需属性 ====================
    required property var boxplotControl

    // ==================== Internal Props 内部属性 ====================
    property real animProgress: boxplotControl.animated ? 0 : 1

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: boxplotControl

    // ==================== Internal Methods 内部方法 ====================
    function paintVertical(ctx, dataLen, startIndex, endIndex) {
        var groupWidth = control._boxGeometryGroupSize
        var boxWidth = control._boxGeometrySize
        var drawCount = 0

        // Fluent Design: subtle vertical indicator line 微妙垂直指示线
        if (control.hoveredIndex >= 0 && control.hoveredIndex < dataLen) {
            var indicatorX = (control.hoveredIndex + 0.5) * groupWidth
            ctx.beginPath()
            ctx.strokeStyle = Enums.chartColors.gridLine
            ctx.lineWidth = 1
            ctx.moveTo(indicatorX, 0)
            ctx.lineTo(indicatorX, height)
            ctx.stroke()
        }

        for (var i = startIndex; i < endIndex; i++) {
            var geometry = control._boxGeometry[i]
            if (!geometry) continue
            drawCount++
            var d = control.boxplotData[i]
            var centerX = geometry.center
            var hovered = (i === control.hoveredIndex)
            var color = control.getBoxColor(i)

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
            if (control.showValues && animProgress >= 1) {
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
        return drawCount
    }

    function paintHorizontal(ctx, dataLen, startIndex, endIndex) {
        var groupHeight = control._boxGeometryGroupSize
        var boxHeight = control._boxGeometrySize
        var drawCount = 0

        // Fluent Design: subtle horizontal indicator line 微妙水平指示线
        if (control.hoveredIndex >= 0 && control.hoveredIndex < dataLen) {
            var indicatorY = (control.hoveredIndex + 0.5) * groupHeight
            ctx.beginPath()
            ctx.strokeStyle = Enums.chartColors.gridLine
            ctx.lineWidth = 1
            ctx.moveTo(0, indicatorY)
            ctx.lineTo(width, indicatorY)
            ctx.stroke()
        }

        for (var i = startIndex; i < endIndex; i++) {
            var geometry = control._boxGeometry[i]
            if (!geometry) continue
            drawCount++
            var centerY = geometry.center
            var hovered = (i === control.hoveredIndex)
            var color = control.getBoxColor(i)

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
        return drawCount
    }

    anchors.fill: parent

    onPaint: (region) => {
        var ctx = getContext("2d")
        var fullPaint = control._boxGeometryDirty || !region ||
                (region.x <= 0 && region.y <= 0 &&
                 region.width >= width && region.height >= height)
        if (fullPaint) ctx.clearRect(0, 0, width, height)
        else ctx.clearRect(region.x, region.y, region.width, region.height)

        if (control.boxplotData.length === 0) {
            control._lastFrameBoxDrawCount = 0
            control._paintedHoverIndex = control.hoveredIndex
            return
        }

        var dataLen = control.dataLength
        control._updateAnimatedGeometry(control.animated ? animProgress : 1)
        var range = Geometry.paintRange(
            region, fullPaint, dataLen, control._boxGeometryGroupSize,
            control.isHorizontal, Enums.spacing.xs + Enums.border.thin
        )
        if (!fullPaint) {
            ctx.save()
            ctx.beginPath()
            ctx.rect(region.x, region.y, region.width, region.height)
            ctx.clip()
        }

        if (control.isHorizontal) {
            control._lastFrameBoxDrawCount = paintHorizontal(
                ctx, dataLen, range.start, range.end
            )
        } else {
            control._lastFrameBoxDrawCount = paintVertical(
                ctx, dataLen, range.start, range.end
            )
        }
        if (!fullPaint) ctx.restore()
        control._paintedHoverIndex = control.hoveredIndex
    }

    onWidthChanged: control._invalidateBoxGeometry()
    onHeightChanged: control._invalidateBoxGeometry()

    Component.onCompleted: {
        if (control.animated) {
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
