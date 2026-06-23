// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import "../../../data"

// XYChartCore - Base component for XY-axis charts XY轴图表基类
// Provides common grid, axes, and chart area for Bar/Line/Area/Scatter charts 为柱状图/折线图/面积图/散点图提供公共网格、坐标轴和图表区域

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var chartData      // Chart data 图表数据 [{label: "", value: 0, color: ""}, ...]
    required property real maxValue      // Maximum value for Y-axis Y轴最大值
    required property bool showLabels    // Show X-axis labels 显示X轴标签
    required property bool showValues    // Show value labels 显示数值标签
    required property bool showGrid      // Show grid lines 显示网格线
    required property string title       // Chart title 图表标题
    
    // ==================== Optional Props 可选属性 ====================
    property var series: []              // For scatter chart 散点图系列数据
    property bool isScatter: false       // Is scatter chart 是否散点图
    property int hoveredIndex: -1        // Hovered data index 悬浮数据索引
    property real minValue: 0            // Minimum value for Y-axis Y轴最小值
    property bool isHorizontal: false    // Horizontal bar chart 水平柱状图
    property string subtitle: ""         // Subtitle 副标题
    property string yAxisSuffix: ""      // Y-axis label suffix (e.g. " °C") Y轴标签后缀
    // Y-axis label / tooltip value formatter 自定义 Y 轴/tooltip 数值格式化器
    // function(value) -> string;若提供则覆盖 yAxisSuffix 默认拼接
    property var valueFormatter: null
    // Y-axis label area width (px) Y 轴标签区宽度;默认走全局常量,
    // 多级货币等长字符串场景可覆盖更大值避免左截断
    property real yAxisLabelWidth: Enums.controlSize.chartYAxisWidth
    property bool showLegend: false      // Show legend (affects bottom margin) 显示图例（影响底部边距）
    
    // ==================== Signals 信号 ====================
    signal xLabelHovered(int index)
    
    // ==================== Readonly Props 只读属性 ====================
    readonly property Item chartArea: chartAreaItem
    readonly property real chartAreaX: chartAreaItem ? chartAreaItem.x : 0
    readonly property real chartAreaY: chartAreaItem ? chartAreaItem.y : 0
    readonly property real chartAreaWidth: chartAreaItem ? (chartAreaItem.width || 0) : 0
    readonly property real chartAreaHeight: chartAreaItem ? (chartAreaItem.height || 0) : 0
    
    // Value range for charts with negative values 支持负值的数值范围
    readonly property var valueRange: {
        var min = 0, max = 0
        // 1) chartData 单 series 模式: 每项 {label, value}
        for (var i = 0; i < chartData.length; i++) {
            var val = chartData[i] && chartData[i].value !== undefined ? chartData[i].value : 0
            if (val < min) min = val
            if (val > max) max = val
        }
        // 2) series 多 series 模式: 每 series {name, values[], color}
        for (var s = 0; s < series.length; s++) {
            var vals = series[s] && series[s].values ? series[s].values : []
            for (var k = 0; k < vals.length; k++) {
                var v = vals[k] !== undefined ? vals[k] : 0
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
    
    // Zero line position (0-1) 零轴线位置
    readonly property real zeroLineRatio: {
        var range = valueRange
        if (!range.hasNegative) return 1.0  // All positive, zero at bottom 全正值，零轴在底部
        if (!range.hasPositive) return 0.0  // All negative, zero at top 全负值，零轴在顶部
        return range.max / (range.max - range.min)
    }
    
    // Scatter chart data range 散点图数据范围
    readonly property var scatterDataRange: {
        if (!isScatter || series.length === 0) return { xMin: 0, xMax: 1, yMin: 0, yMax: 1 }
        
        var minX = Infinity, maxX = -Infinity
        var minY = Infinity, maxY = -Infinity
        
        for (var s = 0; s < series.length; s++) {
            var data = series[s].data || []
            for (var i = 0; i < data.length; i++) {
                var x = data[i][0], y = data[i][1]
                if (x < minX) minX = x
                if (x > maxX) maxX = x
                if (y < minY) minY = y
                if (y > maxY) maxY = y
            }
        }
        
        var xPadding = (maxX - minX) * 0.1 || 1
        var yPadding = (maxY - minY) * 0.1 || 1
        
        return {
            xMin: minX - xPadding, xMax: maxX + xPadding,
            yMin: minY - yPadding, yMax: maxY + yPadding
        }
    }

    // ==================== Title 标题 ====================
    ChartTitle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: Enums.spacing.m
        title: root.title
        subtitle: root.subtitle
    }
    
    // ==================== Chart Area 图表区域 ====================
    Item {
        id: chartAreaItem
        x: root.isHorizontal ? root.yAxisLabelWidth + Enums.spacing.xl
                             : root.yAxisLabelWidth
        y: root.title !== "" ? Enums.spacing.xxxl + Enums.spacing.xl : Enums.spacing.xxxl
        width: root.isHorizontal
               ? root.width - root.yAxisLabelWidth - Enums.spacing.xxxl - Enums.spacing.l
               : root.width - root.yAxisLabelWidth - Enums.spacing.xl
        height: root.height - y
                - (root.showLabels ? Enums.controlSize.chartXAxisHeight + Enums.spacing.m : Enums.spacing.l)
                - (root.isScatter ? Enums.spacing.xxxl : 0)
                - (root.showLegend && root.series.length > 0 ? Enums.spacing.xxxl : 0)
    }
    
    // ==================== Grid Lines 网格线 (Fluent Design) ====================
    Item {
        id: gridLines
        anchors.fill: chartAreaItem
        visible: root.showGrid && (root.chartData.length > 0 || root.series.length > 0)
        
        // Horizontal grid lines - light and subtle 水平网格线 - 轻量简洁
        Repeater {
            model: 5
            Rectangle {
                x: 0
                y: index * (gridLines.height / 4)
                width: gridLines.width
                height: Enums.border.thin
                color: Enums.chartColors.gridLine
            }
        }
        
        // Zero line for negative values 负值零轴线
        Rectangle {
            x: 0
            y: root.zeroLineRatio * gridLines.height
            width: gridLines.width
            height: Enums.border.thin
            color: Enums.textColor.tertiary
            visible: root.valueRange.hasNegative && root.valueRange.hasPositive && !root.isScatter
        }
        
        // Vertical grid lines for horizontal bar chart 水平柱状图的垂直网格线
        Repeater {
            model: root.isHorizontal ? 5 : 0
            Rectangle {
                x: index * (gridLines.width / 4)
                y: 0
                width: Enums.border.thin
                height: gridLines.height
                color: Enums.chartColors.gridLine
            }
        }
    }
    
    // ==================== Y-Axis Labels Y轴标签 ====================
    Item {
        id: yAxisLabels
        x: 0
        y: chartAreaItem.y
        width: root.yAxisLabelWidth - Enums.spacing.s
        height: chartAreaItem.height
        visible: (root.chartData.length > 0 || root.series.length > 0) && !root.isHorizontal
        
        Repeater {
            model: 5
            Label {
                x: 0
                y: index * (yAxisLabels.height / 4) - Enums.spacing.xs
                width: yAxisLabels.width
                type: Enums.label.type_caption
                text: {
                    function fmt(v) {
                        if (root.valueFormatter && typeof root.valueFormatter === "function") {
                            return root.valueFormatter(v)
                        }
                        return v + root.yAxisSuffix
                    }
                    if (root.isScatter) {
                        var range = root.scatterDataRange
                        var value = range.yMax - (range.yMax - range.yMin) * index / 4
                        return fmt(value.toFixed(1))
                    }
                    var vRange = root.valueRange
                    var v2 = vRange.max - (vRange.max - vRange.min) * index / 4
                    return fmt(Math.round(v2 * 100) / 100)
                }
                color: Enums.chartColors.axisLabel
                horizontalAlignment: Text.AlignRight
            }
        }
    }
    
    // ==================== Y-Axis Labels for Horizontal Bar 水平柱状图Y轴标签（分类） ====================
    Column {
        id: horizontalYAxisLabels
        x: Enums.spacing.s
        y: chartAreaItem.y
        width: Enums.controlSize.chartYAxisWidth + Enums.spacing.l
        height: chartAreaItem.height
        visible: root.isHorizontal && root.chartData.length > 0
        
        Repeater {
            model: root.chartData
            Label {
                width: parent.width
                height: parent.height / Math.max(root.chartData.length, 1)
                type: Enums.label.type_caption
                text: modelData && modelData.label ? modelData.label : ""
                color: root.hoveredIndex === index
                       ? Enums.textColor.primary 
                       : Enums.textColor.tertiary
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                rightPadding: Enums.spacing.s
                
                Behavior on color {
                    ColorAnimation { duration: Enums.duration.fast }
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: root.xLabelHovered(index)
                    onExited: root.xLabelHovered(-1)
                }
            }
        }
    }
    
    // ==================== X-Axis Labels for Horizontal Bar 水平柱状图X轴标签（数值） ====================
    Item {
        x: chartAreaItem.x
        y: chartAreaItem.y + chartAreaItem.height + Enums.spacing.xs
        width: chartAreaItem.width
        height: Enums.controlSize.chartXAxisHeight
        visible: root.isHorizontal && root.chartData.length > 0
        
        Repeater {
            model: 5
            Label {
                x: index * (parent.width / 4) - (index === 0 ? 0 : width / 2)
                type: Enums.label.type_caption
                text: {
                    var vRange = root.valueRange
                    var value = vRange.min + (vRange.max - vRange.min) * index / 4
                    return Math.round(value * 100) / 100
                }
                color: Enums.textColor.tertiary
            }
        }
    }
    
    // ==================== X-Axis Labels (Category) X轴标签（分类） ====================
    Row {
        id: xAxisLabels
        x: chartAreaItem.x
        y: chartAreaItem.y + chartAreaItem.height + Enums.spacing.xs
        width: chartAreaItem.width
        visible: root.showLabels && root.chartData.length > 0 && !root.isScatter && !root.isHorizontal
        
        Repeater {
            model: root.chartData
            Label {
                width: parent.width / root.chartData.length
                type: Enums.label.type_caption
                // 每个 label 宽度太窄就跳过 (避免 1000+ 数据点 label 糊成黑条 + 巨量渲染开销)
                // 至少留 24px 给一个 caption, 否则按比例抽样: 每 N 个画 1 个
                visible: {
                    if (width >= 24) return true
                    var n = Math.ceil(24 / Math.max(1, width))
                    return index % n === 0
                }
                text: modelData && modelData.label ? modelData.label : ""
                color: root.hoveredIndex === index
                       ? Enums.textColor.primary
                       : Enums.textColor.tertiary
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight

                Behavior on color {
                    ColorAnimation { duration: Enums.duration.fast }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: root.xLabelHovered(index)
                    onExited: root.xLabelHovered(-1)
                }
            }
        }
    }
    
    // ==================== X-Axis Labels (Numeric for Scatter) X轴标签（散点图数值） ====================
    Item {
        x: chartAreaItem.x
        y: chartAreaItem.y + chartAreaItem.height + Enums.spacing.xs
        width: chartAreaItem.width
        height: Enums.controlSize.chartXAxisHeight
        visible: root.isScatter && root.series.length > 0
        
        Repeater {
            model: 6
            Label {
                x: index * (parent.width / 5) - width / 2
                type: Enums.label.type_caption
                text: {
                    var range = root.scatterDataRange
                    var value = range.xMin + (range.xMax - range.xMin) * index / 5
                    return value.toFixed(1)
                }
                color: Enums.textColor.secondary
            }
        }
    }
}
