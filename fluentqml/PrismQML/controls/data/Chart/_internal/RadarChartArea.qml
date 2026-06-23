// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// RadarChartArea - Complete radar chart area 完整雷达图区域
// Includes chart content, tooltip, and legend 包含图表内容、提示框和图例


Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var indicators         // [{name: "", max: 100}, ...]
    required property var series             // [{name: "", values: [], color: ""}, ...]
    required property bool animated
    required property bool showLabels
    required property bool showLegend
    required property int rings
    
    // ==================== Props 属性 ====================
    property string title: ""
    property string subtitle: ""
    property int hoveredSeriesIndex: -1
    property int hoveredPointIndex: -1
    property var hiddenSeriesIndices: []
    
    // ==================== Signals 信号 ====================
    signal pointClicked(int index, var data)
    signal pointHovered(int seriesIndex, int pointIndex)
    signal legendClicked(int seriesIndex)
    
    // ==================== Helper Functions 辅助函数 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function isSeriesVisible(index) {
        return hiddenSeriesIndices.indexOf(index) < 0
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
        id: chartArea
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        anchors.topMargin: root.title !== "" ? Enums.spacing.xxxl + Enums.spacing.m : Enums.spacing.l
        anchors.bottomMargin: root.showLegend ? Enums.spacing.xxxl : Enums.spacing.l
        
        RadarChartContent {
            id: radarContent
            anchors.fill: parent
            visible: root.indicators.length > 2
            
            indicators: root.indicators
            series: root.series
            animated: root.animated
            showLabels: root.showLabels
            rings: root.rings
            hoveredSeriesIndex: root.hoveredSeriesIndex
            hoveredPointIndex: root.hoveredPointIndex
            
            onPointClicked: (index, data) => root.pointClicked(index, data)
            onPointHovered: (seriesIndex, pointIndex) => root.pointHovered(seriesIndex, pointIndex)
        }
    }
    
    // ==================== Tooltip 提示框 ====================
    // Tooltip follows mouse position 提示框跟随鼠标位置
    ChartTooltip {
        visible: root.hoveredSeriesIndex >= 0 && root.hoveredPointIndex >= 0 && root.indicators.length > 2
        x: chartArea.x + Math.min(Math.max(radarContent.mouseX + Enums.spacing.m, 0), chartArea.width - width - Enums.spacing.m)
        y: chartArea.y + Math.max(radarContent.mouseY - height - Enums.spacing.m, Enums.spacing.m)
        
        showColorDot: true
        dotColor: root.hoveredSeriesIndex >= 0 ? root.getSeriesColor(root.hoveredSeriesIndex) : "transparent"
        label: root.hoveredSeriesIndex >= 0 ? (root.series[root.hoveredSeriesIndex].name || "") : ""
        value: {
            if (root.hoveredSeriesIndex < 0 || root.hoveredPointIndex < 0) return ""
            var indicator = root.indicators[root.hoveredPointIndex]
            var val = root.series[root.hoveredSeriesIndex].values[root.hoveredPointIndex]
            return (indicator.name || "") + ": " + (val || 0)
        }
        isValueString: true
        
        Behavior on x { NumberAnimation { duration: Enums.duration.ultraFast; easing.type: Easing.OutQuad } }
        Behavior on y { NumberAnimation { duration: Enums.duration.ultraFast; easing.type: Easing.OutQuad } }
    }
    
    // ==================== Legend 图例 ====================
    ChartBottomLegend {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.m
        visible: root.showLegend && root.series.length > 0
        legendData: root.series
        legendStyle: "bar"
        hoveredIndex: root.hoveredSeriesIndex
        hiddenIndices: root.hiddenSeriesIndices
        clickable: true
        onItemHovered: (index) => root.pointHovered(index, -1)
        onItemClicked: (index) => root.legendClicked(index)
    }
}
