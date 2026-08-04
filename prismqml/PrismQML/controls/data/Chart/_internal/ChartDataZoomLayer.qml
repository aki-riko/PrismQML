// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ChartDataZoomLayer - Lazy bottom viewport selector 延迟创建的底部图表视窗选择器
Loader {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var chart: null

    // ==================== Readonly State 只读状态 ====================
    readonly property bool shouldLoad: chart && chart.dataZoomEnabled && chart._isXYChart

    // ==================== Internal Methods 内部方法 ====================
    function ensureLoaded() {
        if (shouldLoad) active = true
    }

    anchors.left: parent ? parent.left : undefined
    anchors.right: parent ? parent.right : undefined
    anchors.bottom: parent ? parent.bottom : undefined
    anchors.leftMargin: Enums.spacing.m
    anchors.rightMargin: Enums.spacing.m
    anchors.bottomMargin: Enums.spacing.s
    height: Enums.controlSize.chartDataZoomBarHeight
    active: false
    onShouldLoadChanged: ensureLoaded()
    Component.onCompleted: ensureLoaded()

    // ==================== Content 内容 ====================
    sourceComponent: Component {
        ChartDataZoom {
            anchors.fill: parent
            visible: root.chart && root.chart.dataZoomEnabled && root.chart._isXYChart
            chartData: root.chart ? root.chart._chartData : []
            series: root.chart ? root.chart._series : []
            primaryColor: root.chart ? root.chart.primaryColor : Enums.accentColor
            viewportStart: root.chart ? root.chart._visualStart : 0
            viewportEnd: root.chart ? root.chart._visualEnd : 1
            onViewportChanged: (start, end) => {
                if (!root.chart) return
                root.chart.viewportStart = start
                root.chart.viewportEnd = end
                root.chart.viewportChanged(start, end)
            }
            onInteractiveChanged: (active) => {
                if (root.chart) root.chart._viewportInteractive = active
            }
        }
    }
}
