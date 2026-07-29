// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ChartPanArea - Chart viewport panning interaction 图表视窗平移交互
MouseArea {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var chart: null

    // ==================== Internal Props 内部属性 ====================
    property real _pressX: 0
    property real _pressVS: 0
    property real _pressVE: 0

    enabled: chart && chart.panEnabled && chart._isXYChart
    acceptedButtons: Qt.LeftButton
    cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
    propagateComposedEvents: true
    onPressed: (mouse) => {
        if (!chart) return
        _pressX = mouse.x
        _pressVS = chart._visualStart
        _pressVE = chart._visualEnd
        chart._viewportInteractive = true
    }
    onReleased: {
        if (chart) chart._viewportInteractive = false
    }
    onCanceled: {
        if (chart) chart._viewportInteractive = false
    }
    onPositionChanged: (mouse) => {
        if (!chart || !pressed || width <= 0) return
        var dx = mouse.x - _pressX
        var span = _pressVE - _pressVS
        var deltaRatio = -dx / width * span
        var nextStart = _pressVS + deltaRatio
        var nextEnd = _pressVE + deltaRatio
        if (nextStart < 0) { nextStart = 0; nextEnd = span }
        if (nextEnd > 1) { nextEnd = 1; nextStart = 1 - span }
        chart.viewportStart = nextStart
        chart.viewportEnd = nextEnd
        chart.viewportChanged(nextStart, nextEnd)
    }
}
