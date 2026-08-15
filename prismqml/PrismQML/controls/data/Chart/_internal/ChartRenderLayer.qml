// ChartRenderLayer - Chart renderer orchestration 图表渲染编排层
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../../../.."

// Keeps the renderer branches and their visual stacking in one internal layer.
// 将渲染分支及其视觉堆叠顺序集中在内部层，入口组件只负责状态与生命周期。
Item {
    id: renderLayer

    required property var chartControl

    property alias xyChartBaseLoader: xyChartBaseLoader
    property alias barContentLoader: barContentLoader
    property alias lineContentLoader: lineContentLoader
    property alias scatterContentLoader: scatterContentLoader

    // ==================== Content 内容 ====================
    Loader {
        id: xyChartBaseLoader
        objectName: "xyChartBaseLoader"

        // Reserve space for the data zoom bar 为底部数据缩放条预留空间
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: chartControl.dataZoomEnabled && chartControl._isXYChart
                        ? dataZoomBar.top : parent.bottom
        anchors.bottomMargin: chartControl.dataZoomEnabled && chartControl._isXYChart
                              ? Enums.spacing.s : 0
        active: chartControl._isXYChart

        sourceComponent: Component {
            XYChartCore {
                chartData: chartControl._viewChartData
                maxValue: chartControl.maxValue
                showLabels: chartControl.showLabels
                showValues: chartControl.showValues
                showGrid: chartControl.showGrid
                showLegend: chartControl.showLegend
                title: chartControl.title
                subtitle: chartControl.subtitle
                series: chartControl._viewSeries
                isScatter: chartControl._isScatter
                isHorizontal: chartControl._isHorizontalBar
                yAxisSuffix: chartControl.yAxisSuffix
                yAxisLabelWidth: chartControl.yAxisLabelWidth
                valueFormatter: chartControl.valueFormatter
                hoveredIndex: chartControl._isScatter
                               ? -1
                               : (chartControl._hoveredBarIndex >= 0
                                  ? chartControl._hoveredBarIndex
                                  : chartControl._hoveredPointIndex)
                viewportScale: chartControl._viewportScale
                viewportOffsetRatio: chartControl._viewportOffsetRatio
                viewportTransitionActive: chartControl._viewportTransitionActive
                categoryProjection: chartControl._viewChartDataProjection
                viewportStart: chartControl._visualStart
                viewportEnd: chartControl._visualEnd
                animateValueRange: chartControl.chartType === Enums.chart.type_line
                                   && chartControl.animated

                onXLabelHovered: (index) => {
                    if (chartControl.chartType === Enums.chart.type_bar)
                        chartControl._hoveredBarIndex = index
                    else
                        chartControl._hoveredPointIndex = index
                }
            }
        }
    }

    Item {
        id: chartViewportClip
        x: chartControl._xyChartBase ? chartControl._xyChartBase.chartAreaX : 0
        y: chartControl._xyChartBase ? chartControl._xyChartBase.chartAreaY : 0
        width: chartControl._xyChartBase ? chartControl._xyChartBase.chartAreaWidth : 0
        height: chartControl._xyChartBase ? chartControl._xyChartBase.chartAreaHeight : 0
        clip: true

        Item {
            id: chartViewportLayer
            x: chartControl._isHorizontalBar
               ? 0 : chartControl._viewportOffsetRatio * parent.width
            y: chartControl._isHorizontalBar
               ? chartControl._viewportOffsetRatio * parent.height : 0
            width: parent.width
            height: parent.height
            transform: Scale {
                origin.x: 0
                origin.y: 0
                xScale: chartControl._isHorizontalBar ? 1 : chartControl._viewportScale
                yScale: chartControl._isHorizontalBar ? chartControl._viewportScale : 1
            }

            Loader {
                id: barContentLoader
                objectName: "barContentLoader"
                anchors.fill: parent
                active: chartControl._xyChartBase !== null
                        && chartControl.chartType === Enums.chart.type_bar
                        && (chartControl._hasChartData || chartControl._hasSeriesValues)
                sourceComponent: Component {
                    BarChartContent {
                        chartData: chartControl._viewChartData
                        series: chartControl._viewSeries
                        maxValue: chartControl.maxValue
                        animated: chartControl.animated
                        showValues: chartControl.showValues
                        showAverage: chartControl.showAverage
                        showMinMax: chartControl.showMinMax
                        showBarGradient: chartControl.showBarGradient
                        getColor: chartControl.getColor
                        hoveredIndex: chartControl._hoveredBarIndex
                        hoveredSeriesIndex: chartControl._hoveredBarSeriesIndex
                        isHorizontal: chartControl._isHorizontalBar
                        valueRange: chartControl._xyChartBase
                                    ? chartControl._xyChartBase.valueRange
                                    : ({ min: 0, max: 1, hasNegative: false, hasPositive: true })
                        zeroLineRatio: chartControl._xyChartBase
                                       ? chartControl._xyChartBase.zeroLineRatio : 1
                        onBarClicked: (index, data) => chartControl.barClicked(index, data)
                        onBarHovered: (index) => chartControl._hoveredBarIndex = index
                        onSeriesBarHovered: (si, bi) => {
                            chartControl._hoveredBarSeriesIndex = si
                            chartControl._hoveredBarIndex = bi
                        }
                    }
                }
            }

            Loader {
                id: lineContentLoader
                objectName: "lineContentLoader"
                anchors.fill: parent
                active: chartControl._xyChartBase !== null
                        && chartControl.chartType === Enums.chart.type_line
                        && (chartControl._hasChartData || chartControl._hasSeriesValues)
                sourceComponent: Component {
                    LineChartContent {
                        chartData: chartControl._viewChartData
                        series: chartControl._viewSeries
                        maxValue: chartControl.maxValue
                        primaryColor: chartControl.primaryColor
                        smoothLine: chartControl.smoothLine
                        animated: chartControl.animated
                        hoverDetectEnabled: chartControl.showTooltip
                                             && !chartControl._viewportTransitionActive
                        showAverage: chartControl.showAverage
                        showMinMax: chartControl.showMinMax
                        isArea: false
                        hoveredIndex: chartControl._hoveredPointIndex
                        hoveredSeriesIndex: chartControl._hoveredLineSeriesIndex
                        boundaryGap: chartControl.boundaryGap
                        showAreaGradient: chartControl.showAreaGradient
                        stacked: chartControl.stacked
                        chartDataProjection: chartControl._viewChartDataProjection
                        seriesValueSources: chartControl._viewSeriesProjection.valueSources
                        renderViewportStart: chartControl._renderStart
                        renderViewportEnd: chartControl._renderEnd
                        onPointClicked: (index, data) => chartControl.pointClicked(index, data)
                        onPointHovered: (index) => chartControl._hoveredPointIndex = index
                        onSeriesPointHovered: (si, pi) => {
                            chartControl._hoveredLineSeriesIndex = si
                            chartControl._hoveredPointIndex = pi
                        }
                        onWheelZoomed: (delta, anchorRatio) =>
                            chartControl.wheelZoomed(delta, anchorRatio)
                    }
                }
            }

            Loader {
                id: scatterContentLoader
                objectName: "scatterContentLoader"
                anchors.fill: parent
                active: chartControl._xyChartBase !== null
                        && chartControl._isScatter
                        && chartControl._hasScatterData
                sourceComponent: Component {
                    ScatterChartContent {
                        series: chartControl._viewSeries
                        dataRange: chartControl._xyChartBase
                                   ? chartControl._xyChartBase.scatterDataRange
                                   : ({ xMin: 0, xMax: 1, yMin: 0, yMax: 1 })
                        animated: chartControl.animated
                        showGrid: chartControl.showGrid
                        hoveredSeriesIndex: chartControl._hoveredScatterSeriesIndex
                        hoveredPointIndex: chartControl._hoveredScatterPointIndex
                        defaultSymbolSize: chartControl.symbolSize
                        onPointClicked: (index, data) => chartControl.pointClicked(index, data)
                        onPointHovered: (si, pi) => {
                            chartControl._hoveredScatterSeriesIndex = si
                            chartControl._hoveredScatterPointIndex = pi
                        }
                    }
                }
            }
        }
    }

    // XY chart tooltips XY 图表提示框
    XYSingleTooltip {
        chart: chartControl
        chartBase: chartControl._xyChartBase
    }

    XYMultiTooltip {
        chart: chartControl
        chartBase: chartControl._xyChartBase
    }

    // XY chart legend; load only the active type with renderable data XY 图表图例；仅加载当前类型且有可渲染数据的图例
    Loader {
        id: xyLegendLoader
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: chartControl.dataZoomEnabled && chartControl._isXYChart
                        ? dataZoomBar.top : parent.bottom
        anchors.bottomMargin: chartControl.dataZoomEnabled && chartControl._isXYChart
                              ? Enums.spacing.s : Enums.spacing.m
        active: chartControl.showLegend
                && ((chartControl.chartType === Enums.chart.type_line
                     || chartControl.chartType === Enums.chart.type_bar)
                    ? chartControl._hasSeriesValues
                    : (chartControl._isScatter && chartControl._hasScatterData))
        sourceComponent: Component {
            ChartBottomLegend {
                legendData: chartControl._series
                legendStyle: chartControl.chartType === Enums.chart.type_line ? "line" :
                             chartControl.chartType === Enums.chart.type_bar ? "bar" : "dot"
                hoveredIndex: chartControl.chartType === Enums.chart.type_line
                              ? chartControl._hoveredLineSeriesIndex
                              : chartControl.chartType === Enums.chart.type_bar
                                ? chartControl._hoveredBarSeriesIndex
                                : chartControl._hoveredScatterSeriesIndex
                hiddenIndices: chartControl._isScatter ? [] : chartControl._hiddenSeriesIndices
                clickable: !chartControl._isScatter
                onItemHovered: (index) => {
                    if (chartControl.chartType === Enums.chart.type_line)
                        chartControl._hoveredLineSeriesIndex = index
                    else if (chartControl.chartType === Enums.chart.type_bar)
                        chartControl._hoveredBarSeriesIndex = index
                    else if (chartControl._isScatter)
                        chartControl._hoveredScatterSeriesIndex = index
                }
                onItemClicked: (index) => {
                    if (!chartControl._isScatter)
                        chartControl.toggleSeriesVisibility(index)
                }
            }
        }
    }

    // Pie chart 饼图
    Loader {
        id: pieAreaLoader
        objectName: "pieAreaLoader"
        anchors.fill: parent
        active: chartControl._isPie && chartControl._hasChartData
        sourceComponent: Component {
            PieChartArea {
                chartData: chartControl._chartData
                totalValue: chartControl.totalValue
                animated: chartControl.animated
                showValues: chartControl.showValues
                showLegend: chartControl.showLegend
                getColor: chartControl.getColor
                title: chartControl.title
                subtitle: chartControl.subtitle
                isDonut: chartControl.isDonut
                donutRatio: chartControl.donutRatio
                donutCenterText: chartControl.donutCenterText
                donutCenterSubtext: chartControl.donutCenterSubtext
                emphasisCenter: chartControl.emphasisCenter
                labelOutside: chartControl.labelOutside
                hoveredIndex: chartControl._hoveredSliceIndex
                onSliceClicked: (index, data) => chartControl.sliceClicked(index, data)
                onSliceHovered: (index) => chartControl._hoveredSliceIndex = index
            }
        }
    }

    // Radar chart 雷达图
    Loader {
        id: radarAreaLoader
        objectName: "radarAreaLoader"
        anchors.fill: parent
        active: chartControl._isRadar && chartControl._hasRadarData
        sourceComponent: Component {
            RadarChartArea {
                indicators: chartControl._indicators
                series: chartControl._series
                animated: chartControl.animated
                showLabels: chartControl.showLabels
                showLegend: chartControl.showLegend
                rings: chartControl.rings
                title: chartControl.title
                subtitle: chartControl.subtitle
                hoveredSeriesIndex: chartControl._hoveredRadarSeriesIndex
                hoveredPointIndex: chartControl._hoveredRadarPointIndex
                hiddenSeriesIndices: chartControl._hiddenSeriesIndices
                onPointClicked: (index, data) => chartControl.pointClicked(index, data)
                onPointHovered: (si, pi) => {
                    chartControl._hoveredRadarSeriesIndex = si
                    chartControl._hoveredRadarPointIndex = pi
                }
                onLegendClicked: (index) => chartControl.toggleSeriesVisibility(index)
            }
        }
    }

    // Boxplot chart 箱线图
    Loader {
        id: boxplotAreaLoader
        objectName: "boxplotAreaLoader"
        anchors.fill: parent
        active: chartControl._isBoxplot && chartControl._hasBoxplotData
        sourceComponent: Component {
            BoxplotChartArea {
                boxplotData: chartControl._boxplotData
                animated: chartControl.animated
                showValues: chartControl.showValues
                showGrid: chartControl.showGrid
                isHorizontal: chartControl.barOrientation === Enums.chart.orientation_horizontal
                title: chartControl.title
                subtitle: chartControl.subtitle
                hoveredIndex: chartControl._hoveredBoxplotIndex
                yAxisLabelWidth: chartControl.yAxisLabelWidth
                valueFormatter: chartControl.valueFormatter
                onBoxClicked: (index, data) => chartControl.boxClicked(index, data)
                onBoxHovered: (index) => chartControl._hoveredBoxplotIndex = index
            }
        }
    }

    // Bottom data zoom slider 底部数据缩放滑块
    ChartDataZoomLayer {
        id: dataZoomBar
        chart: chartControl
    }

    // Chart panning interaction 主图拖动平移交互
    ChartPanArea {
        chart: chartControl
        anchors.fill: xyChartBaseLoader
        z: -1
    }

    // Empty state 空状态
    ChartEmptyState {
        chart: chartControl
    }
}
