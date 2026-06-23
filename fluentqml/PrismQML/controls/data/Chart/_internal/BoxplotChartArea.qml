// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../data"

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
    
    // ==================== Props 属性 ====================
    property string title: ""
    property string subtitle: ""
    property int hoveredIndex: -1
    
    // ==================== Signals 信号 ====================
    signal boxClicked(int index, var data)
    signal boxHovered(int index)
    
    // ==================== Title 标题 ====================
    ChartTitle {
        anchors.horizontalCenter: chartArea.horizontalCenter
        y: Enums.spacing.m
        title: root.title
        subtitle: root.subtitle
    }
    
    // ==================== Chart Area 图表区域 ====================
    Item {
        id: chartArea
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        anchors.topMargin: root.title !== "" ? Enums.spacing.xxxl + Enums.spacing.m : Enums.spacing.l
        anchors.bottomMargin: Enums.spacing.xxxl
        anchors.leftMargin: Enums.spacing.xxxl
        
        // Y-axis labels Y轴标签
        Column {
            id: yAxis
            x: -Enums.spacing.xxxl
            width: Enums.spacing.xxxl - Enums.spacing.xs
            height: parent.height
            
            Repeater {
                model: 6
                Label {
                    width: parent.width
                    y: index * (chartArea.height / 5) - height / 2
                    type: Enums.label.type_caption
                    text: {
                        if (root.boxplotData.length === 0) return ""
                        var range = boxplotContent.valueRange
                        var val = range.max - (range.max - range.min) * index / 5
                        return Math.round(val).toString()
                    }
                    color: Enums.textColor.tertiary
                    horizontalAlignment: Text.AlignRight
                }
            }
        }
        
        // X-axis labels X轴标签
        Row {
            y: parent.height + Enums.spacing.s
            width: parent.width
            
            Repeater {
                model: root.boxplotData
                Label {
                    width: chartArea.width / root.boxplotData.length
                    type: Enums.label.type_caption
                    text: modelData.label || ""
                    color: root.hoveredIndex === index 
                           ? Enums.textColor.primary : Enums.textColor.secondary
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
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
    
    // ==================== Tooltip 提示框 ====================
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
