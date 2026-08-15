// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import "../../../data"
import "ChartAxisLayout.js" as ChartAxisLayout

// XYChartCore - Base component for XY-axis charts XY轴图表基类
// Provides common range calculations and axis orchestration for XY charts.
// 提供 XY 图表的范围计算与坐标轴编排。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var chartData
    required property real maxValue
    required property bool showLabels
    required property bool showValues
    required property bool showGrid
    required property string title

    // ==================== Public Props 公开属性 ====================
    property var series: []
    property bool isScatter: false
    property int hoveredIndex: -1
    property real minValue: 0
    property bool isHorizontal: false
    property string subtitle: ""
    property string yAxisSuffix: ""
    property var valueFormatter: null
    property real yAxisLabelWidth: 0
    property bool showLegend: false
    property real viewportScale: 1
    property real viewportOffsetRatio: 0
    property bool viewportTransitionActive: false
    property var categoryProjection: ({ sourceLength: chartData.length,
                                         sourceOffset: 0, sourceIndices: [] })
    property real viewportStart: 0
    property real viewportEnd: 1
    property bool animateValueRange: false

    // ==================== Readonly State 只读状态 ====================
    readonly property Item chartArea: axesLayer.chartArea
    readonly property real chartAreaX: chartArea ? chartArea.x : 0
    readonly property real chartAreaY: chartArea ? chartArea.y : 0
    readonly property real chartAreaWidth: chartArea ? (chartArea.width || 0) : 0
    readonly property real chartAreaHeight: chartArea ? (chartArea.height || 0) : 0
    readonly property bool _hasAxisData: chartData.length > 0 || series.length > 0
    readonly property bool _showGridLines: root.visible && showGrid && _hasAxisData
    readonly property bool _showVerticalValueAxis:
        root.visible && _hasAxisData && !isHorizontal
    readonly property bool _showHorizontalAxes:
        root.visible && isHorizontal && chartData.length > 0
    readonly property bool _showVerticalCategoryAxis: root.visible && showLabels
        && chartData.length > 0 && !isScatter && !isHorizontal
    readonly property bool _showScatterXAxis:
        root.visible && isScatter && series.length > 0
    readonly property var _verticalValueAxisLabels: _buildVerticalValueAxisLabels()
    readonly property var _horizontalValueAxisLabels: _buildHorizontalValueAxisLabels()
    readonly property var _scatterXAxisLabelTexts: _buildScatterXAxisLabels()
    readonly property var _categoryLabelTexts: _buildCategoryLabels()
    readonly property real _categoryViewportStart:
        isFinite(viewportStart) ? Math.max(0, Math.min(1, viewportStart)) : 0
    readonly property real _categoryViewportEnd:
        isFinite(viewportEnd) ? Math.max(_categoryViewportStart, Math.min(1, viewportEnd)) : 1
    readonly property real _categoryViewportSpan:
        Math.max(Enums.chart.viewport_epsilon,
                 _categoryViewportEnd - _categoryViewportStart)
    readonly property int _categorySourceLength:
        categoryProjection && categoryProjection.sourceLength > 0
        ? categoryProjection.sourceLength : chartData.length
    readonly property real effectiveYAxisLabelWidth: {
        if (yAxisLabelWidth > 0) return yAxisLabelWidth
        var labels = isHorizontal ? _categoryLabelTexts : _verticalValueAxisLabels
        return ChartAxisLayout.boundedAxisWidth(
            axisFontMetrics,
            labels,
            Enums.controlSize.chartYAxisWidth,
            Enums.controlSize.chartYAxisMaxWidth,
            Enums.spacing.m + Enums.spacing.s
        )
    }
    readonly property real _categorySlotWidth: _categorySourceLength > 0
        ? chartAreaWidth / (_categorySourceLength * _categoryViewportSpan) : 0
    readonly property int _categoryLabelStride: ChartAxisLayout.categoryStride(
        axisFontMetrics,
        _categoryLabelTexts,
        _categorySlotWidth,
        Enums.spacing.m
    )

    // Value range for charts with negative values 支持负值的数值范围
    readonly property var _calculatedValueRange: {
        var min = 0, max = 0
        // 1) chartData 单 series 模式: 每项 {label, value}
        for (var i = 0; i < chartData.length; i++) {
            var val = chartData[i] && chartData[i].value !== undefined ? chartData[i].value : 0
            if (val < min) min = val
            if (val > max) max = val
        }
        // 2) series 多 series 模式: 每 series {name, values[], color}
        for (var s = 0; s < series.length; s++) {
            var vals = series[s] && series[s].values && typeof series[s].values.length === "number"
                       ? series[s].values : []
            for (var k = 0; k < vals.length; k++) {
                var v = vals[k] !== undefined ? vals[k] : 0
                if (typeof v !== "number" || !isFinite(v)) continue
                if (v < min) min = v
                if (v > max) max = v
            }
        }
        // Add padding 添加边距
        var range = max - min
        var padding = range * 0.1 || 1
        return {
            min: min < 0 ? min - padding : 0,
            max: max > 0 ? max + padding : 0,
            hasNegative: min < 0,
            hasPositive: max > 0
        }
    }
    property real _displayRangeMin: _calculatedValueRange.min
    property real _displayRangeMax: _calculatedValueRange.max
    readonly property var valueRange: {
        var min = _displayRangeMin
        var max = _displayRangeMax
        return {
            min: min,
            max: max,
            hasNegative: min < 0,
            hasPositive: max > 0
        }
    }

    // Zero line position (0-1) 零轴线位置
    readonly property real zeroLineRatio: {
        var range = valueRange
        if (!range.hasNegative) return 1.0
        if (!range.hasPositive) return 0.0
        return range.max / (range.max - range.min)
    }

    // Scatter chart data range 散点图数据范围
    readonly property var scatterDataRange: {
        if (!isScatter || series.length === 0)
            return { xMin: 0, xMax: 1, yMin: 0, yMax: 1 }

        var minX = Infinity, maxX = -Infinity
        var minY = Infinity, maxY = -Infinity

        for (var s = 0; s < series.length; s++) {
            var data = series[s] && series[s].data && typeof series[s].data.length === "number"
                       ? series[s].data : []
            for (var i = 0; i < data.length; i++) {
                if (!data[i] || typeof data[i].length !== "number") continue
                var x = data[i][0], y = data[i][1]
                if (typeof x !== "number" || typeof y !== "number" || !isFinite(x) || !isFinite(y)) continue
                if (x < minX) minX = x
                if (x > maxX) maxX = x
                if (y < minY) minY = y
                if (y > maxY) maxY = y
            }
        }

        if (!isFinite(minX) || !isFinite(maxX) || !isFinite(minY) || !isFinite(maxY))
            return { xMin: 0, xMax: 1, yMin: 0, yMax: 1 }

        var xPadding = (maxX - minX) * 0.1 || 1
        var yPadding = (maxY - minY) * 0.1 || 1
        return {
            xMin: minX - xPadding, xMax: maxX + xPadding,
            yMin: minY - yPadding, yMax: maxY + yPadding
        }
    }

    // ==================== Signals 信号 ====================
    signal xLabelHovered(int index)

    // ==================== Internal Methods 内部方法 ====================
    function _formatAxisValue(value, fallbackText) {
        if (valueFormatter && typeof valueFormatter === "function")
            return String(valueFormatter(value))
        return String(fallbackText) + yAxisSuffix
    }

    function _buildVerticalValueAxisLabels() {
        var labels = []
        for (var index = 0; index < 5; index++) {
            if (isScatter) {
                var scatterRange = scatterDataRange
                var scatterValue = scatterRange.yMax
                    - (scatterRange.yMax - scatterRange.yMin) * index / 4
                labels.push(_formatAxisValue(scatterValue, scatterValue.toFixed(1)))
                continue
            }
            var range = valueRange
            var value = range.max - (range.max - range.min) * index / 4
            var rounded = Math.round(value * 100) / 100
            labels.push(_formatAxisValue(rounded, rounded))
        }
        return labels
    }

    function _buildHorizontalValueAxisLabels() {
        var labels = []
        for (var index = 0; index < 5; index++) {
            var range = valueRange
            var value = range.min + (range.max - range.min) * index / 4
            labels.push(String(Math.round(value * 100) / 100))
        }
        return labels
    }

    function _buildScatterXAxisLabels() {
        var labels = []
        for (var index = 0; index < 6; index++) {
            var range = scatterDataRange
            var value = range.xMin + (range.xMax - range.xMin) * index / 5
            labels.push(value.toFixed(1))
        }
        return labels
    }

    function _buildCategoryLabels() {
        var labels = []
        for (var index = 0; index < chartData.length; index++) {
            var item = chartData[index]
            labels.push(item && item.label !== undefined ? String(item.label) : "")
        }
        return labels
    }

    function _categorySourceIndex(localIndex) {
        var indices = categoryProjection ? categoryProjection.sourceIndices : null
        if (indices && typeof indices.length === "number" && indices.length > localIndex)
            return indices[localIndex]
        var offset = categoryProjection && typeof categoryProjection.sourceOffset === "number"
            ? categoryProjection.sourceOffset : 0
        return offset + localIndex
    }

    function _categorySlotPosition(localIndex, extent) {
        if (_categorySourceLength <= 0) return 0
        var normalized = _categorySourceIndex(localIndex) / _categorySourceLength
        return (normalized - _categoryViewportStart) / _categoryViewportSpan * extent
    }

    function _categorySlotExtent(extent) {
        return _categorySourceLength > 0
            ? extent / (_categorySourceLength * _categoryViewportSpan) : 0
    }

    function _categorySlotIntersectsViewport(localIndex) {
        if (_categorySourceLength <= 0) return false
        var start = _categorySourceIndex(localIndex) / _categorySourceLength
        var end = start + 1 / _categorySourceLength
        return end >= _categoryViewportStart && start <= _categoryViewportEnd
    }

    // ==================== Content 内容 ====================
    ChartTitle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: Enums.spacing.m
        title: root.title
        subtitle: root.subtitle
    }

    FontMetrics {
        id: axisFontMetrics
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.caption
    }

    XYChartAxes {
        id: axesLayer

        chartControl: root
        axisFontMetrics: axisFontMetrics
    }

    Behavior on _displayRangeMin {
        enabled: root.animateValueRange

        NumberAnimation {
            duration: Enums.duration.normal
            easing.type: Easing.InOutCubic
        }
    }

    Behavior on _displayRangeMax {
        enabled: root.animateValueRange

        NumberAnimation {
            duration: Enums.duration.normal
            easing.type: Easing.InOutCubic
        }
    }
}
