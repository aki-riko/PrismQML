// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../data"
import "ChartAxisLayout.js" as ChartAxisLayout

// BoxplotChartArea - Complete boxplot chart area 完整箱线图区域
// Includes chart content, axes, tooltip, and grid 包含图表内容、坐标轴、提示框和网格

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var boxplotData        // [{label: "", min, q1, median, q3, max, outliers: []}, ...]
    required property bool animated
    required property bool showValues
    required property bool showGrid
    required property bool isHorizontal
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property string subtitle: ""
    property int hoveredIndex: -1
    // Explicit Y-axis width; zero enables content measurement 显式Y轴宽度；0表示按内容自动测量
    property real yAxisLabelWidth: 0
    property var valueFormatter: null

    // ==================== Internal Props 内部属性 ====================
    property int _labelHoverIndex: -1
    property int _lastLabelUpdateCount: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property var _yAxisLabelTexts: _buildYAxisLabels()
    readonly property var _categoryLabelTexts: _buildCategoryLabels()
    readonly property real effectiveYAxisLabelWidth: {
        if (yAxisLabelWidth > 0) return yAxisLabelWidth
        return ChartAxisLayout.boundedAxisWidth(
            axisFontMetrics,
            _yAxisLabelTexts,
            Enums.controlSize.chartYAxisWidth,
            Enums.controlSize.chartYAxisMaxWidth,
            Enums.spacing.m + Enums.spacing.s
        )
    }
    readonly property real _categorySlotWidth: boxplotData.length > 0
        ? chartArea.width / boxplotData.length : 0
    readonly property int _categoryLabelStride: ChartAxisLayout.categoryStride(
        axisFontMetrics,
        _categoryLabelTexts,
        _categorySlotWidth,
        Enums.spacing.m
    )
    
    // ==================== Signals 信号 ====================
    signal boxClicked(int index, var data)
    signal boxHovered(int index)

    // ==================== Internal Methods 内部方法 ====================
    function _setLabelHovered(index, hovered) {
        if (index < 0 || index >= xAxisLabelRepeater.count) return false
        var label = xAxisLabelRepeater.itemAt(index)
        if (!label) return false
        label._hovered = hovered
        return true
    }

    function _syncHoveredLabel() {
        var updateCount = 0
        if (_labelHoverIndex !== hoveredIndex) {
            if (_setLabelHovered(_labelHoverIndex, false)) updateCount++
            if (_setLabelHovered(hoveredIndex, true)) updateCount++
        }
        _labelHoverIndex = hoveredIndex
        _lastLabelUpdateCount = updateCount
    }

    function _formatAxisValue(value) {
        if (valueFormatter && typeof valueFormatter === "function") {
            return String(valueFormatter(value))
        }
        return String(Math.round(value))
    }

    function _buildYAxisLabels() {
        var labels = []
        if (boxplotData.length === 0) return labels
        var range = boxplotContent.valueRange
        for (var index = 0; index < 6; index++) {
            var value = range.max - (range.max - range.min) * index / 5
            labels.push(_formatAxisValue(value))
        }
        return labels
    }

    function _buildCategoryLabels() {
        var labels = []
        for (var index = 0; index < boxplotData.length; index++) {
            var item = boxplotData[index]
            labels.push(item && item.label !== undefined ? String(item.label) : "")
        }
        return labels
    }

    onHoveredIndexChanged: _syncHoveredLabel()
    
    // ==================== Content 内容 ====================
    // Title 标题
    ChartTitle {
        anchors.horizontalCenter: chartArea.horizontalCenter
        y: Enums.spacing.m
        title: root.title
        subtitle: root.subtitle
    }

    FontMetrics {
        id: axisFontMetrics
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.caption
    }
    
    // Chart area 图表区域
    Item {
        id: chartArea
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        anchors.topMargin: root.title !== "" ? Enums.spacing.xxxl + Enums.spacing.m : Enums.spacing.l
        anchors.bottomMargin: Enums.spacing.xxxl
        anchors.leftMargin: root.effectiveYAxisLabelWidth
        
        // Y-axis labels Y轴标签
        Column {
            id: yAxis
            x: -root.effectiveYAxisLabelWidth
            width: root.effectiveYAxisLabelWidth - Enums.spacing.s
            height: parent.height
            
            Repeater {
                model: 6
                Label {
                    width: parent.width
                    y: index * (chartArea.height / 5) - height / 2
                    type: Enums.label.type_caption
                    text: root._yAxisLabelTexts[index] || ""
                    color: Enums.textColor.tertiary
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideLeft
                }
            }
        }
        
        // X-axis labels X轴标签
        Item {
            id: xAxis

            y: parent.height + Enums.spacing.s
            width: parent.width
            height: Enums.controlSize.chartXAxisHeight
            clip: true
            
            Repeater {
                id: xAxisLabelRepeater

                model: root.boxplotData
                Item {
                    property bool _hovered: false

                    x: index * root._categorySlotWidth
                    width: root._categorySlotWidth
                    height: parent.height
                    Component.onCompleted: _hovered = root.hoveredIndex === index

                    Label {
                        x: ChartAxisLayout.clampedCenteredX(
                            parent.x + parent.width / 2,
                            width,
                            xAxis.width
                        ) - parent.x
                        width: ChartAxisLayout.categoryLabelWidth(
                            axisFontMetrics,
                            text,
                            root._categorySlotWidth,
                            root._categoryLabelStride,
                            Enums.spacing.m,
                            xAxis.width
                        )
                        type: Enums.label.type_caption
                        visible: ChartAxisLayout.categoryLabelVisible(
                            index, root.boxplotData.length, root._categoryLabelStride
                        )
                        text: root._categoryLabelTexts[index] || ""
                        color: parent._hovered ? Enums.textColor.primary : Enums.textColor.secondary
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }
                }
            }
        }
        
        // Grid lines 网格线
        Canvas {
            anchors.fill: parent
            visible: root.showGrid
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = Enums.stateColor.controlBgHover
                ctx.lineWidth = 1
                
                for (var i = 0; i <= 5; i++) {
                    var y = i * height / 5
                    ctx.beginPath()
                    ctx.moveTo(0, y)
                    ctx.lineTo(width, y)
                    ctx.stroke()
                }
            }
        }
        
        BoxplotChartContent {
            id: boxplotContent
            anchors.fill: parent
            visible: root.boxplotData.length > 0
            
            boxplotData: root.boxplotData
            animated: root.animated
            showValues: root.showValues
            isHorizontal: root.isHorizontal
            hoveredIndex: root.hoveredIndex
            
            onBoxClicked: (index, data) => root.boxClicked(index, data)
            onBoxHovered: (index) => root.boxHovered(index)
        }
    }
    
    // Tooltip 提示框
    Rectangle {
        id: tooltip
        visible: root.hoveredIndex >= 0 && root.boxplotData.length > 0
        x: chartArea.x + Math.min(Math.max(
            (root.hoveredIndex + 0.5) * (chartArea.width / root.boxplotData.length) - width / 2, 0),
            chartArea.width - width)
        y: chartArea.y + Enums.spacing.m
        width: Math.max(tooltipColumn.width + Enums.spacing.l, 100)
        height: tooltipColumn.height + Enums.spacing.m
        radius: Enums.radius.medium
        color: Enums.cardColor
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
        
        layer.enabled: visible
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: Enums.shadow.level2.color
            shadowBlur: Enums.shadow.level2.blurNormalized
            shadowVerticalOffset: Enums.shadow.level2.offset
        }
        
        Column {
            id: tooltipColumn
            x: Enums.spacing.s
            y: Enums.spacing.xs
            spacing: Enums.spacing.xxs
            
            Label {
                type: Enums.label.type_caption
                text: root.hoveredIndex >= 0 && root.hoveredIndex < root.boxplotData.length
                      ? (root.boxplotData[root.hoveredIndex].label || "") : ""
                font.weight: Font.DemiBold
            }
            
            Repeater {
                model: root.hoveredIndex >= 0 && root.hoveredIndex < root.boxplotData.length ? [
                    { key: "Max", val: root.boxplotData[root.hoveredIndex].max },
                    { key: "Q3", val: root.boxplotData[root.hoveredIndex].q3 },
                    { key: "Median", val: root.boxplotData[root.hoveredIndex].median },
                    { key: "Q1", val: root.boxplotData[root.hoveredIndex].q1 },
                    { key: "Min", val: root.boxplotData[root.hoveredIndex].min }
                ] : []
                
                Row {
                    spacing: Enums.spacing.m
                    Label {
                        type: Enums.label.type_caption
                        text: modelData.key
                        color: Enums.textColor.secondary
                        width: 50
                    }
                    Label {
                        type: Enums.label.type_caption
                        text: modelData.val !== undefined ? modelData.val.toString() : ""
                        font.weight: Font.DemiBold
                    }
                }
            }
        }
    }
}
