// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data/Label"
import "BarChartGeometry.js" as Geometry

// BarChartMarkers - Multi-series extrema markers outside plot clipping 多系列极值标记（脱离绘图区裁剪）
Item {
    id: root

    required property var chartContent
    required property var series
    required property bool showMinMax
    required property var getSeriesColor

    function _pointFor(position) {
        if (!chartContent || !position) return Qt.point(0, 0)
        return chartContent.mapToItem(root, position.x, position.barTop)
    }

    function _findMinMax(values) {
        return Geometry.findMinMaxIndices(values)
    }

    // Min/max bubble markers 最大最小值气泡标记
    Repeater {
        model: root.showMinMax ? root.series : []

        Item {
            id: markerItem

            property int seriesIdx: index
            property var values: modelData.values || []
            property var minMax: root._findMinMax(values)
            property color seriesColor: root.getSeriesColor(index)

            anchors.fill: parent

            // Max marker (above bar) 最大值标记（柱子上方）
            Rectangle {
                id: maxMarker
                objectName: "barMaxMarker_" + index
                visible: markerItem.minMax.maxIdx >= 0 && root.chartContent.barPositions.length > markerItem.seriesIdx
                x: {
                    if (!visible || !root.chartContent.barPositions[markerItem.seriesIdx]) return 0
                    var point = root._pointFor(
                        root.chartContent.barPositions[markerItem.seriesIdx][markerItem.minMax.maxIdx]
                    )
                    return point.x - width / 2
                }
                y: {
                    if (!visible || !root.chartContent.barPositions[markerItem.seriesIdx]) return 0
                    var point = root._pointFor(
                        root.chartContent.barPositions[markerItem.seriesIdx][markerItem.minMax.maxIdx]
                    )
                    return Math.max(0, point.y - height - 6)
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
                    type: Enums.label.type_caption
                    anchors.centerIn: parent
                    text: markerItem.minMax.maxVal !== undefined ? markerItem.minMax.maxVal.toString() : ""
                    font.weight: Font.DemiBold
                    color: Enums.chartColors.markerText
                }
            }

            // Min marker (below bar or at bottom) 最小值标记
            Rectangle {
                id: minMarker
                objectName: "barMinMarker_" + index
                visible: markerItem.minMax.minIdx >= 0 && root.chartContent.barPositions.length > markerItem.seriesIdx
                x: {
                    if (!visible || !root.chartContent.barPositions[markerItem.seriesIdx]) return 0
                    var point = root._pointFor(
                        root.chartContent.barPositions[markerItem.seriesIdx][markerItem.minMax.minIdx]
                    )
                    return point.x - width / 2
                }
                y: {
                    if (!visible || !root.chartContent.barPositions[markerItem.seriesIdx]) return 0
                    var point = root._pointFor(
                        root.chartContent.barPositions[markerItem.seriesIdx][markerItem.minMax.minIdx]
                    )
                    return Math.min(root.height - height, point.y + height + 6)
                }
                width: minLabel.width + Enums.spacing.l
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
                    id: minLabel
                    type: Enums.label.type_caption
                    anchors.centerIn: parent
                    text: markerItem.minMax.minVal !== undefined ? markerItem.minMax.minVal.toString() : ""
                    font.weight: Font.DemiBold
                    color: Enums.chartColors.markerText
                }
            }
        }
    }

}
