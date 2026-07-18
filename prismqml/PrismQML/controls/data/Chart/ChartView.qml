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
    // Y-axis label area width (px) Y 轴标签区宽度;长字符串场景 (多级货币等) 可手动加大
    property real yAxisLabelWidth: Enums.controlSize.chartYAxisWidth
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
        for (var i = 0; i < chartData.length; i++) {
            if (chartData[i] && chartData[i].value > max) max = chartData[i].value
        }
        return max || 1
    }
    readonly property real totalValue: {
        var sum = 0
        for (var i = 0; i < chartData.length; i++) {
            if (chartData[i]) sum += chartData[i].value || 0
        }
        return sum || 1
    }
    readonly property var defaultColors: Enums.chartColors.palette

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
    readonly property var _barContent: barContentLoader.item
    readonly property var _lineContent: lineContentLoader.item
    readonly property var _scatterContent: scatterContentLoader.item

    // Slice the viewport before LTTB sampling to preserve trends and extrema 先按视窗切片，再用 LTTB 保留趋势与峰谷
    readonly property var _viewChartData: ChartViewport.viewChartData(
        chartData, _renderViewport.start, _renderViewport.end, lttbThreshold
    )
    readonly property var _viewSeries: ChartViewport.viewSeries(
        series, _renderViewport.start, _renderViewport.end, lttbThreshold
    )

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

    function getColor(index) {
        if (chartData[index] && chartData[index].color) return chartData[index].color
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
    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.large
    border.width: Enums.border.thin
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
    XYChartCore {
        id: xyChartBase
        // Reserve space for the data zoom bar 为底部数据缩放条预留空间
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: control.dataZoomEnabled && control._isXYChart ? dataZoomBar.top : parent.bottom
        anchors.bottomMargin: control.dataZoomEnabled && control._isXYChart ? Enums.spacing.s : 0
        visible: control._isXYChart

        chartData: control._viewChartData
        maxValue: control.maxValue
        showLabels: control.showLabels
        showValues: control.showValues
        showGrid: control.showGrid
        showLegend: control.showLegend
        title: control.title
        subtitle: control.subtitle
        series: control._viewSeries
        isScatter: control._isScatter
        isHorizontal: control._isHorizontalBar
        yAxisSuffix: control.yAxisSuffix
        yAxisLabelWidth: control.yAxisLabelWidth
        valueFormatter: control.valueFormatter
        hoveredIndex: control._isScatter ? -1 : (control._hoveredBarIndex >= 0 ? control._hoveredBarIndex : control._hoveredPointIndex)
        viewportScale: control._viewportScale
        viewportOffsetRatio: control._viewportOffsetRatio
        viewportTransitionActive: control._viewportTransitionActive

        onXLabelHovered: (index) => {
            if (control.chartType === Enums.chart.type_bar) control._hoveredBarIndex = index
            else control._hoveredPointIndex = index
        }

        Item {
            id: chartViewportClip
            anchors.fill: xyChartBase.chartArea
            clip: true

            Item {
                id: chartViewportLayer
                x: control._isHorizontalBar ? 0 : control._viewportOffsetRatio * parent.width
                y: control._isHorizontalBar ? control._viewportOffsetRatio * parent.height : 0
                width: parent.width
                height: parent.height
                transform: Scale {
                    origin.x: 0
                    origin.y: 0
                    xScale: control._isHorizontalBar ? 1 : control._viewportScale
                    yScale: control._isHorizontalBar ? control._viewportScale : 1
                }

                Loader {
                    id: barContentLoader
                    objectName: "barContentLoader"
                    anchors.fill: parent
                    active: control.chartType === Enums.chart.type_bar &&
                            (control.chartData.length > 0 || control.series.length > 0)
                    sourceComponent: Component {
                        BarChartContent {
                            chartData: control._viewChartData
                            series: control._viewSeries
                            maxValue: control.maxValue
                            animated: control.animated
                            showValues: control.showValues
                            showAverage: control.showAverage
                            showMinMax: control.showMinMax
                            showBarGradient: control.showBarGradient
                            getColor: control.getColor
                            hoveredIndex: control._hoveredBarIndex
                            hoveredSeriesIndex: control._hoveredBarSeriesIndex
                            isHorizontal: control._isHorizontalBar
                            valueRange: xyChartBase.valueRange
                            zeroLineRatio: xyChartBase.zeroLineRatio
                            onBarClicked: (index, data) => control.barClicked(index, data)
                            onBarHovered: (index) => control._hoveredBarIndex = index
                            onSeriesBarHovered: (si, bi) => { control._hoveredBarSeriesIndex = si; control._hoveredBarIndex = bi }
                        }
                    }
                }

                Loader {
                    id: lineContentLoader
                    objectName: "lineContentLoader"
                    anchors.fill: parent
                    active: control.chartType === Enums.chart.type_line &&
                            (control.chartData.length > 0 || control.series.length > 0)
                    sourceComponent: Component {
                        LineChartContent {
                            chartData: control._viewChartData
                            series: control._viewSeries
                            maxValue: control.maxValue
                            primaryColor: control.primaryColor
                            smoothLine: control.smoothLine
                            animated: control.animated
                            hoverDetectEnabled: control.showTooltip && !control._viewportTransitionActive
                            showAverage: control.showAverage
                            showMinMax: control.showMinMax
                            isArea: false
                            hoveredIndex: control._hoveredPointIndex
                            hoveredSeriesIndex: control._hoveredLineSeriesIndex
                            boundaryGap: control.boundaryGap
                            showAreaGradient: control.showAreaGradient
                            stacked: control.stacked
                            onPointClicked: (index, data) => control.pointClicked(index, data)
                            onPointHovered: (index) => control._hoveredPointIndex = index
                            onSeriesPointHovered: (si, pi) => { control._hoveredLineSeriesIndex = si; control._hoveredPointIndex = pi }
                            onWheelZoomed: (delta, anchorRatio) => control.wheelZoomed(delta, anchorRatio)
                        }
                    }
                }

                Loader {
                    id: scatterContentLoader
                    objectName: "scatterContentLoader"
                    anchors.fill: parent
                    active: control._isScatter && control.series.length > 0
                    sourceComponent: Component {
                        ScatterChartContent {
                            series: control._viewSeries
                            dataRange: xyChartBase.scatterDataRange
                            animated: control.animated
                            showGrid: control.showGrid
                            hoveredSeriesIndex: control._hoveredScatterSeriesIndex
                            hoveredPointIndex: control._hoveredScatterPointIndex
                            defaultSymbolSize: control.symbolSize
                            onPointClicked: (index, data) => control.pointClicked(index, data)
                            onPointHovered: (si, pi) => { control._hoveredScatterSeriesIndex = si; control._hoveredScatterPointIndex = pi }
                        }
                    }
                }
            }
        }
    }

    // XY chart tooltips XY 图表提示框
    // Single series bar chart tooltip 单系列柱状图 Tooltip
    ChartTooltip {
        visible: !control._viewportTransitionActive && control._hoveredBarIndex >= 0 &&
                 control._barContent !== null && !control._barContent.isMultiSeries
        x: {
            if (control._hoveredBarIndex < 0 || control._viewChartData.length === 0) return 0
            var barWidth = (xyChartBase.chartAreaWidth - control._viewChartData.length * Enums.spacing.s) / control._viewChartData.length
            return xyChartBase.chartAreaX + control._hoveredBarIndex * (barWidth + Enums.spacing.s) + barWidth / 2 - width / 2
        }
        y: xyChartBase.chartAreaY + Enums.spacing.m
        label: control._hoveredBarIndex >= 0 && control._hoveredBarIndex < control._viewChartData.length ? (control._viewChartData[control._hoveredBarIndex].label || "") : ""
        value: control._hoveredBarIndex >= 0 && control._hoveredBarIndex < control._viewChartData.length ? (control._viewChartData[control._hoveredBarIndex].value || 0) : 0
        valueFormatter: control.valueFormatter
    }

    // Single series line chart tooltip 单系列折线图 Tooltip
    ChartTooltip {
        visible: !control._viewportTransitionActive && control._hoveredPointIndex >= 0 &&
                 control._lineContent !== null && !control._lineContent.isMultiSeries
        x: xyChartBase.chartAreaX + (control._lineContent ? control._lineContent.getTooltipPosition(control._hoveredPointIndex).x : 0) - width / 2
        y: xyChartBase.chartAreaY + (control._lineContent ? control._lineContent.getTooltipPosition(control._hoveredPointIndex).y : 0) - height - Enums.spacing.m
        label: control._hoveredPointIndex >= 0 && control._hoveredPointIndex < control._viewChartData.length ? (control._viewChartData[control._hoveredPointIndex].label || "") : ""
        value: control._hoveredPointIndex >= 0 && control._hoveredPointIndex < control._viewChartData.length ? (control._viewChartData[control._hoveredPointIndex].value || 0) : 0
        valueFormatter: control.valueFormatter
    }

    ChartMultiTooltip {
        visible: !control._viewportTransitionActive && control.showTooltip && control._hoveredPointIndex >= 0 &&
                 control._lineContent !== null && control._lineContent.isMultiSeries
        // 默认放鼠标右下角; 触右/下边时反向到左/上 (单轴独立判断)
        x: {
            var mx = control._lineContent ? control._lineContent.mouseX : 0
            var right = mx + Enums.spacing.m
            // 右侧放得下 → 右; 否则翻到左侧 (mx - width - spacing.s)
            if (right + width <= xyChartBase.chartAreaWidth) {
                return xyChartBase.chartAreaX + right
            }
            return xyChartBase.chartAreaX + Math.max(0, mx - width - Enums.spacing.s)
        }
        y: {
            var my = control._lineContent ? control._lineContent.mouseY : 0
            var below = my + Enums.spacing.m
            if (below + height <= xyChartBase.chartAreaHeight) {
                return xyChartBase.chartAreaY + below
            }
            return xyChartBase.chartAreaY + Math.max(0, my - height - Enums.spacing.s)
        }
        xLabel: control._hoveredPointIndex >= 0 && control._viewChartData.length > control._hoveredPointIndex ? (control._viewChartData[control._hoveredPointIndex].label || "") : ""
        seriesData: {
            var result = []
            for (var i = 0; i < control._viewSeries.length; i++) {
                var s = control._viewSeries[i]
                var vals = s.values || []
                result.push({
                    name: s.name || "",
                    value: control._hoveredPointIndex >= 0 && control._hoveredPointIndex < vals.length ? vals[control._hoveredPointIndex] : 0,
                    color: s.color || Enums.chartColors.extendedPalette[i % Enums.chartColors.extendedPalette.length]
                })
            }
            return result
        }
        showTotal: control.stacked
        totalValue: {
            if (control._hoveredPointIndex < 0) return 0
            var sum = 0
            for (var i = 0; i < control._viewSeries.length; i++) {
                var vals = control._viewSeries[i].values || []
                if (control._hoveredPointIndex < vals.length) sum += vals[control._hoveredPointIndex] || 0
            }
            return sum
        }
        valueFormatter: control.valueFormatter
    }

    ChartMultiTooltip {
        visible: !control._viewportTransitionActive && control._hoveredBarIndex >= 0 &&
                 control._barContent !== null && control._barContent.isMultiSeries
        x: {
            var dataLength = control._barContent ? control._barContent.dataLength : 0
            if (dataLength <= 0) return xyChartBase.chartAreaX
            return xyChartBase.chartAreaX + Math.min(Math.max((control._hoveredBarIndex + 0.5) * (xyChartBase.chartAreaWidth / dataLength) - width / 2, 0), xyChartBase.chartAreaWidth - width)
        }
        y: xyChartBase.chartAreaY + Enums.spacing.m
        xLabel: control._hoveredBarIndex >= 0 && control._viewChartData.length > control._hoveredBarIndex ? (control._viewChartData[control._hoveredBarIndex].label || "") : ""
        seriesData: {
            var result = []
            for (var i = 0; i < control._viewSeries.length; i++) {
                var s = control._viewSeries[i]
                var vals = s.values || []
                result.push({
                    name: s.name || "",
                    value: control._hoveredBarIndex >= 0 && control._hoveredBarIndex < vals.length ? vals[control._hoveredBarIndex] : 0,
                    color: s.color || Enums.chartColors.extendedPalette[i % Enums.chartColors.extendedPalette.length]
                })
            }
            return result
        }
        valueFormatter: control.valueFormatter
    }

    ChartTooltip {
        visible: !control._viewportTransitionActive && control._hoveredScatterSeriesIndex >= 0 &&
                 control._scatterContent !== null
        x: xyChartBase.chartAreaX + Math.min(Math.max((control._scatterContent ? control._scatterContent.tooltipX : 0) - width / 2, 0), xyChartBase.chartAreaWidth - width)
        y: xyChartBase.chartAreaY + (control._scatterContent ? control._scatterContent.tooltipY : 0) - height - Enums.spacing.m
        showColorDot: true
        dotColor: control._hoveredScatterSeriesIndex >= 0 ? (control._viewSeries[control._hoveredScatterSeriesIndex].color || Enums.chartColors.extendedPalette[control._hoveredScatterSeriesIndex % Enums.chartColors.extendedPalette.length]) : Enums.transparent
        label: control._hoveredScatterSeriesIndex >= 0 ? (control._viewSeries[control._hoveredScatterSeriesIndex].name || "") : ""
        value: control._scatterContent
               ? "(" + control._scatterContent.dataX.toFixed(2) + ", " + control._scatterContent.dataY.toFixed(2) + ")"
               : ""
        isValueString: true
    }

    // XY chart legends XY 图表图例
    ChartBottomLegend {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.m
        visible: control.chartType === Enums.chart.type_line && control.showLegend && control.series.length > 0
        legendData: control.series
        legendStyle: "line"
        hoveredIndex: control._hoveredLineSeriesIndex
        hiddenIndices: control._hiddenSeriesIndices
        onItemHovered: (index) => control._hoveredLineSeriesIndex = index
        onItemClicked: (index) => control.toggleSeriesVisibility(index)
    }

    ChartBottomLegend {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.m
        visible: control.chartType === Enums.chart.type_bar && control.showLegend && control.series.length > 0
        legendData: control.series
        legendStyle: "bar"
        hoveredIndex: control._hoveredBarSeriesIndex
        hiddenIndices: control._hiddenSeriesIndices
        onItemHovered: (index) => control._hoveredBarSeriesIndex = index
        onItemClicked: (index) => control.toggleSeriesVisibility(index)
    }

    ChartBottomLegend {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.m
        visible: control._isScatter && control.showLegend && control.series.length > 0
        legendData: control.series
        legendStyle: "dot"
        hoveredIndex: control._hoveredScatterSeriesIndex
        clickable: false
        onItemHovered: (index) => control._hoveredScatterSeriesIndex = index
    }

    // Pie chart 饼图
    Loader {
        id: pieAreaLoader
        objectName: "pieAreaLoader"
        anchors.fill: parent
        active: control._isPie && control.chartData.length > 0
        sourceComponent: Component {
            PieChartArea {
                chartData: control.chartData
                totalValue: control.totalValue
                animated: control.animated
                showValues: control.showValues
                showLegend: control.showLegend
                getColor: control.getColor
                title: control.title
                subtitle: control.subtitle
                isDonut: control.isDonut
                donutRatio: control.donutRatio
                donutCenterText: control.donutCenterText
                donutCenterSubtext: control.donutCenterSubtext
                emphasisCenter: control.emphasisCenter
                labelOutside: control.labelOutside
                hoveredIndex: control._hoveredSliceIndex
                onSliceClicked: (index, data) => control.sliceClicked(index, data)
                onSliceHovered: (index) => control._hoveredSliceIndex = index
            }
        }
    }

    // Radar chart 雷达图
    Loader {
        id: radarAreaLoader
        objectName: "radarAreaLoader"
        anchors.fill: parent
        active: control._isRadar && control.indicators.length > 2
        sourceComponent: Component {
            RadarChartArea {
                indicators: control.indicators
                series: control.series
                animated: control.animated
                showLabels: control.showLabels
                showLegend: control.showLegend
                rings: control.rings
                title: control.title
                subtitle: control.subtitle
                hoveredSeriesIndex: control._hoveredRadarSeriesIndex
                hoveredPointIndex: control._hoveredRadarPointIndex
                hiddenSeriesIndices: control._hiddenSeriesIndices
                onPointClicked: (index, data) => control.pointClicked(index, data)
                onPointHovered: (si, pi) => { control._hoveredRadarSeriesIndex = si; control._hoveredRadarPointIndex = pi }
                onLegendClicked: (index) => control.toggleSeriesVisibility(index)
            }
        }
    }

    // Boxplot chart 箱线图
    Loader {
        id: boxplotAreaLoader
        objectName: "boxplotAreaLoader"
        anchors.fill: parent
        active: control._isBoxplot && control.boxplotData.length > 0
        sourceComponent: Component {
            BoxplotChartArea {
                boxplotData: control.boxplotData
                animated: control.animated
                showValues: control.showValues
                showGrid: control.showGrid
                isHorizontal: control.barOrientation === Enums.chart.orientation_horizontal
                title: control.title
                subtitle: control.subtitle
                hoveredIndex: control._hoveredBoxplotIndex
                onBoxClicked: (index, data) => control.boxClicked(index, data)
                onBoxHovered: (index) => control._hoveredBoxplotIndex = index
            }
        }
    }

    // Bottom data zoom slider 底部数据缩放滑块
    ChartDataZoom {
        id: dataZoomBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: Enums.spacing.m
        anchors.rightMargin: Enums.spacing.m
        anchors.bottomMargin: Enums.spacing.s
        height: Enums.controlSize.chartDataZoomBarHeight
        visible: control.dataZoomEnabled && control._isXYChart
        chartData: control.chartData
        series: control.series
        primaryColor: control.primaryColor
        viewportStart: control._visualStart
        viewportEnd: control._visualEnd
        onViewportChanged: (s, e) => {
            control.viewportStart = s
            control.viewportEnd = e
            control.viewportChanged(s, e)
        }
        onInteractiveChanged: (active) => {
            control._viewportInteractive = active
        }
    }

    // Chart panning interaction 主图拖动平移交互
    // Keep chart hover and tooltips above this pointer area 图表悬停与提示层保持更高优先级
    MouseArea {
        property real _pressX: 0
        property real _pressVS: 0
        property real _pressVE: 0

        anchors.fill: xyChartBase
        z: -1
        enabled: control.panEnabled && control._isXYChart
        acceptedButtons: Qt.LeftButton
        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        propagateComposedEvents: true
        onPressed: (mouse) => {
            _pressX = mouse.x
            _pressVS = control._visualStart
            _pressVE = control._visualEnd
            control._viewportInteractive = true
        }
        onReleased: { control._viewportInteractive = false }
        onCanceled: { control._viewportInteractive = false }
        onPositionChanged: (mouse) => {
            if (!pressed || width <= 0) return
            var dx = mouse.x - _pressX
            // Convert pointer movement to inverse viewport movement 将指针位移转换为反向视窗位移
            var span = _pressVE - _pressVS
            var deltaRatio = -dx / width * span
            var ns = _pressVS + deltaRatio
            var ne = _pressVE + deltaRatio
            if (ns < 0) { ns = 0; ne = span }
            if (ne > 1) { ne = 1; ns = 1 - span }
            control.viewportStart = ns
            control.viewportEnd = ne
            control.viewportChanged(ns, ne)
        }
    }

    // Empty state 空状态
    Column {
        id: emptyState
        anchors.centerIn: parent
        spacing: Enums.spacing.m
        visible: ((control._isXYChart && !control._isScatter && control.chartData.length === 0) ||
                 (control._isScatter && control.series.length === 0) ||
                 (control._isPie && control.chartData.length === 0) ||
                 (control._isRadar && control.indicators.length <= 2) ||
                 (control._isBoxplot && control.boxplotData.length === 0))
        opacity: visible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }

        Label {
            type: Enums.label.type_display
            anchors.horizontalCenter: parent.horizontalCenter
            text: "📊"
            font.pixelSize: Enums.typography.displayLarge
            color: Enums.textColor.tertiary
            SequentialAnimation on y {
                objectName: "emptyStateAnimation"
                running: emptyState.visible
                loops: Animation.Infinite
                NumberAnimation { from: 0; to: -4; duration: Enums.duration.emptyFloat; easing.type: Easing.InOutSine }
                NumberAnimation { from: -4; to: 0; duration: Enums.duration.emptyFloat; easing.type: Easing.InOutSine }
            }
        }

        Label {
            type: Enums.label.type_body
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.emptyText || "No data"
            color: Enums.textColor.tertiary
        }
    }
}
