// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// PieChartArea - Complete pie/donut chart area 完整饼图/环形图区域
// Includes chart content, center text, tooltip, and legend 包含图表内容、中心文字、提示框和图例


Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var chartData          // [{label: "", value: 0, color: ""}, ...]
    required property real totalValue        // Sum of all values 所有值的总和
    required property bool animated          // Enable animation 启用动画
    required property bool showValues        // Show percentage labels 显示百分比标签
    required property bool showLegend        // Show legend 显示图例
    required property var getColor           // Function to get color 获取颜色函数
    
    // ==================== Props 属性 ====================
    property string title: ""
    property string subtitle: ""
    property bool isDonut: false
    property real donutRatio: 0.6
    property string donutCenterText: ""
    property string donutCenterSubtext: ""
    property bool emphasisCenter: false
    property bool labelOutside: false
    property int hoveredIndex: -1
    
    // ==================== Signals 信号 ====================
    signal sliceClicked(int index, var data)
    signal sliceHovered(int index)
    
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
        x: Enums.spacing.l
        y: root.title !== "" ? Enums.spacing.xxxl + Enums.spacing.m : Enums.spacing.l
        width: root.width - Enums.spacing.xxl
        height: root.height - y - (root.showLegend ? Enums.spacing.xxxl + Enums.spacing.m : Enums.spacing.l)
        
        PieChartContent {
            id: pieContent
            anchors.fill: parent
            visible: root.chartData.length > 0
            
            chartData: root.chartData
            totalValue: root.totalValue
            animated: root.animated
            showValues: root.showValues
            isDonut: root.isDonut
            donutRatio: root.donutRatio
            getColor: root.getColor
            hoveredIndex: root.hoveredIndex
            labelOutside: root.labelOutside
            
            onSliceClicked: (index, data) => root.sliceClicked(index, data)
            onSliceHovered: (index) => root.sliceHovered(index)
        }
        
        // Donut center text 环形图中心文字
        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.xxs
            visible: root.isDonut && (root.donutCenterText !== "" || root.donutCenterSubtext !== "" || root.emphasisCenter)
            
            // Static center text 静态中心文字
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_body_strong
                text: root.donutCenterText
                font.pixelSize: Enums.typography.title
                visible: root.donutCenterText !== "" && (!root.emphasisCenter || root.hoveredIndex < 0)
            }
            
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_caption
                text: root.donutCenterSubtext
                color: Enums.textColor.secondary
                visible: root.donutCenterSubtext !== "" && (!root.emphasisCenter || root.hoveredIndex < 0)
            }
            
            // Emphasis center label (shown on hover) 悬停时中心强调标签
            Label {
                id: emphasisValue
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_body_strong
                text: {
                    if (root.hoveredIndex < 0 || root.hoveredIndex >= root.chartData.length) return ""
                    var d = root.chartData[root.hoveredIndex]
                    return d ? (d.value || 0).toString() : ""
                }
                font.pixelSize: Enums.typography.displayLarge
                color: root.hoveredIndex >= 0 ? root.getColor(root.hoveredIndex) : Enums.textColor.primary
                visible: root.emphasisCenter && root.hoveredIndex >= 0
                
                Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                
                transform: Scale {
                    origin.x: emphasisValue.width / 2
                    origin.y: emphasisValue.height / 2
                    xScale: root.hoveredIndex >= 0 ? 1.0 : 0.8
                    yScale: root.hoveredIndex >= 0 ? 1.0 : 0.8
                    Behavior on xScale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                    Behavior on yScale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                }
            }
            
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_body
                text: {
                    if (root.hoveredIndex < 0 || root.hoveredIndex >= root.chartData.length) return ""
                    var d = root.chartData[root.hoveredIndex]
                    return d ? (d.label || "") : ""
                }
                color: Enums.textColor.secondary
                visible: root.emphasisCenter && root.hoveredIndex >= 0
            }
        }
    }
    
    // ==================== Tooltip 提示框 ====================
    ChartTooltip {
        visible: root.hoveredIndex >= 0 && root.chartData.length > 0
        x: Math.min(chartArea.x + chartArea.width / 2 - width / 2, root.width - width - Enums.spacing.m)
        y: chartArea.y + Enums.spacing.m
        
        showColorDot: true
        dotColor: root.hoveredIndex >= 0 ? root.getColor(root.hoveredIndex) : "transparent"
        label: root.hoveredIndex >= 0 && root.hoveredIndex < root.chartData.length
               ? (root.chartData[root.hoveredIndex].label || "") : ""
        value: {
            if (root.hoveredIndex < 0 || root.hoveredIndex >= root.chartData.length) return ""
            var d = root.chartData[root.hoveredIndex]
            if (!d || d.value === undefined) return ""
            return d.value + " (" + Math.round(d.value / root.totalValue * 100) + "%)"
        }
        isValueString: true
    }
    
    // ==================== Legend 图例 ====================
    ChartBottomLegend {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.m
        visible: root.showLegend && root.chartData.length > 0
        legendData: root.chartData
        legendStyle: "dot"
        hoveredIndex: root.hoveredIndex
        getColor: root.getColor
        clickable: true
        onItemHovered: (index) => root.sliceHovered(index)
        onItemClicked: (index) => root.sliceClicked(index, root.chartData[index])
    }
}
