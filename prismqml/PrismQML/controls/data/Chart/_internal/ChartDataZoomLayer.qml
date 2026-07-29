// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ChartDataZoomLayer - Bottom viewport selector 底部图表视窗选择器
ChartDataZoom {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var chart: null

    anchors.left: parent ? parent.left : undefined
    anchors.right: parent ? parent.right : undefined
    anchors.bottom: parent ? parent.bottom : undefined
    anchors.leftMargin: Enums.spacing.m
    anchors.rightMargin: Enums.spacing.m
    anchors.bottomMargin: Enums.spacing.s
    height: Enums.controlSize.chartDataZoomBarHeight
    visible: chart && chart.dataZoomEnabled && chart._isXYChart
    chartData: chart ? chart._chartData : []
    series: chart ? chart._series : []
    primaryColor: chart ? chart.primaryColor : Enums.accentColor
    viewportStart: chart ? chart._visualStart : 0
    viewportEnd: chart ? chart._visualEnd : 1
    onViewportChanged: (start, end) => {
        if (!chart) return
        chart.viewportStart = start
        chart.viewportEnd = end
        chart.viewportChanged(start, end)
    }
    onInteractiveChanged: (active) => {
        if (chart) chart._viewportInteractive = active
    }
}
