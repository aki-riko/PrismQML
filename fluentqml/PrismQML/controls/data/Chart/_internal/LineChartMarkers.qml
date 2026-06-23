// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// LineChartMarkers - Min/Max markers and average labels 最大最小值标记和平均值标签
// Extracted from LineChartContent.qml for modularity 从 LineChartContent.qml 提取以实现模块化

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var series              // Series data array 系列数据数组
    required property var seriesPointPositions // Calculated point positions 计算的点位置
    required property bool showMinMax         // Show min/max markers 显示最大最小值标记
    required property bool showAverage        // Show average labels 显示平均值标签
    required property real chartWidth         // Chart width 图表宽度
    
    // ==================== Functions 函数 ====================
    property var getSeriesColor: function(index) { return Enums.accentColor }
    property var valueToY: function(value) { return 0 }
    property var findMinMaxIndices: function(values) {
        if (!values || values.length === 0) {
            return { minIdx: -1, maxIdx: -1, minVal: 0, maxVal: 0 }
        }
        var minIdx = 0, maxIdx = 0
        for (var i = 1; i < values.length; i++) {
            if (values[i] < values[minIdx]) minIdx = i
            if (values[i] > values[maxIdx]) maxIdx = i
        }
        return { minIdx: minIdx, maxIdx: maxIdx, minVal: values[minIdx], maxVal: values[maxIdx] }
    }
    property var calculateAverage: function(values) {
        if (!values || values.length === 0) return 0
        var sum = 0
        for (var i = 0; i < values.length; i++) sum += values[i]
        return sum / values.length
    }
    
    // ==================== Min/Max Bubble Markers 最大最小值气泡标记 ====================
    Repeater {
        model: root.series.length > 0 && root.showMinMax ? root.series : []
        
        Item {
            id: markerItem
            anchors.fill: parent
            
            property int seriesIdx: index
            property var values: modelData.values || []
            property var minMax: root.findMinMaxIndices(values)
            property color seriesColor: root.getSeriesColor(index)
            
            // Max marker (above point) 最大值标记（点上方）
            Rectangle {
                id: maxMarker
                visible: markerItem.minMax.maxIdx >= 0 && root.seriesPointPositions.length > markerItem.seriesIdx
                x: {
                    if (!visible || !root.seriesPointPositions[markerItem.seriesIdx]) return 0
                    return root.seriesPointPositions[markerItem.seriesIdx][markerItem.minMax.maxIdx].x - width/2
                }
                y: {
                    if (!visible || !root.seriesPointPositions[markerItem.seriesIdx]) return 0
                    return root.seriesPointPositions[markerItem.seriesIdx][markerItem.minMax.maxIdx].y - height - 6
                }
                width: maxLabel.width + Enums.spacing.l
                height: Enums.spacing.xxl
                radius: Enums.radius.small
                color: markerItem.seriesColor
                
                // Triangle pointer 三角形指针
                Canvas {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.bottom
                    width: 8
                    height: 5
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.fillStyle = markerItem.seriesColor
                        ctx.beginPath()
                        ctx.moveTo(0, 0)
                        ctx.lineTo(width, 0)
                        ctx.lineTo(width/2, height)
                        ctx.closePath()
                        ctx.fill()
                    }
                }
                
                Label {
                    id: maxLabel
                    anchors.centerIn: parent
                    type: Enums.label.type_caption
                    text: markerItem.minMax.maxVal !== undefined ? markerItem.minMax.maxVal.toString() : ""
                    font.weight: Font.DemiBold
                    color: "white"
                }
            }
            
            // Min marker (below point) 最小值标记（点下方）
            Rectangle {
                id: minMarker
                visible: markerItem.minMax.minIdx >= 0 && root.seriesPointPositions.length > markerItem.seriesIdx
                x: {
                    if (!visible || !root.seriesPointPositions[markerItem.seriesIdx]) return 0
                    return root.seriesPointPositions[markerItem.seriesIdx][markerItem.minMax.minIdx].x - width/2
                }
                y: {
                    if (!visible || !root.seriesPointPositions[markerItem.seriesIdx]) return 0
                    return root.seriesPointPositions[markerItem.seriesIdx][markerItem.minMax.minIdx].y + 6 + 5
                }
                width: minLabel.width + Enums.spacing.l
                height: Enums.spacing.xxl
                radius: Enums.radius.small
                color: markerItem.seriesColor
                
                // Triangle pointer (pointing up) 三角形指针（向上）
                Canvas {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.top
                    width: 8
                    height: 5
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.fillStyle = markerItem.seriesColor
                        ctx.beginPath()
                        ctx.moveTo(width/2, 0)
                        ctx.lineTo(0, height)
                        ctx.lineTo(width, height)
                        ctx.closePath()
                        ctx.fill()
                    }
                }
                
                Label {
                    id: minLabel
                    anchors.centerIn: parent
                    type: Enums.label.type_caption
                    text: markerItem.minMax.minVal !== undefined ? markerItem.minMax.minVal.toString() : ""
                    font.weight: Font.DemiBold
                    color: "white"
                }
            }
        }
    }
    
    // ==================== Average Value Labels 平均值标签 ====================
    Repeater {
        model: root.series.length > 0 && root.showAverage ? root.series : []
        
        Label {
            property var values: modelData.values || []
            property real avg: root.calculateAverage(values)
            property color seriesColor: root.getSeriesColor(index)
            
            x: root.chartWidth + 4
            y: root.valueToY(avg) - height / 2
            type: Enums.label.type_caption
            text: avg.toFixed(2)
            color: seriesColor
            visible: values.length > 0
        }
    }
}
