// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "_internal"
import "_internal/lttb.js" as Lttb
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

    // ==================== DataZoom Viewport 视窗 ====================
    // 视窗范围 0..1 (相对于 chartData/series 的总长). 默认全量 [0, 1] 不影响老调用方.
    // 三种交互入口 (滚轮 / 主图拖动 / dataZoom slider) 都通过 viewportChanged 同步.
    property real viewportStart: 0
    property real viewportEnd: 1
    // 是否在主图下方显示 dataZoom slider (双手柄 + 缩略图)
    property bool dataZoomEnabled: false
    // 是否启用主图鼠标按住拖动平移 (dataZoom 启用时建议保持 true)
    property bool panEnabled: true
    // 拖动期间标志位 — 由 MouseArea/ChartDataZoom 设置, 用来关掉 viewport 动画
    property bool _viewportInteractive: false

    // ==================== Render Viewport 节流 (内部) ====================
    // _renderStart/End 是实际驱动 _viewChartData/_viewSeries 重算的"画面值",
    // 由 _renderTimer 50ms 节流跟上 viewportStart/End. 避免每帧切片+LTTB+重画卡顿.
    // viewport 动画 120ms 内 timer 反复 restart, 最后只触发 1-2 次重画.
    property real _renderStart: 0
    property real _renderEnd: 1

    // ==================== Readonly Props 只读属性 ====================
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

    // ==================== Size & Style 尺寸和样式 ====================
    // Size priority (manual, ShadowedRectangle can't extend Widget) 尺寸优先级（手动实现，ShadowedRectangle 无法继承 Widget）
    property real preferredWidth: 0
    property real preferredHeight: 0
    property real contentWidth: Enums.controlSize.chartDefaultWidth
    property real contentHeight: Enums.controlSize.chartDefaultHeight

    // Chart card entrance animation 图表卡片入场动画
    property bool deferAnimation: false  // Set true for lazy-loaded charts 懒加载图表设为true

    // ==================== Internal Props 内部属性 ====================
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

    // ==================== Viewport 切片 + LTTB 降采样 (内部) ====================
    // 1) 把 chartData / series 按 [viewportStart, viewportEnd] 切片
    // 2) 切片后点数 > _lttbThreshold 时走 LTTB 抽稀, 保留趋势/峰谷
    // 默认 [0, 1] + 点数小时 == 全量, 行为和原 ChartView 完全一致.
    property int lttbThreshold: 600
    readonly property var _viewChartData: {
        if (!chartData || chartData.length === 0) return []
        var src = chartData
        if (_renderStart > 0 || _renderEnd < 1) {
            var n = chartData.length
            var lo = Math.max(0, Math.floor(n * _renderStart))
            var hi = Math.min(n, Math.ceil(n * _renderEnd))
            if (hi <= lo) hi = Math.min(n, lo + 1)
            src = chartData.slice(lo, hi)
        }
        if (src.length <= lttbThreshold) return src
        // LTTB 降采样: value 字段当主导, 索引同步
        var indices = Lttb.lttbIndices(_indexArray(src.length), _valuesOf(src), lttbThreshold)
        var out = new Array(indices.length)
        for (var i = 0; i < indices.length; i++) out[i] = src[indices[i]]
        return out
    }
    readonly property var _viewSeries: {
        if (!series || series.length === 0) return []
        var srcAll = series
        var hadViewport = _renderStart > 0 || _renderEnd < 1
        if (hadViewport) {
            var sliced = []
            for (var s = 0; s < series.length; s++) {
                var src = series[s] || {}
                var copy = {}
                for (var k in src) copy[k] = src[k]
                if (Array.isArray(src.values)) {
                    var n = src.values.length
                    var lo = Math.max(0, Math.floor(n * _renderStart))
                    var hi = Math.min(n, Math.ceil(n * _renderEnd))
                    if (hi <= lo) hi = Math.min(n, lo + 1)
                    copy.values = src.values.slice(lo, hi)
                }
                if (Array.isArray(src.data)) {
                    var n2 = src.data.length
                    var lo2 = Math.max(0, Math.floor(n2 * _renderStart))
                    var hi2 = Math.min(n2, Math.ceil(n2 * _renderEnd))
                    if (hi2 <= lo2) hi2 = Math.min(n2, lo2 + 1)
                    copy.data = src.data.slice(lo2, hi2)
                }
                sliced.push(copy)
            }
            srcAll = sliced
        }
        var maxLen = 0
        for (var s2 = 0; s2 < srcAll.length; s2++) {
            var v2 = srcAll[s2].values || srcAll[s2].data || []
            if (v2.length > maxLen) maxLen = v2.length
        }
        if (maxLen <= lttbThreshold) return srcAll
        // 多 series 用第一条 values 作主导算 indices, 其它 series 同 indices 切
        var primary = srcAll[0].values || srcAll[0].data || []
        if (primary.length <= lttbThreshold) return srcAll
        var primIdx = Lttb.lttbIndices(_indexArray(primary.length), _numbersOf(primary), lttbThreshold)
        var out2 = []
        for (var s3 = 0; s3 < srcAll.length; s3++) {
            var c = {}
            for (var k2 in srcAll[s3]) c[k2] = srcAll[s3][k2]
            if (Array.isArray(srcAll[s3].values)) {
                c.values = primIdx.map(function(i) { return srcAll[s3].values[i] })
            }
            if (Array.isArray(srcAll[s3].data)) {
                c.data = primIdx.map(function(i) { return srcAll[s3].data[i] })
            }
            out2.push(c)
        }
        return out2
    }

    // ==================== Signals 信号 ====================
    signal barClicked(int index, var data)
    signal pointClicked(int index, var data)
    signal sliceClicked(int index, var data)
    signal boxClicked(int index, var data)
    // 折线图鼠标滚轮缩放: delta > 0 放大 (zoom in), < 0 缩小;
    // anchorRatio: 鼠标在 chart 内 0..1 (用于以鼠标位置为锚)
    signal wheelZoomed(int delta, real anchorRatio)
    // 视窗变化 (滚轮/拖动/slider 三方任意一种) - 使用方监听后向 backend 重拉数据
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

    function _indexArray(n) {
        var a = new Array(n)
        for (var i = 0; i < n; i++) a[i] = i
        return a
    }
    function _valuesOf(arr) {
        var a = new Array(arr.length)
        for (var i = 0; i < arr.length; i++) {
            var it = arr[i]
            a[i] = (it && it.value !== undefined) ? it.value : 0
        }
        return a
    }
    function _numbersOf(vals) {
        var a = new Array(vals.length)
        for (var i = 0; i < vals.length; i++) {
            a[i] = (typeof vals[i] === 'number') ? vals[i] : 0
        }
        return a
    }

    implicitWidth: preferredWidth > 0 ? preferredWidth : contentWidth
    implicitHeight: preferredHeight > 0 ? preferredHeight : contentHeight
    color: Enums.cardColor
    radius: Enums.radius.large
    border.width: Enums.border.thin
    border.color: Enums.stateColor.border
    shadowLevel: Enums.shadow.level2

    // Skip entrance animation in deferred mode 延迟模式跳过入场动画
    opacity: deferAnimation ? 1.0 : 0
    scale: 1.0

    // viewport 平滑过渡 (滚轮缩放等"一次性"操作时启用):
    // 100ms 内 slider 手柄 / dataZoom 缩略图 binding 跟着滑动, 视觉有动画.
    // 拖动期间 _viewportInteractive=true 关掉, 跟随用户实时.
    Behavior on viewportStart {
        enabled: !_viewportInteractive
        NumberAnimation { duration: 120; easing.type: Easing.OutCubic }
    }
    Behavior on viewportEnd {
        enabled: !_viewportInteractive
        NumberAnimation { duration: 120; easing.type: Easing.OutCubic }
    }

    Timer {
        id: _renderTimer
        interval: 50
        repeat: false
        onTriggered: {
            control._renderStart = control.viewportStart
            control._renderEnd = control.viewportEnd
        }
    }
    onViewportStartChanged: _renderTimer.restart()
    onViewportEndChanged: _renderTimer.restart()

    Component.onCompleted: {
        if (!deferAnimation) {
            entranceAnim.start()
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

    // ==================== 滚轮缩放 → viewport 内部处理 ====================
    // ChartView 内部接 wheelZoomed signal, 自己改 viewportStart/End.
    // 老调用方仍然能监听 wheelZoomed (兼容), 双重触发不影响.
    onWheelZoomed: function(delta, anchorRatio) {
        var span = control.viewportEnd - control.viewportStart
        if (span <= 0) span = 1
        var zoomFactor = delta > 0 ? 0.7 : 1.4
        var newSpan = span * zoomFactor
        if (newSpan < 0.001) newSpan = 0.001  // 最小 0.1% 范围
        if (newSpan > 1) newSpan = 1
        // 锚点对应数据位置 = viewportStart + span * anchorRatio
        var anchor = control.viewportStart + span * anchorRatio
        var ns = anchor - newSpan * anchorRatio
        var ne = ns + newSpan
        if (ns < 0) { ns = 0; ne = newSpan }
        if (ne > 1) { ne = 1; ns = 1 - newSpan }
        control.viewportStart = ns
        control.viewportEnd = ne
        control.viewportChanged(ns, ne)
    }

    // ==================== XY Chart (Bar/Line/Scatter) ====================
    XYChartCore {
        id: xyChartBase
        // dataZoomEnabled=true 时给底部 ChartDataZoom 留 60px 空间
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

        onXLabelHovered: (index) => {
            if (control.chartType === Enums.chart.type_bar) control._hoveredBarIndex = index
            else control._hoveredPointIndex = index
        }

        BarChartContent {
            id: barContent
            anchors.fill: xyChartBase.chartArea
            visible: control.chartType === Enums.chart.type_bar && (control.chartData.length > 0 || control.series.length > 0)
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

        LineChartContent {
            id: lineContent
            anchors.fill: xyChartBase.chartArea
            visible: control.chartType === Enums.chart.type_line && (control.chartData.length > 0 || control.series.length > 0)
            chartData: control._viewChartData
            series: control._viewSeries
            maxValue: control.maxValue
            primaryColor: control.primaryColor
            smoothLine: control.smoothLine
            hoverDetectEnabled: control.showTooltip
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

        ScatterChartContent {
            id: scatterContent
            anchors.fill: xyChartBase.chartArea
            visible: control._isScatter && control.series.length > 0
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

    // ==================== XY Chart Tooltips ====================
    // Single series bar chart tooltip 单系列柱状图 Tooltip
    ChartTooltip {
        visible: control._hoveredBarIndex >= 0 && barContent.visible && !barContent.isMultiSeries
        x: {
            if (control._hoveredBarIndex < 0 || control.chartData.length === 0) return 0
            var barWidth = (xyChartBase.chartAreaWidth - control.chartData.length * Enums.spacing.s) / control.chartData.length
            return xyChartBase.chartAreaX + control._hoveredBarIndex * (barWidth + Enums.spacing.s) + barWidth / 2 - width / 2
        }
        y: xyChartBase.chartAreaY + Enums.spacing.m
        label: control._hoveredBarIndex >= 0 && control._hoveredBarIndex < control.chartData.length ? (control.chartData[control._hoveredBarIndex].label || "") : ""
        value: control._hoveredBarIndex >= 0 && control._hoveredBarIndex < control.chartData.length ? (control.chartData[control._hoveredBarIndex].value || 0) : 0
        valueFormatter: control.valueFormatter
    }

    // Single series line chart tooltip 单系列折线图 Tooltip
    ChartTooltip {
        visible: control._hoveredPointIndex >= 0 && lineContent.visible && !lineContent.isMultiSeries
        x: xyChartBase.chartAreaX + lineContent.getTooltipPosition(control._hoveredPointIndex).x - width / 2
        y: xyChartBase.chartAreaY + lineContent.getTooltipPosition(control._hoveredPointIndex).y - height - Enums.spacing.m
        label: control._hoveredPointIndex >= 0 && control._hoveredPointIndex < control.chartData.length ? (control.chartData[control._hoveredPointIndex].label || "") : ""
        value: control._hoveredPointIndex >= 0 && control._hoveredPointIndex < control.chartData.length ? (control.chartData[control._hoveredPointIndex].value || 0) : 0
        valueFormatter: control.valueFormatter
    }

    ChartMultiTooltip {
        visible: control.showTooltip && control._hoveredPointIndex >= 0 && lineContent.visible && lineContent.isMultiSeries
        // 默认放鼠标右下角; 触右/下边时反向到左/上 (单轴独立判断)
        x: {
            var mx = lineContent.mouseX || 0
            var right = mx + Enums.spacing.m
            // 右侧放得下 → 右; 否则翻到左侧 (mx - width - spacing.s)
            if (right + width <= xyChartBase.chartAreaWidth) {
                return xyChartBase.chartAreaX + right
            }
            return xyChartBase.chartAreaX + Math.max(0, mx - width - Enums.spacing.s)
        }
        y: {
            var my = lineContent.mouseY || 0
            var below = my + Enums.spacing.m
            if (below + height <= xyChartBase.chartAreaHeight) {
                return xyChartBase.chartAreaY + below
            }
            return xyChartBase.chartAreaY + Math.max(0, my - height - Enums.spacing.s)
        }
        xLabel: control._hoveredPointIndex >= 0 && control.chartData.length > control._hoveredPointIndex ? (control.chartData[control._hoveredPointIndex].label || "") : ""
        seriesData: {
            var result = []
            for (var i = 0; i < control.series.length; i++) {
                var s = control.series[i]
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
            for (var i = 0; i < control.series.length; i++) {
                var vals = control.series[i].values || []
                if (control._hoveredPointIndex < vals.length) sum += vals[control._hoveredPointIndex] || 0
            }
            return sum
        }
        valueFormatter: control.valueFormatter
    }

    ChartMultiTooltip {
        visible: control._hoveredBarIndex >= 0 && barContent.visible && barContent.isMultiSeries
        x: xyChartBase.chartAreaX + Math.min(Math.max((control._hoveredBarIndex + 0.5) * (xyChartBase.chartAreaWidth / barContent.dataLength) - width / 2, 0), xyChartBase.chartAreaWidth - width)
        y: xyChartBase.chartAreaY + Enums.spacing.m
        xLabel: control._hoveredBarIndex >= 0 && control.chartData.length > control._hoveredBarIndex ? (control.chartData[control._hoveredBarIndex].label || "") : ""
        seriesData: {
            var result = []
            for (var i = 0; i < control.series.length; i++) {
                var s = control.series[i]
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
        visible: control._hoveredScatterSeriesIndex >= 0 && scatterContent.visible
        x: xyChartBase.chartAreaX + Math.min(Math.max(scatterContent.tooltipX - width / 2, 0), xyChartBase.chartAreaWidth - width)
        y: xyChartBase.chartAreaY + scatterContent.tooltipY - height - Enums.spacing.m
        showColorDot: true
        dotColor: control._hoveredScatterSeriesIndex >= 0 ? (control.series[control._hoveredScatterSeriesIndex].color || Enums.chartColors.extendedPalette[control._hoveredScatterSeriesIndex % Enums.chartColors.extendedPalette.length]) : "transparent"
        label: control._hoveredScatterSeriesIndex >= 0 ? (control.series[control._hoveredScatterSeriesIndex].name || "") : ""
        value: "(" + scatterContent.dataX.toFixed(2) + ", " + scatterContent.dataY.toFixed(2) + ")"
        isValueString: true
    }

    // ==================== XY Chart Legends ====================
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

    // ==================== Pie Chart ====================
    PieChartArea {
        anchors.fill: parent
        visible: control._isPie
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

    // ==================== Radar Chart ====================
    RadarChartArea {
        anchors.fill: parent
        visible: control._isRadar
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

    // ==================== Boxplot Chart ====================
    BoxplotChartArea {
        anchors.fill: parent
        visible: control._isBoxplot
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

    // ==================== DataZoom 底部 slider ====================
    ChartDataZoom {
        id: dataZoomBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: Enums.spacing.m
        anchors.rightMargin: Enums.spacing.m
        anchors.bottomMargin: Enums.spacing.s
        height: 50
        visible: control.dataZoomEnabled && control._isXYChart
        chartData: control.chartData
        series: control.series
        primaryColor: control.primaryColor
        viewportStart: control.viewportStart
        viewportEnd: control.viewportEnd
        onViewportChanged: (s, e) => {
            control.viewportStart = s
            control.viewportEnd = e
            control.viewportChanged(s, e)
        }
        onInteractiveChanged: (active) => {
            control._viewportInteractive = active
        }
    }

    // ==================== 主图拖动平移 MouseArea ====================
    // 按住左键拖动 → viewport 平移. 走 z=-1 让 ChartView 内部 hover/tooltip
    // 优先, 这里只接 press/release 不抢 hover.
    MouseArea {
        anchors.fill: xyChartBase
        z: -1
        enabled: control.panEnabled && control._isXYChart
        acceptedButtons: Qt.LeftButton
        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        propagateComposedEvents: true
        property real _pressX: 0
        property real _pressVS: 0
        property real _pressVE: 0
        onPressed: (mouse) => {
            _pressX = mouse.x
            _pressVS = control.viewportStart
            _pressVE = control.viewportEnd
            control._viewportInteractive = true
        }
        onReleased: { control._viewportInteractive = false }
        onCanceled: { control._viewportInteractive = false }
        onPositionChanged: (mouse) => {
            if (!pressed || width <= 0) return
            var dx = mouse.x - _pressX
            // 拖动 dx 像素 → viewport 反向移动 dx/width * span
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

    // ==================== Empty State 空状态 ====================
    Column {
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
