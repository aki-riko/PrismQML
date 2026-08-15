// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../../effects"
import "../../../data"
import "ChartAxisLayout.js" as ChartAxisLayout

// XYChartAxes - XY chart grid and axis visuals XY图表网格与坐标轴视觉层
Item {
    id: axesLayer

    // ==================== Required Props 必需属性 ====================
    required property var chartControl
    required property var axisFontMetrics

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: chartControl
    readonly property Item chartArea: chartAreaItem

    anchors.fill: parent

    // Chart area 图表区域
    Item {
        id: chartAreaItem

        x: control.isHorizontal ? control.effectiveYAxisLabelWidth + Enums.spacing.xl
                                : control.effectiveYAxisLabelWidth
        y: control.title !== ""
           ? Enums.spacing.xxxl + Enums.spacing.xl : Enums.spacing.xxxl
        width: control.isHorizontal
               ? control.width - control.effectiveYAxisLabelWidth
                 - Enums.spacing.xxxl - Enums.spacing.l
               : control.width - control.effectiveYAxisLabelWidth - Enums.spacing.xl
        height: control.height - y
                - (control.showLabels
                   ? Enums.controlSize.chartXAxisHeight + Enums.spacing.m
                   : Enums.spacing.l)
                - (control.isScatter ? Enums.spacing.xxxl : 0)
                - (control.showLegend && control.series.length > 0
                   ? Enums.spacing.xxxl : 0)
    }

    // Grid lines (Fluent Design) 网格线（Fluent Design）
    Item {
        id: gridLines

        anchors.fill: chartAreaItem
        visible: control._showGridLines

        // Horizontal grid lines - light and subtle 水平网格线 - 轻量简洁
        Repeater {
            model: control._showGridLines ? 5 : 0

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
            y: control.zeroLineRatio * gridLines.height
            width: gridLines.width
            height: Enums.border.thin
            color: Enums.textColor.tertiary
            visible: control.valueRange.hasNegative && control.valueRange.hasPositive
                     && !control.isScatter
        }

        // Vertical grid lines for horizontal bar chart 水平柱状图的垂直网格线
        Repeater {
            model: control._showGridLines && control.isHorizontal ? 5 : 0

            Rectangle {
                x: index * (gridLines.width / 4)
                y: 0
                width: Enums.border.thin
                height: gridLines.height
                color: Enums.chartColors.gridLine
            }
        }
    }

    // Y-axis labels Y轴标签
    Item {
        id: yAxisLabels

        x: 0
        y: chartAreaItem.y
        width: control.effectiveYAxisLabelWidth - Enums.spacing.s
        height: chartAreaItem.height
        visible: control._showVerticalValueAxis

        Repeater {
            model: control._showVerticalValueAxis ? 5 : 0

            Label {
                x: 0
                y: index * (yAxisLabels.height / 4) - Enums.spacing.xs
                width: yAxisLabels.width
                type: Enums.label.type_caption
                text: control._verticalValueAxisLabels[index] || ""
                color: Enums.chartColors.axisLabel
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideLeft
            }
        }
    }

    // Y-axis labels for horizontal bar 水平柱状图Y轴标签（分类）
    Item {
        id: horizontalYAxisLabels
        objectName: "chartHorizontalYAxisViewport"

        x: Enums.spacing.s
        y: chartAreaItem.y
        width: control.effectiveYAxisLabelWidth - Enums.spacing.s
        height: chartAreaItem.height
        visible: control._showHorizontalAxes
        clip: true

        Repeater {
            model: control._showHorizontalAxes ? control.chartData : []

            Item {
                y: control._categorySlotPosition(index, horizontalYAxisLabels.height)
                width: parent.width
                height: control._categorySlotExtent(horizontalYAxisLabels.height)
                visible: control._categorySlotIntersectsViewport(index)

                Label {
                    anchors.fill: parent
                    type: Enums.label.type_caption
                    text: control._categoryLabelTexts[index] || ""
                    color: control.hoveredIndex === index
                           ? Enums.textColor.primary : Enums.textColor.tertiary
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    rightPadding: Enums.spacing.s

                    HoverBehavior on color {
                        active: control.hoveredIndex === index
                        enterDuration: Enums.duration.fast
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: !control.viewportTransitionActive
                        onEntered: control.xLabelHovered(index)
                        onExited: control.xLabelHovered(-1)
                    }
                }
            }
        }
    }

    // X-axis labels for horizontal bar 水平柱状图X轴标签（数值）
    Item {
        id: horizontalXAxisLabels

        x: chartAreaItem.x
        y: chartAreaItem.y + chartAreaItem.height + Enums.spacing.xs
        width: chartAreaItem.width
        height: Enums.controlSize.chartXAxisHeight
        visible: control._showHorizontalAxes
        clip: true

        Repeater {
            model: control._showHorizontalAxes ? 5 : 0

            Label {
                x: ChartAxisLayout.clampedCenteredX(
                    index * (parent.width / 4), width, parent.width
                )
                type: Enums.label.type_caption
                text: control._horizontalValueAxisLabels[index] || ""
                color: Enums.textColor.tertiary
            }
        }
    }

    // X-axis labels (category) X轴标签（分类）
    Item {
        id: xAxisLabels
        objectName: "chartXAxisViewport"

        x: chartAreaItem.x
        y: chartAreaItem.y + chartAreaItem.height + Enums.spacing.xs
        width: chartAreaItem.width
        height: Enums.controlSize.chartXAxisHeight
        visible: control._showVerticalCategoryAxis
        clip: true

        Repeater {
            model: control._showVerticalCategoryAxis ? control.chartData : []

            Item {
                x: control._categorySlotPosition(index, xAxisLabels.width)
                width: control._categorySlotWidth
                height: parent.height
                visible: control._categorySlotIntersectsViewport(index)

                Label {
                    id: categoryLabel

                    x: ChartAxisLayout.clampedCenteredX(
                        parent.x + parent.width / 2,
                        width,
                        xAxisLabels.width
                    ) - parent.x
                    width: ChartAxisLayout.categoryLabelWidth(
                        axisFontMetrics,
                        text,
                        control._categorySlotWidth,
                        control._categoryLabelStride,
                        Enums.spacing.m,
                        xAxisLabels.width
                    )
                    type: Enums.label.type_caption
                    visible: ChartAxisLayout.categoryLabelVisible(
                        index, control.chartData.length, control._categoryLabelStride
                    )
                    text: control._categoryLabelTexts[index] || ""
                    color: control.hoveredIndex === index
                           ? Enums.textColor.primary : Enums.textColor.tertiary
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight

                    HoverBehavior on color {
                        active: control.hoveredIndex === index
                        enterDuration: Enums.duration.fast
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: !control.viewportTransitionActive
                        onEntered: control.xLabelHovered(index)
                        onExited: control.xLabelHovered(-1)
                    }
                }
            }
        }
    }

    // X-axis labels (numeric for scatter) X轴标签（散点图数值）
    Item {
        id: scatterXAxisLabels
        objectName: "chartScatterXAxisViewport"

        x: chartAreaItem.x
        y: chartAreaItem.y + chartAreaItem.height + Enums.spacing.xs
        width: chartAreaItem.width
        height: Enums.controlSize.chartXAxisHeight
        visible: control._showScatterXAxis
        clip: true

        Item {
            id: scatterXAxisLayer

            x: control.viewportOffsetRatio * parent.width
            width: parent.width
            height: parent.height
            transform: Scale {
                origin.x: 0
                origin.y: 0
                xScale: control.viewportScale
            }

            Repeater {
                model: control._showScatterXAxis ? 6 : 0

                Label {
                    x: ChartAxisLayout.clampedCenteredX(
                        index * (parent.width / 5), width, parent.width
                    )
                    type: Enums.label.type_caption
                    text: control._scatterXAxisLabelTexts[index] || ""
                    color: Enums.textColor.secondary
                }
            }
        }
    }
}
