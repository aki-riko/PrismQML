// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import "../../inputs/Slider"

// ChartDataZoom - Dual-handle viewport selector 双手柄视窗范围选择器
// The canvas renders a full-data thumbnail without depending on ChartView Canvas 绘制全量缩略图且不依赖 ChartView
// SliderCore provides the range handles SliderCore 提供范围双手柄
//
// Usage 用法:
//   ChartDataZoom {
//       chartData: chartWidget.chartData
//       series: chartWidget.series
//       primaryColor: chartWidget.primaryColor
//       viewportStart: chartWidget.viewportStart
//       viewportEnd: chartWidget.viewportEnd
//       onViewportChanged: (s, e) => {
//           chartWidget.viewportStart = s
//           chartWidget.viewportEnd = e
//       }
//   }

Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Full data used by the thumbnail renderer 缩略图渲染使用的全量数据
    property var chartData: []
    property var series: []
    property color primaryColor: Enums.accentColor

    // Current selected range 当前选中范围
    property real viewportStart: 0
    property real viewportEnd: 1

    // ==================== Internal Props 内部属性 ====================
    property bool _suppressSliderUpdate: false
    property bool _dragging: false
    readonly property int _panelRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.small
    readonly property color _panelColor: Enums.isPrismDesign ? Enums.surfaceColor : Enums.transparent
    readonly property color _panelBorderColor: Enums.isPrismDesign ? Enums.borderLightColor : Enums.transparent
    readonly property int _thumbnailMargin: Enums.isPrismDesign ? Enums.spacing.xs : Enums.spacing.none
    readonly property int _sliderSpace: Enums.spacing.m
    readonly property int _thumbnailStrokeWidth: Enums.border.thin
    readonly property real _thumbnailFillAlpha: Enums.isPrismDesign ? Enums.stateColor.chartFillMedium : Enums.opacityLevel.light - Enums.opacityLevel.faint
    readonly property real _thumbnailStrokeAlpha: Enums.isPrismDesign ? Enums.stateColor.chartStrokeAlpha : Enums.opacityLevel.strong
    readonly property real _safeViewportStart: _normalizeViewport(viewportStart, 0)
    readonly property real _safeViewportEnd: _normalizeViewport(viewportEnd, 1)

    // ==================== Signals 信号 ====================
    signal viewportChanged(real start, real end)
    // Notify the parent about direct manipulation so transitions can pause 通知父级直接拖动状态以暂停过渡
    signal interactiveChanged(bool active)

    // ==================== Internal Methods 内部方法 ====================
    function _normalizeViewport(value, fallback) {
        return typeof value === "number" && isFinite(value)
                ? Math.max(0, Math.min(1, value)) : fallback
    }

    implicitWidth: Enums.controlSize.chartDataZoomDefaultWidth
    implicitHeight: Enums.controlSize.chartDataZoomDefaultHeight

    onChartDataChanged: if (thumbCanvas) thumbCanvas.requestPaint()
    onSeriesChanged: if (thumbCanvas) thumbCanvas.requestPaint()
    onViewportStartChanged: {
        if (!rangeSlider) return
        _suppressSliderUpdate = true
        rangeSlider.firstValue = Math.round(_normalizeViewport(viewportStart, 0)
                                            * Enums.chart.viewport_slider_steps)
        _suppressSliderUpdate = false
    }
    onViewportEndChanged: {
        if (!rangeSlider) return
        _suppressSliderUpdate = true
        rangeSlider.secondValue = Math.round(_normalizeViewport(viewportEnd, 1)
                                             * Enums.chart.viewport_slider_steps)
        _suppressSliderUpdate = false
    }

    Rectangle {
        anchors.fill: parent
        radius: control._panelRadius
        color: control._panelColor
        border.width: Enums.isPrismDesign ? Enums.border.thin : Enums.border.none
        border.color: control._panelBorderColor
    }

    // Render the leading series as the full-data thumbnail 将主序列绘制为全量数据缩略图
    Canvas {
        id: thumbCanvas

        property var _drawValues: {
            var source = []
            var series = control.series
            if (series && typeof series.length === "number" && series.length > 0) {
                var first = series[0]
                if (first && first.values && typeof first.values.length === "number") {
                    source = first.values
                }
            }
            if (source.length === 0) {
                var chartData = control.chartData
                if (chartData && typeof chartData.length === "number") {
                    for (var i = 0; i < chartData.length; i++) {
                        var item = chartData[i]
                        source.push(item && item.value !== undefined ? item.value : 0)
                    }
                }
            }
            return _normalizeValues(source)
        }

        function _normalizeValues(values) {
            var normalized = []
            if (!values || typeof values.length !== "number") return normalized
            for (var i = 0; i < values.length; i++) {
                var value = values[i]
                normalized.push(typeof value === "number" && isFinite(value) ? value : 0)
            }
            return normalized
        }

        anchors.fill: parent
        anchors.margins: control._thumbnailMargin
        anchors.bottomMargin: control._sliderSpace  // Reserve space for the slider 为滑块预留空间

        onPaint: {
            var ctx = getContext('2d')
            ctx.clearRect(0, 0, width, height)
            var vals = _drawValues
            if (!vals || vals.length === 0) return
            // Resolve the vertical data range 计算纵向数据范围
            var minV = vals[0], maxV = vals[0]
            for (var i = 1; i < vals.length; i++) {
                if (vals[i] < minV) minV = vals[i]
                if (vals[i] > maxV) maxV = vals[i]
            }
            var range = maxV - minV || 1
            var n = vals.length
            // Downsample to at most one point per pixel 每个像素最多保留一个点
            var maxPoints = Math.min(n, Math.max(1, Math.floor(width)))
            var step = n / maxPoints
            ctx.beginPath()
            for (var k = 0; k < maxPoints; k++) {
                var idx = Math.floor(k * step)
                var x = (k / (maxPoints - 1 || 1)) * width
                var y = height - ((vals[idx] - minV) / range) * height
                if (k === 0) ctx.moveTo(x, y)
                else ctx.lineTo(x, y)
            }
            // Fill the translucent area 填充半透明区域
            ctx.lineTo(width, height)
            ctx.lineTo(0, height)
            ctx.closePath()
            ctx.fillStyle = Qt.rgba(control.primaryColor.r, control.primaryColor.g,
                                     control.primaryColor.b, control._thumbnailFillAlpha)
            ctx.fill()
            // Draw the thumbnail line 绘制缩略折线
            ctx.beginPath()
            for (var k2 = 0; k2 < maxPoints; k2++) {
                var idx2 = Math.floor(k2 * step)
                var x2 = (k2 / (maxPoints - 1 || 1)) * width
                var y2 = height - ((vals[idx2] - minV) / range) * height
                if (k2 === 0) ctx.moveTo(x2, y2)
                else ctx.lineTo(x2, y2)
            }
            ctx.strokeStyle = Qt.rgba(control.primaryColor.r, control.primaryColor.g,
                                       control.primaryColor.b, control._thumbnailStrokeAlpha)
            ctx.lineWidth = control._thumbnailStrokeWidth
            ctx.stroke()
        }

        Component.onCompleted: requestPaint()
    }

    // Overlay the dual-handle range slider on the thumbnail 将双手柄范围滑块叠加在缩略图上
    SliderCore {
        id: rangeSlider
        anchors.fill: parent
        type: Enums.slider.type_range
        from: 0
        to: Enums.chart.viewport_slider_steps
        firstValue: Math.round(control._safeViewportStart * Enums.chart.viewport_slider_steps)
        secondValue: Math.round(control._safeViewportEnd * Enums.chart.viewport_slider_steps)

        onSliderMoved: (first, second) => {
            if (control._suppressSliderUpdate) return
            // Pause parent transitions while the user drags 用户拖动时暂停父级过渡
            if (!control._dragging) {
                control._dragging = true
                control.interactiveChanged(true)
                // Treat an idle interval as drag completion 一段时间无输入后视为拖动结束
                _dragEndTimer.restart()
            } else {
                _dragEndTimer.restart()
            }
            var lo = Math.min(first, second) / Enums.chart.viewport_slider_steps
            var hi = Math.max(first, second) / Enums.chart.viewport_slider_steps
            if (hi - lo < Enums.chart.minimum_viewport_span) {
                hi = Math.min(1, lo + Enums.chart.minimum_viewport_span)
                lo = Math.max(0, hi - Enums.chart.minimum_viewport_span)
            }
            control.viewportChanged(lo, hi)
        }
    }
    Timer {
        id: _dragEndTimer
        interval: Enums.duration.slow
        repeat: false
        onTriggered: {
            control._dragging = false
            control.interactiveChanged(false)
        }
    }
}
