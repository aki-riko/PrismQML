// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "LineChartGeometry.js" as Geometry
import "LineChartPainter.js" as Painter

// LineChartCanvas - Line chart canvas renderer 折线图画布渲染器
Canvas {
    id: canvas

    // ==================== Required Props 必需属性 ====================
    required property var lineControl

    // ==================== Internal Props 内部属性 ====================
    property real animProgress: 1.0

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: lineControl

    // ==================== Internal Methods 内部方法 ====================
    function animatedY(targetY, baselineY) {
        return baselineY + (targetY - baselineY) * animProgress
    }

    function paintSingleSeries(ctx, region, fullPaint) {
        if (control.chartData.length < 2) return 0

        var padding = Enums.spacing.m
        var chartHeight = height - padding * 2
        var points = control.pointPositions
        var range = Geometry.paintRange(points, region, fullPaint, padding)
        var pathPoints = fullPaint ? points : points.slice(range.start, range.end)

        if (control.isArea || control.showAreaGradient) {
            Painter.drawAreaFill(ctx, pathPoints, control.primaryColor, padding + chartHeight,
                control.smoothLine, Enums.stateColor.chartFillMedium,
                Enums.stateColor.chartFillSubtle)
        }
        Painter.drawLine(ctx, pathPoints, control.primaryColor, 2, control.smoothLine)

        for (var p = range.start; p < range.end; p++) {
            var hovered = (p === control.hoveredIndex)
            Painter.drawSolidPoint(
                ctx, points[p].x, points[p].y, control.primaryColor,
                hovered, Enums.cardColor
            )
        }
        return range.end - range.start
    }

    function paintMultiSeries(ctx, region, fullPaint) {
        var seriesData = control.series
        if (seriesData.length === 0) return 0

        var maxLen = control._lineGeometry.maxLength
        if (maxLen < 2) return 0
        var drawCount = 0

        // Draw vertical indicator 绘制垂直指示线
        if (control.hoveredIndex >= 0 && control.hoveredIndex < maxLen) {
            var indicatorPoints = control.seriesPointPositions.length > 0
                ? (control.seriesPointPositions[0] || []) : []
            if (control.hoveredIndex < indicatorPoints.length) {
                Painter.drawVerticalIndicator(
                    ctx, indicatorPoints[control.hoveredIndex].x,
                    height, Enums.chartColors.gridLine
                )
            }
        }

        // Reuse cached points 复用缓存点位
        var allPoints = control.seriesPointPositions

        // Draw areas 绘制面积
        if (control.stacked || control.showAreaGradient) {
            for (var ai = seriesData.length - 1; ai >= 0; ai--) {
                var areaPoints = allPoints[ai]
                var areaColor = control.getSeriesColor(ai)
                var areaRange = Geometry.paintRange(
                    areaPoints, region, fullPaint, Enums.spacing.m
                )
                var visibleArea = fullPaint ? areaPoints
                    : areaPoints.slice(areaRange.start, areaRange.end)

                if (control.stacked) {
                    var prevPoints = ai < seriesData.length - 1 ? allPoints[ai + 1] : null
                    var prevRange = Geometry.paintRange(
                        prevPoints, region, fullPaint, Enums.spacing.m
                    )
                    var visiblePrev = !prevPoints || fullPaint ? prevPoints
                        : prevPoints.slice(prevRange.start, prevRange.end)
                    Painter.drawStackedArea(
                        ctx, visibleArea, visiblePrev, areaColor, height,
                        control.smoothLine, Enums.stateColor.chartFillStrong
                    )
                } else if (control.showAreaGradient) {
                    Painter.drawAreaGradient(
                        ctx, visibleArea, areaColor, height, control.smoothLine,
                        Enums.stateColor.chartFillMedium,
                        Enums.stateColor.chartFillLight,
                        Enums.stateColor.chartFillFaint
                    )
                }
            }
        }

        // Draw lines and points 绘制线条和点
        for (var li = 0; li < seriesData.length; li++) {
            var lineSeriesItem = seriesData[li]
            var lineValues = lineSeriesItem && lineSeriesItem.values
                             && typeof lineSeriesItem.values.length === "number"
                             ? lineSeriesItem.values : []
            var lineColor = control.getSeriesColor(li)
            var linePoints = allPoints[li]
            var isLineSeriesHovered = (li === control.hoveredSeriesIndex)
            var lineRange = Geometry.paintRange(
                linePoints, region, fullPaint, Enums.spacing.m
            )
            var visibleLine = fullPaint ? linePoints
                : linePoints.slice(lineRange.start, lineRange.end)

            // Draw average line 绘制平均线
            if (control.showAverage && lineValues.length > 0) {
                var avg = Painter.calculateAverage(lineValues)
                var avgY = control.valueToY(avg)
                Painter.drawAverageLine(
                    ctx, avgY, width, lineColor, Enums.stateColor.chartLineAlpha
                )
            }

            Painter.drawLine(
                ctx, visibleLine, lineColor,
                isLineSeriesHovered ? 2.5 : 2, control.smoothLine
            )

            for (var p = lineRange.start; p < lineRange.end; p++) {
                var hovered = (p === control.hoveredIndex)
                Painter.drawHollowPoint(
                    ctx, linePoints[p].x, linePoints[p].y, lineColor,
                    hovered, Enums.cardColor
                )
            }
            drawCount += lineRange.end - lineRange.start
        }
        return drawCount
    }

    anchors.fill: parent

    onPaint: (region) => {
        var ctx = getContext("2d")
        var fullPaint = control._lineGeometryDirty || !region ||
                (region.x <= 0 && region.y <= 0 &&
                 region.width >= width && region.height >= height)
        if (fullPaint) ctx.clearRect(0, 0, width, height)
        else ctx.clearRect(region.x, region.y, region.width, region.height)
        control._updateAnimatedLineGeometry(control.animated ? animProgress : 1)
        if (!fullPaint) {
            ctx.save()
            ctx.beginPath()
            ctx.rect(region.x, region.y, region.width, region.height)
            ctx.clip()
        }

        if (control.isMultiSeries) {
            control._lastFramePointDrawCount = paintMultiSeries(
                ctx, region, fullPaint
            )
        } else {
            control._lastFramePointDrawCount = paintSingleSeries(
                ctx, region, fullPaint
            )
        }
        if (!fullPaint) ctx.restore()
        control._paintedHoverIndex = control.hoveredIndex
        control._paintedHoverSeriesIndex = control.hoveredSeriesIndex
    }

    Component.onCompleted: {
        if (control.animated) {
            animProgress = 0
            lineAnimation.restart()
        } else {
            requestPaint()
        }
    }
    onVisibleChanged: if (visible) requestPaint()
    onAnimProgressChanged: requestPaint()
    onWidthChanged: control._invalidateLineGeometry()
    onHeightChanged: control._invalidateLineGeometry()

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
