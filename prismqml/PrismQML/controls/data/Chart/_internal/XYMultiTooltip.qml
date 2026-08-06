// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// XYMultiTooltip - Active multi-series XY tooltip 当前多系列 XY 图表提示框
Loader {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var chart
    required property var chartBase

    x: {
        if (!chartBase) return 0
        if (chart.chartType === Enums.chart.type_line) {
            var lineMouseX = chart._lineContent ? chart._lineContent.mouseX : 0
            var right = lineMouseX + Enums.spacing.m
            if (right + width <= chartBase.chartAreaWidth)
                return chartBase.chartAreaX + right
            return chartBase.chartAreaX + Math.max(0, lineMouseX - width - Enums.spacing.s)
        }
        if (chart.chartType === Enums.chart.type_bar) {
            var dataLength = chart._barContent ? chart._barContent.dataLength : 0
            if (dataLength <= 0) return chartBase.chartAreaX
            return chartBase.chartAreaX + Math.min(Math.max((chart._hoveredBarIndex + 0.5) * (chartBase.chartAreaWidth / dataLength) - width / 2, 0), chartBase.chartAreaWidth - width)
        }
        return 0
    }
    y: {
        if (!chartBase) return 0
        if (chart.chartType === Enums.chart.type_line) {
            var lineMouseY = chart._lineContent ? chart._lineContent.mouseY : 0
            var below = lineMouseY + Enums.spacing.m
            if (below + height <= chartBase.chartAreaHeight)
                return chartBase.chartAreaY + below
            return chartBase.chartAreaY + Math.max(0, lineMouseY - height - Enums.spacing.s)
        }
        if (chart.chartType === Enums.chart.type_bar)
            return chartBase.chartAreaY + Enums.spacing.m
        return 0
    }
    active: chart.showTooltip && (
        (chart.chartType === Enums.chart.type_bar
            && chart._barContent !== null && chart._barContent.isMultiSeries) ||
        (chart.chartType === Enums.chart.type_line
            && chart._lineContent !== null && chart._lineContent.isMultiSeries)
    )
    sourceComponent: Component {
        ChartMultiTooltip {
            visible: !chart._viewportTransitionActive &&
                     ((chart.chartType === Enums.chart.type_line && chart.showTooltip && chart._hoveredPointIndex >= 0) ||
                      (chart.chartType === Enums.chart.type_bar && chart._hoveredBarIndex >= 0))
            xLabel: {
                var index = chart.chartType === Enums.chart.type_line ? chart._hoveredPointIndex : chart._hoveredBarIndex
                return index >= 0 && index < chart._viewChartData.length ? (chart._viewChartData[index].label || "") : ""
            }
            seriesData: {
                var index = chart.chartType === Enums.chart.type_line ? chart._hoveredPointIndex : chart._hoveredBarIndex
                var result = []
                for (var i = 0; i < chart._viewSeries.length; i++) {
                    var seriesItem = chart._viewSeries[i]
                    var values = seriesItem.values || []
                    result.push({
                        name: seriesItem.name || "",
                        value: index >= 0 && index < values.length ? values[index] : 0,
                        color: seriesItem.color || Enums.chartColors.extendedPalette[i % Enums.chartColors.extendedPalette.length]
                    })
                }
                return result
            }
            showTotal: chart.chartType === Enums.chart.type_line && chart.stacked
            totalValue: {
                if (chart.chartType !== Enums.chart.type_line || chart._hoveredPointIndex < 0) return 0
                var sum = 0
                for (var i = 0; i < chart._viewSeries.length; i++) {
                    var values = chart._viewSeries[i].values || []
                    if (chart._hoveredPointIndex < values.length) sum += values[chart._hoveredPointIndex] || 0
                }
                return sum
            }
            valueFormatter: chart.valueFormatter
        }
    }
}
