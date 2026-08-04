// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// XYSingleTooltip - Active single-series XY tooltip 当前单系列 XY 图表提示框
Loader {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var chart
    required property var chartBase

    x: {
        if (chart.chartType === Enums.chart.type_bar) {
            if (chart._hoveredBarIndex < 0 || chart._viewChartData.length === 0) return 0
            var barWidth = (chartBase.chartAreaWidth - chart._viewChartData.length * Enums.spacing.s) / chart._viewChartData.length
            return chartBase.chartAreaX + chart._hoveredBarIndex * (barWidth + Enums.spacing.s) + barWidth / 2 - width / 2
        }
        if (chart.chartType === Enums.chart.type_line) {
            return chartBase.chartAreaX + (chart._lineContent ? chart._lineContent.getTooltipPosition(chart._hoveredPointIndex).x : 0) - width / 2
        }
        if (chart._isScatter) {
            return chartBase.chartAreaX + Math.min(Math.max((chart._scatterContent ? chart._scatterContent.tooltipX : 0) - width / 2, 0), chartBase.chartAreaWidth - width)
        }
        return 0
    }
    y: {
        if (chart.chartType === Enums.chart.type_bar)
            return chartBase.chartAreaY + Enums.spacing.m
        if (chart.chartType === Enums.chart.type_line) {
            return chartBase.chartAreaY + (chart._lineContent ? chart._lineContent.getTooltipPosition(chart._hoveredPointIndex).y : 0) - height - Enums.spacing.m
        }
        if (chart._isScatter) {
            return chartBase.chartAreaY + (chart._scatterContent ? chart._scatterContent.tooltipY : 0) - height - Enums.spacing.m
        }
        return 0
    }
    z: Enums.zIndex.tooltip
    active: chart.showTooltip && (
        (chart.chartType === Enums.chart.type_bar
            && chart._barContent !== null && !chart._barContent.isMultiSeries) ||
        (chart.chartType === Enums.chart.type_line
            && chart._lineContent !== null && !chart._lineContent.isMultiSeries) ||
        (chart._isScatter && chart._scatterContent !== null)
    )
    sourceComponent: Component {
        ChartTooltip {
            visible: !chart._viewportTransitionActive &&
                     ((chart.chartType === Enums.chart.type_bar && chart._hoveredBarIndex >= 0) ||
                      (chart.chartType === Enums.chart.type_line && chart._hoveredPointIndex >= 0) ||
                      (chart._isScatter && chart._hoveredScatterSeriesIndex >= 0))
            label: {
                var index = chart.chartType === Enums.chart.type_bar ? chart._hoveredBarIndex : chart._hoveredPointIndex
                if (chart._isScatter) {
                    return chart._hoveredScatterSeriesIndex >= 0 && chart._hoveredScatterSeriesIndex < chart._viewSeries.length
                           ? (chart._viewSeries[chart._hoveredScatterSeriesIndex].name || "") : ""
                }
                return index >= 0 && index < chart._viewChartData.length ? (chart._viewChartData[index].label || "") : ""
            }
            value: {
                var index = chart.chartType === Enums.chart.type_bar ? chart._hoveredBarIndex : chart._hoveredPointIndex
                if (chart._isScatter) {
                    return chart._scatterContent
                           ? "(" + chart._scatterContent.dataX.toFixed(2) + ", " + chart._scatterContent.dataY.toFixed(2) + ")"
                           : ""
                }
                return index >= 0 && index < chart._viewChartData.length ? (chart._viewChartData[index].value || 0) : 0
            }
            valueFormatter: chart.valueFormatter
            showColorDot: chart._isScatter
            dotColor: chart._isScatter && chart._hoveredScatterSeriesIndex >= 0 &&
                      chart._hoveredScatterSeriesIndex < chart._viewSeries.length
                      ? (chart._viewSeries[chart._hoveredScatterSeriesIndex].color || Enums.chartColors.extendedPalette[chart._hoveredScatterSeriesIndex % Enums.chartColors.extendedPalette.length])
                      : Enums.transparent
            isValueString: chart._isScatter
        }
    }
}
