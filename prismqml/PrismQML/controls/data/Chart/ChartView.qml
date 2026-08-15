// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "_internal"
import "_internal/ChartViewport.js" as ChartViewport
import "../Label"

// ChartView - Fluent Design chart component 综合图表组件
// Supports Bar/Line/Pie/Scatter/Radar/Boxplot with Fluent Design styling 支持柱状图/折线图/饼图/散点图/雷达图/箱线图，Fluent Design 风格

ShadowedRectangle {
    id: control
    // ==================== Public Props 公开属性 ====================
    property int chartType: Enums.chart.type_bar
    property int barOrientation: Enums.chart.orientation_vertical
    property var chartData: []           // [{label: "", value: 0, color: ""}, ...]
    property var indicators: []          // [{name: "", max: 100}, ...] - for radar
    property var series: []              // [{name: "", values/data: [], color: ""}, ...]
    property var boxplotData: []         // [{label: "", min, q1, median, q3, max, outliers: []}, ...]
    property string title: ""
    property string subtitle: ""
    property string yAxisSuffix: ""
    // Explicit Y-axis width; zero enables content measurement 显式Y轴宽度；0表示按内容自动测量
    property real yAxisLabelWidth: 0
    property color primaryColor: Enums.accentColor
    property bool showLabels: true
    property bool showValues: true
    property bool showLegend: true
    property bool showGrid: true
    // 是否显示 hover tooltip; 折线图数据点过密时关闭可显著减少掉帧
    property bool showTooltip: true
    property bool animated: true
    property bool smoothLine: true
    property bool showAverage: false
    property bool showMinMax: false
    property int rings: 5
    property string emptyText: ""
    property string donutCenterText: ""
    property string donutCenterSubtext: ""
    property bool isDonut: false
    property real donutRatio: 0.6
    property bool emphasisCenter: false
    property bool labelOutside: false
    property var valueFormatter: null
    property bool boundaryGap: true
    property bool showAreaGradient: false
    property bool showBarGradient: false
    property bool showAxisTick: true
    property bool stacked: false
    property int symbolSize: 10

    // DataZoom viewport relative to the full data range 数据缩放视窗相对于全量数据的范围
    // Wheel, chart panning, and the slider share viewportChanged 滚轮、主图平移和滑块统一通过 viewportChanged 同步
    property real viewportStart: 0
    property real viewportEnd: 1
    // Show the thumbnail range slider below the chart 是否在主图下方显示缩略图范围滑块
    property bool dataZoomEnabled: false
    // Enable click-and-drag chart panning 是否启用按住主图拖动平移
    property bool panEnabled: true
    // Maximum point count after viewport slicing and LTTB sampling 视窗切片与 LTTB 抽样后的最大点数
    property int lttbThreshold: Enums.chart.lttb_threshold

    // ==================== Readonly State 只读状态 ====================
    readonly property real maxValue: {
        var max = 0
        for (var i = 0; i < _chartData.length; i++) {
            if (_chartData[i] && _chartData[i].value > max) max = _chartData[i].value
        }
        return max || 1
    }
    readonly property real totalValue: {
        var sum = 0
        for (var i = 0; i < _chartData.length; i++) {
            if (_chartData[i]) sum += _chartData[i].value || 0
        }
        return sum || 1
    }
    readonly property var defaultColors: Enums.chartColors.palette
    // Normalize nullable Python/QML list properties before renderer access 归一化可空的 Python/QML 列表，避免渲染器直接读取 null.length
    readonly property var _chartData: _normalizeChartData(chartData)
    readonly property var _indicators: _normalizeIndicators(indicators)
    readonly property var _series: _normalizeSeries(series)
    readonly property var _boxplotData: _validBoxplotData(boxplotData)
    readonly property bool _hasChartData: _chartData.length > 0
    readonly property bool _hasSeriesValues: _hasRenderableSeries(_series, "values")
    readonly property bool _hasScatterData: _hasRenderableSeries(_series, "data")
    readonly property bool _hasSeriesData: _hasSeriesValues || _hasScatterData
    readonly property bool _hasRadarData: _indicators.length > 2 && _hasSeriesValues
    readonly property bool _hasBoxplotData: _boxplotData.length > 0

    // Size and style 尺寸与样式
    // Size priority (manual, ShadowedRectangle can't extend Widget) 尺寸优先级（手动实现，ShadowedRectangle 无法继承 Widget）
    property real preferredWidth: 0
    property real preferredHeight: 0
    property real contentWidth: Enums.controlSize.chartDefaultWidth
    property real contentHeight: Enums.controlSize.chartDefaultHeight

    // Chart card entrance animation 图表卡片入场动画
    property bool deferAnimation: false  // Set true for lazy-loaded charts 懒加载图表设为true

    // ==================== Internal Props 内部属性 ====================
    // Disable viewport transitions during direct manipulation 直接拖动期间禁用视窗过渡
    property bool _viewportInteractive: false
    readonly property var _renderViewport: viewportAnimator.renderViewport
    readonly property real _renderStart: _renderViewport.start
    readonly property real _renderEnd: _renderViewport.end
    readonly property real _viewportScale: viewportAnimator.scaleValue
    readonly property real _viewportOffsetRatio: viewportAnimator.offsetRatio
    readonly property real _visualStart: viewportAnimator.visualStart
    readonly property real _visualEnd: viewportAnimator.visualEnd
    readonly property bool _viewportTransitionActive: viewportAnimator.active
    property int _hoveredBarIndex: -1
    property int _hoveredBarSeriesIndex: -1
    property int _hoveredPointIndex: -1
    property int _hoveredSliceIndex: -1
    property int _hoveredRadarSeriesIndex: -1
    property int _hoveredRadarPointIndex: -1
    property int _hoveredScatterSeriesIndex: -1
    property int _hoveredScatterPointIndex: -1
    property int _hoveredLineSeriesIndex: -1
    property int _hoveredBoxplotIndex: -1
    property var _hiddenSeriesIndices: []

    readonly property bool _isXYChart: chartType === Enums.chart.type_bar ||
                                       chartType === Enums.chart.type_line ||
                                       chartType === Enums.chart.type_scatter
    readonly property bool _isPie: chartType === Enums.chart.type_pie
    readonly property bool _isRadar: chartType === Enums.chart.type_radar
    readonly property bool _isScatter: chartType === Enums.chart.type_scatter
    readonly property bool _isBoxplot: chartType === Enums.chart.type_boxplot
    readonly property bool _isHorizontalBar: chartType === Enums.chart.type_bar &&
                                             barOrientation === Enums.chart.orientation_horizontal
    readonly property var _xyChartBase: renderLayer.xyChartBaseLoader.item
    readonly property var _barContent: renderLayer.barContentLoader.item
    readonly property var _lineContent: renderLayer.lineContentLoader.item
    readonly property var _scatterContent: renderLayer.scatterContentLoader.item

    // Slice the viewport before LTTB sampling to preserve trends and extrema 先按视窗切片，再用 LTTB 保留趋势与峰谷
    readonly property var _viewSeriesProjection: ChartViewport.projectSeries(
        _series, _renderViewport.start, _renderViewport.end, lttbThreshold
    )
    readonly property var _viewSeries: _viewSeriesProjection.data
    readonly property var _viewChartDataProjection: ChartViewport.projectChartData(
        _chartData, _renderViewport.start, _renderViewport.end, lttbThreshold,
        _viewSeriesProjection.valueSources.length > 0
            ? _viewSeriesProjection.valueSources[0] : null
    )
    readonly property var _viewChartData: _viewChartDataProjection.data

    // ==================== Signals 信号 ====================
    signal barClicked(int index, var data)
    signal pointClicked(int index, var data)
    signal sliceClicked(int index, var data)
    signal boxClicked(int index, var data)
    // Line-chart wheel zoom; positive delta zooms in 折线图滚轮缩放，正增量表示放大
    // anchorRatio is the pointer position in the chart 鼠标锚点在图表中的相对位置
    signal wheelZoomed(int delta, real anchorRatio)
    // Emitted by wheel, panning, or slider changes 由滚轮、平移或滑块变化触发
    signal viewportChanged(real start, real end)

    // Return a length-bearing list for QVariantList and JavaScript arrays 返回带 length 的列表，兼容 QVariantList 与 JavaScript 数组
    function _listOrEmpty(value) {
        return value && typeof value.length === "number" ? value : []
    }

    function _normalizeChartData(value) {
        var source = _listOrEmpty(value)
        var normalized = []
        for (var i = 0; i < source.length; i++) {
            var item = source[i]
            normalized.push(item && typeof item === "object" && !Array.isArray(item)
                            ? item : { label: "", value: 0 })
        }
        return normalized
    }

    function _normalizeIndicators(value) {
        var source = _listOrEmpty(value)
        var normalized = []
        for (var i = 0; i < source.length; i++) {
            var item = source[i]
            normalized.push(item && typeof item === "object" && !Array.isArray(item)
                            ? item : { name: "", max: 100 })
        }
        return normalized
    }

    function _normalizeSeries(value) {
        var source = _listOrEmpty(value)
        var normalized = []
        for (var i = 0; i < source.length; i++) {
            var item = source[i]
            normalized.push(item && typeof item === "object" && !Array.isArray(item)
                            ? item : {})
        }
        return normalized
    }

    function _hasRenderableSeries(items, field) {
        for (var i = 0; i < items.length; i++) {
            var item = items[i]
            if (!item) continue
            if (_listOrEmpty(item[field]).length > 0) return true
        }
        return false
    }

    function _validBoxplotData(items) {
        items = _listOrEmpty(items)
        var valid = []
        for (var i = 0; i < items.length; i++) {
            var item = items[i]
            if (!item) continue
            var fields = [item.min, item.q1, item.median, item.q3, item.max]
            var complete = true
            for (var j = 0; j < fields.length; j++) {
                if (typeof fields[j] !== "number" || !isFinite(fields[j])) {
                    complete = false
                    break
                }
            }
            if (complete) valid.push(item)
        }
        return valid
    }

    function getColor(index) {
        if (_chartData[index] && _chartData[index].color) return _chartData[index].color
        return defaultColors[index % defaultColors.length]
    }
    function formatValue(value) {
        if (valueFormatter && typeof valueFormatter === "function") return valueFormatter(value)
        if (typeof value === "number") return value.toLocaleString()
        return value
    }
    function toggleSeriesVisibility(seriesIndex) {
        var hidden = _hiddenSeriesIndices.slice()
        var idx = hidden.indexOf(seriesIndex)
        if (idx >= 0) hidden.splice(idx, 1)
        else hidden.push(seriesIndex)
        _hiddenSeriesIndices = hidden
    }
    function isSeriesVisible(seriesIndex) {
        return _hiddenSeriesIndices.indexOf(seriesIndex) < 0
    }
    implicitWidth: preferredWidth > 0 ? preferredWidth : contentWidth
    implicitHeight: preferredHeight > 0 ? preferredHeight : contentHeight
    color: Enums.cardColor
    radius: Enums.surfaceRadius(Enums.radius.large)
    border.width: Enums.surfaceBorderWidth(Enums.border.thin)
    border.color: Enums.stateColor.border
    shadowLevel: Enums.shadow.level2

    // Skip entrance animation in deferred mode 延迟模式跳过入场动画
    opacity: deferAnimation ? 1.0 : 0
    scale: 1.0

    Component.onCompleted: {
        if (!deferAnimation) {
            entranceAnim.start()
        }
    }
    // Apply pointer-anchored wheel zoom and retarget running transitions 应用鼠标锚定滚轮缩放并重定向进行中的过渡
    onWheelZoomed: function(delta, anchorRatio) {
        var span = control._visualEnd - control._visualStart
        if (span <= 0) span = 1
        var zoomFactor = delta > 0 ? Enums.chart.zoom_in_factor : Enums.chart.zoom_out_factor
        var newSpan = span * zoomFactor
        if (newSpan < Enums.chart.minimum_viewport_span) {
            newSpan = Enums.chart.minimum_viewport_span
        }
        if (newSpan > 1) newSpan = 1
        var anchor = control._visualStart + span * anchorRatio
        var nextStart = anchor - newSpan * anchorRatio
        var nextEnd = nextStart + newSpan
        if (nextStart < 0) {
            nextStart = 0
            nextEnd = newSpan
        }
        if (nextEnd > 1) {
            nextEnd = 1
            nextStart = 1 - newSpan
        }
        control.viewportStart = nextStart
        control.viewportEnd = nextEnd
        control.viewportChanged(nextStart, nextEnd)
    }
    ChartViewportAnimator {
        id: viewportAnimator
        viewportStart: control.viewportStart
        viewportEnd: control.viewportEnd
        animated: control.animated
        interactive: control._viewportInteractive
        transitionEnabled: control._isXYChart
        onTransitionStarted: {
            control._hoveredBarIndex = -1
            control._hoveredBarSeriesIndex = -1
            control._hoveredPointIndex = -1
            control._hoveredLineSeriesIndex = -1
            control._hoveredScatterSeriesIndex = -1
            control._hoveredScatterPointIndex = -1
        }
    }
    SequentialAnimation {
        id: entranceAnim
        PauseAnimation { duration: Enums.duration.instant }
        ParallelAnimation {
            NumberAnimation { target: control; property: "opacity"; to: 1.0; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
            NumberAnimation { target: control; property: "scale"; to: 1.0; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        }
    }
    // ==================== Content 内容 ====================
    ChartRenderLayer {
        id: renderLayer
        anchors.fill: parent
        chartControl: control
    }
}
