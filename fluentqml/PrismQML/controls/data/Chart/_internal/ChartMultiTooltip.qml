// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../data"

// ChartMultiTooltip - Multi-series tooltip component 多系列提示框组件
// Used for line/bar charts with multiple series 用于多系列折线图/柱状图

Rectangle {
    id: root
    
    // ==================== Props 属性 ====================
    property string xLabel: ""           // X-axis label (e.g. "Mon") X轴标签
    property var seriesData: []          // [{name: "", value: 0, color: ""}, ...]
    property bool showTotal: false       // Show total row for stacked charts 堆叠图显示总计
    property real totalValue: 0          // Total value for stacked charts 堆叠图总计值
    // Value formatter callback 自定义数值格式化器
    property var valueFormatter: null
    
    // ==================== Size 尺寸 ====================
    width: Math.max(contentColumn.width + Enums.spacing.l, 80)
    height: Math.max(contentColumn.height + Enums.spacing.m, 30)
    
    // ==================== Style 样式 ====================
    radius: Enums.radius.medium
    color: Enums.cardColor
    border.width: Enums.border.thin
    border.color: Enums.stateColor.border
    
    // Shadow effect 阴影效果
    layer.enabled: visible
    layer.effect: MultiEffect {
        shadowEnabled: true
        shadowColor: Enums.shadow.level2.color
        shadowBlur: Enums.shadow.level2.blurNormalized
        shadowVerticalOffset: Enums.shadow.level2.offset
    }
    
    // Fluent Design: fade in animation 淡入动画
    opacity: visible ? 1.0 : 0.0
    scale: visible ? 1.0 : 0.95
    Behavior on opacity { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
    Behavior on scale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
    
    // ==================== Content 内容 ====================
    Column {
        id: contentColumn
        x: Enums.spacing.s
        y: Enums.spacing.xs
        spacing: Enums.spacing.xxs
        
        // X-axis label X轴标签
        Label {
            type: Enums.label.type_caption
            text: root.xLabel
            font.weight: Font.DemiBold
            visible: root.xLabel !== ""
        }
        
        // Series values 系列值
        Repeater {
            model: root.seriesData
            Row {
                spacing: Enums.spacing.s
                
                Item {
                    width: Enums.spacing.s
                    height: parent.height
                    Rectangle {
                        width: Enums.spacing.s
                        height: Enums.spacing.s
                        radius: width / 2
                        color: modelData.color || Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                Label {
                    type: Enums.label.type_caption
                    text: modelData.name || ""
                    color: Enums.textColor.secondary
                    width: 60
                }
                Label {
                    type: Enums.label.type_caption
                    text: {
                        if (modelData.value === undefined) return ""
                        if (root.valueFormatter && typeof root.valueFormatter === "function") {
                            return root.valueFormatter(modelData.value)
                        }
                        return modelData.value.toString()
                    }
                    font.weight: Font.DemiBold
                }
            }
        }
        
        // Total row for stacked chart 堆叠图总计行
        Row {
            spacing: Enums.spacing.s
            visible: root.showTotal
            
            Item {
                width: Enums.spacing.s
                height: parent.height
            }
            Label {
                type: Enums.label.type_caption
                text: "Total"
                color: Enums.textColor.secondary
                width: 60
            }
            Label {
                type: Enums.label.type_caption
                text: {
                    if (root.valueFormatter && typeof root.valueFormatter === "function") {
                        return root.valueFormatter(root.totalValue)
                    }
                    return root.totalValue.toString()
                }
                font.weight: Font.DemiBold
            }
        }
    }
}
