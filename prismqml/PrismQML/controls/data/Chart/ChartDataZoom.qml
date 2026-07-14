// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import "../../inputs/Slider"

// ChartDataZoom — 双手柄区域缩放选择器
// 上层缩略图: Canvas 自画全量轮廓 (避免引用 ChartView 触发循环依赖)
// 下层叠 SliderCore type_range 双手柄做范围选择
//
// 用法:
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
    // 全量数据 — 用来画缩略图轮廓
    property var chartData: []
    property var series: []
    property color primaryColor: Enums.accentColor

    // 当前选中范围 (0..1)
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

    // ==================== Signals 信号 ====================
    signal viewportChanged(real start, real end)
    // 用户开始/结束拖动手柄 — 父级监听后关闭 viewport 动画避免每帧卡
    signal interactiveChanged(bool active)

    implicitWidth: 400
    implicitHeight: 60

    Rectangle {
        anchors.fill: parent
        radius: control._panelRadius
        color: control._panelColor
        border.width: Enums.isPrismDesign ? Enums.border.thin : Enums.border.none
        border.color: control._panelBorderColor
    }

    // 缩略图: Canvas 自画全量轮廓 (主导 series 取 chartData[i].value 或 series[0].values)
    Canvas {
        id: thumbCanvas

        property var _drawValues: {
            if (control.series && control.series.length > 0) {
                return control.series[0].values || []
            }
            if (control.chartData && control.chartData.length > 0) {
                var out = []
                for (var i = 0; i < control.chartData.length; i++) {
                    var it = control.chartData[i]
                    out.push(it && it.value !== undefined ? it.value : 0)
                }
                return out
            }
            return []
        }

        anchors.fill: parent
        anchors.margins: control._thumbnailMargin
        anchors.bottomMargin: control._sliderSpace  // 给底部 slider 留空间

        onPaint: {
            var ctx = getContext('2d')
            ctx.clearRect(0, 0, width, height)
            var vals = _drawValues
            if (!vals || vals.length === 0) return
            // Y 范围
            var minV = vals[0], maxV = vals[0]
            for (var i = 1; i < vals.length; i++) {
                if (vals[i] < minV) minV = vals[i]
                if (vals[i] > maxV) maxV = vals[i]
            }
            var range = maxV - minV || 1
            var n = vals.length
            // 把点抽稀到画布宽度: 1 像素 1 个点 max
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
            // 填充半透明 area
            ctx.lineTo(width, height)
            ctx.lineTo(0, height)
            ctx.closePath()
            ctx.fillStyle = Qt.rgba(control.primaryColor.r, control.primaryColor.g,
                                     control.primaryColor.b, control._thumbnailFillAlpha)
            ctx.fill()
            // 折线
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

        // 数据变化时重画
        Connections {
            target: control
            function onChartDataChanged() { thumbCanvas.requestPaint() }
            function onSeriesChanged()    { thumbCanvas.requestPaint() }
        }
        Component.onCompleted: requestPaint()
    }

    // 双手柄 RangeSlider 叠在缩略图上
    SliderCore {
        id: rangeSlider
        anchors.fill: parent
        type: Enums.slider.type_range
        from: 0
        to: 1000  // 0..1000 整数刻度避免浮点抖动
        firstValue: Math.round(control.viewportStart * 1000)
        secondValue: Math.round(control.viewportEnd * 1000)

        onSliderMoved: (first, second) => {
            if (control._suppressSliderUpdate) return
            // 标记用户在拖动中, 父 ChartView 关 viewport 动画
            if (!control._dragging) {
                control._dragging = true
                control.interactiveChanged(true)
                // 250ms 内无新 sliderMoved 视为拖完
                _dragEndTimer.restart()
            } else {
                _dragEndTimer.restart()
            }
            var lo = Math.min(first, second) / 1000
            var hi = Math.max(first, second) / 1000
            if (hi - lo < 0.001) hi = lo + 0.001  // 防止两手柄重合
            control.viewportChanged(lo, hi)
        }
    }
    Timer {
        id: _dragEndTimer
        interval: 250
        repeat: false
        onTriggered: {
            control._dragging = false
            control.interactiveChanged(false)
        }
    }

    // 外部改 viewportStart/End 时反向同步 slider 手柄位置 (防 onSliderMoved 反弹)
    Connections {
        target: control
        function onViewportStartChanged() {
            control._suppressSliderUpdate = true
            rangeSlider.firstValue = Math.round(control.viewportStart * 1000)
            control._suppressSliderUpdate = false
        }
        function onViewportEndChanged() {
            control._suppressSliderUpdate = true
            rangeSlider.secondValue = Math.round(control.viewportEnd * 1000)
            control._suppressSliderUpdate = false
        }
    }
}
