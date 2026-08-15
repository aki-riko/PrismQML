// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data/Label"
import "BarChartGeometry.js" as Geometry
import "BarChartPainter.js" as Painter

// BarChartContent - Multi-series bar chart rendering component 多系列柱状图渲染组件
// Supports markPoint (min/max bubbles) and markLine (average dashed line)
// 支持 markPoint(最大最小值气泡) 和 markLine(平均值虚线)

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var chartData      // [{label: "", value: 0, color: ""}, ...] - single series 单系列
    required property real maxValue      // Maximum value Y轴最大值
    required property bool animated      // Enable animation 启用动画
    required property bool showValues    // Show value labels 显示数值标签
    required property var getColor       // Function to get color 获取颜色函数
    
    // ==================== Public Props 公开属性 ====================
    property var series: []              // [{name: "", values: [], color: ""}, ...] - multi series 多系列
    property int hoveredIndex: -1
    property int hoveredSeriesIndex: -1
    property bool isHorizontal: false    // Horizontal bar chart 水平柱状图
    property var valueRange: ({ min: 0, max: maxValue, hasNegative: false, hasPositive: true })
    property real zeroLineRatio: 1.0     // Zero line position (0-1) 零轴线位置
    property bool showAverage: false     // Show average line (markLine) 显示平均线
    property bool showMinMax: false      // Show min/max markers (markPoint) 显示最大最小值标记
    property bool showBarGradient: false // Show gradient fill on bars 柱子渐变填充

    // ==================== Internal Props 内部属性 ====================
    property var barPositions: []        // For markPoint positioning 用于markPoint定位
    property int _lastHoverCandidateCount: 0
    property var _barGeometry: null
    property bool _barGeometryDirty: true
    property int _barGeometryBuildCount: 0
    property int _lastFrameBarUpdateCount: 0
    property real _lastBarGeometryProgress: -1
    property int _lastFrameBarDrawCount: 0
    property int _paintedHoverIndex: -1
    property int _paintedHoverSeriesIndex: -1

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isMultiSeries: series.length > 0
    readonly property int dataLength: isMultiSeries ? (series[0].values ? series[0].values.length : 0) : chartData.length
    readonly property real _barHoverRadius: 30
    readonly property var computedValueRange: {
        var min = 0, max = 0
        if (isMultiSeries) {
            for (var s = 0; s < series.length; s++) {
                var vals = series[s].values || []
                for (var i = 0; i < vals.length; i++) {
                    if (vals[i] < min) min = vals[i]
                    if (vals[i] > max) max = vals[i]
                }
            }
        } else {
            for (var j = 0; j < chartData.length; j++) {
                var v = chartData[j].value || 0
                if (v < min) min = v
                if (v > max) max = v
            }
        }
        var padding = (max - min) * 0.1 || 1
        return { min: Math.min(min, 0), max: max + padding }
    }

    // ==================== Signals 信号 ====================
    signal barClicked(int index, var data)
    signal barHovered(int index)
    signal seriesBarHovered(int seriesIndex, int barIndex)

    // ==================== Internal Methods 内部方法 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function calculateAverage(values) {
        return Geometry.average(values)
    }
    
    function findMinMaxIndices(values) {
        return Geometry.findMinMaxIndices(values)
    }
    
    function valueToY(value) {
        var range = computedValueRange.max - computedValueRange.min
        if (range === 0) return height / 2
        return height - ((value - computedValueRange.min) / range) * height
    }
    
    function getBarRatio(value) {
        var range = computedValueRange.max - computedValueRange.min
        if (range === 0) return 0
        return Math.abs(value) / range
    }
    
    function isPositive(value) {
        return value >= 0
    }

    function _nearestBarHit(x, y) {
        var hit = Geometry.nearestBarHit(barPositions, x, y, _barHoverRadius)
        _lastHoverCandidateCount = hit.candidateCount
        return { barIndex: hit.barIndex, seriesIndex: hit.seriesIndex }
    }

    function _rebuildBarGeometry(canvasWidth, canvasHeight) {
        var range = computedValueRange
        var geometry = Geometry.build(
            series, dataLength, canvasWidth, canvasHeight, range.min, range.max
        )
        _barGeometry = geometry
        if (geometry.dataLength > 0) barPositions = geometry.seriesPositions
        _barGeometryDirty = false
        _lastBarGeometryProgress = -1
        _barGeometryBuildCount++
    }

    function _updateAnimatedBarGeometry(progress) {
        if (_barGeometryDirty) _rebuildBarGeometry(width, height)
        if (progress === _lastBarGeometryProgress) {
            _lastFrameBarUpdateCount = 0
            return
        }
        _lastFrameBarUpdateCount = Geometry.update(
            _barGeometry.seriesPositions, progress, _barGeometry.baseline
        )
        _lastBarGeometryProgress = progress
        if (_lastFrameBarUpdateCount > 0) barPositionsChanged()
    }

    function _invalidateBarGeometry() {
        _barGeometryDirty = true
        canvas.requestPaint()
    }

    function _requestMultiHoverPaint() {
        if (_barGeometryDirty || (animated && canvas.animProgress < 1)) {
            canvas.requestPaint()
            return
        }
        var previousPosition = Geometry.barPosition(
            barPositions, _paintedHoverSeriesIndex, _paintedHoverIndex
        )
        var currentPosition = Geometry.barPosition(
            barPositions, hoveredSeriesIndex, hoveredIndex
        )
        var barWidth = _barGeometry ? _barGeometry.barWidth : 0
        var dirtyBounds = Geometry.unitedBounds(
            Geometry.dirtyBounds(previousPosition, barWidth, width, height, Enums.border.thin),
            Geometry.dirtyBounds(currentPosition, barWidth, width, height, Enums.border.thin)
        )
        if (dirtyBounds && dirtyBounds.width > 0 && dirtyBounds.height > 0) {
            canvas.markDirty(Qt.rect(
                dirtyBounds.x, dirtyBounds.y,
                dirtyBounds.width, dirtyBounds.height
            ))
        }
    }

    // Repaint triggers 重绘触发
    onHoveredIndexChanged: {
        if (isMultiSeries && !isHorizontal) _requestMultiHoverPaint()
        if (!isMultiSeries && !isHorizontal) singleBarIndicator.requestPaint()
    }
    onHoveredSeriesIndexChanged: {
        if (isMultiSeries && !isHorizontal) _requestMultiHoverPaint()
    }
    onSeriesChanged: _invalidateBarGeometry()
    onShowAverageChanged: canvas.requestPaint()
    onShowBarGradientChanged: canvas.requestPaint()

    // ==================== Content 内容 ====================
    // Canvas for multi-series (Fluent Design) 多系列画布（Fluent Design）
    Canvas {
        id: canvas

        property real animProgress: root.animated ? 0 : 1

        function drawBars(ctx, region, fullPaint) {
            var geometry = root._barGeometry
            var barWidth = geometry.barWidth
            var allBarPositions = root.barPositions
            var drawCount = 0
            for (var seriesIndex = 0; seriesIndex < root.series.length; seriesIndex++) {
                var seriesData = root.series[seriesIndex]
                var values = seriesData.values || []
                var color = root.getSeriesColor(seriesIndex)
                drawCount += Painter.drawSeriesBars(
                    ctx, allBarPositions[seriesIndex], values, seriesIndex,
                    color, barWidth, region, fullPaint,
                    root.hoveredSeriesIndex, root.hoveredIndex,
                    Enums.radius.small
                )
                if (root.showAverage && values.length > 0) {
                    Painter.drawAverageLine(
                        ctx, geometry.averageYs[seriesIndex], color,
                        width, Enums.stateColor.chartStrokeAlpha
                    )
                }
            }
            root._lastFrameBarDrawCount = drawCount
        }

        anchors.fill: parent
        visible: root.isMultiSeries && !root.isHorizontal

        onPaint: (region) => {
            var ctx = getContext("2d")
            var fullPaint = root._barGeometryDirty || !region ||
                    (region.x <= 0 && region.y <= 0 &&
                     region.width >= width && region.height >= height)
            if (fullPaint) ctx.clearRect(0, 0, width, height)
            else ctx.clearRect(region.x, region.y, region.width, region.height)
            if (!root.isMultiSeries || root.series.length === 0 ||
                    root.dataLength === 0) {
                root._lastFrameBarDrawCount = 0
                return
            }
            root._updateAnimatedBarGeometry(root.animated ? animProgress : 1)
            if (!fullPaint) {
                ctx.save()
                ctx.beginPath()
                ctx.rect(region.x, region.y, region.width, region.height)
                ctx.clip()
            }
            drawBars(ctx, region, fullPaint)
            if (!fullPaint) ctx.restore()
            root._paintedHoverIndex = root.hoveredIndex
            root._paintedHoverSeriesIndex = root.hoveredSeriesIndex
        }
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                chartAnimation.restart()
            } else {
                requestPaint()
            }
        }
        onAnimProgressChanged: requestPaint()
        onWidthChanged: root._invalidateBarGeometry()
        onHeightChanged: root._invalidateBarGeometry()
        onVisibleChanged: if (visible) root._invalidateBarGeometry()
        
        NumberAnimation {
            id: chartAnimation
            target: canvas
            property: "animProgress"
            from: 0
            to: 1
            duration: Enums.duration.chart
            easing.type: Easing.OutQuint
        }
    }
    
    // Min/max bubble markers 最大最小值气泡标记
    Repeater {
        model: root.isMultiSeries && root.showMinMax ? root.series : []
        
        Item {
            id: markerItem

            property int seriesIdx: index
            property var values: modelData.values || []
            property var minMax: root.findMinMaxIndices(values)
            property color seriesColor: root.getSeriesColor(index)

            anchors.fill: parent

            // Max marker (above bar) 最大值标记（柱子上方）
            Rectangle {
                id: maxMarker
                visible: markerItem.minMax.maxIdx >= 0 && root.barPositions.length > markerItem.seriesIdx
                x: {
                    if (!visible || !root.barPositions[markerItem.seriesIdx]) return 0
                    return root.barPositions[markerItem.seriesIdx][markerItem.minMax.maxIdx].x - width/2
                }
                y: {
                    if (!visible || !root.barPositions[markerItem.seriesIdx]) return 0
                    return root.barPositions[markerItem.seriesIdx][markerItem.minMax.maxIdx].barTop - height - 6
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
                visible: markerItem.minMax.minIdx >= 0 && root.barPositions.length > markerItem.seriesIdx
                x: {
                    if (!visible || !root.barPositions[markerItem.seriesIdx]) return 0
                    return root.barPositions[markerItem.seriesIdx][markerItem.minMax.minIdx].x - width/2
                }
                y: {
                    if (!visible || !root.barPositions[markerItem.seriesIdx]) return 0
                    return root.barPositions[markerItem.seriesIdx][markerItem.minMax.minIdx].barTop - height - 6
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
    
    // Average value labels (right side) 平均值标签（右侧）
    Repeater {
        model: root.isMultiSeries && root.showAverage ? root.series : []
        
        Label {
            property var values: modelData.values || []
            property real avg: root.calculateAverage(values)
            property color seriesColor: root.getSeriesColor(index)

            type: Enums.label.type_caption
            x: root.width + 4
            y: root.valueToY(avg) - height / 2
            text: avg.toFixed(1)
            color: seriesColor
            visible: values.length > 0
        }
    }

    // Single-series vertical bar chart 单系列垂直柱状图
    // Axis trigger indicator line for single series 单系列悬停指示线
    Canvas {
        id: singleBarIndicator
        anchors.fill: parent
        visible: !root.isMultiSeries && !root.isHorizontal && root.hoveredIndex >= 0
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            if (root.hoveredIndex < 0 || root.chartData.length === 0) return
            
            var barWidth = (width - root.chartData.length * Enums.spacing.s) / root.chartData.length
            var indicatorX = root.hoveredIndex * (barWidth + Enums.spacing.s) + barWidth / 2 + Enums.spacing.s / 2
            
            ctx.beginPath()
            ctx.strokeStyle = Enums.textColor.tertiary
            ctx.lineWidth = 1
            ctx.setLineDash([3, 3])
            ctx.moveTo(indicatorX, 0)
            ctx.lineTo(indicatorX, height)
            ctx.stroke()
            ctx.setLineDash([])
        }
    }
    
    Row {
        id: verticalBarRow
        anchors.fill: parent
        spacing: Enums.spacing.s
        visible: !root.isMultiSeries && !root.isHorizontal
        
        Repeater {
            model: !root.isMultiSeries && !root.isHorizontal ? root.chartData : []
            
            Item {
                id: verticalBarItem

                property bool hovered: root.hoveredIndex === index
                property real barValue: modelData && modelData.value !== undefined ? modelData.value : 0
                property bool isPositiveValue: root.isPositive(barValue)
                property real barRatio: root.getBarRatio(barValue)
                property real zeroY: root.zeroLineRatio * height

                width: (verticalBarRow.width - verticalBarRow.spacing * (root.chartData.length - 1)) / Math.max(root.chartData.length, 1)
                height: verticalBarRow.height

                // Fluent Design: simple bar with rounded top corners 简洁柱子+顶部圆角
                Canvas {
                    id: verticalBarRect

                    property color barColor: root.getColor(index)
                    property bool barHovered: verticalBarItem.hovered

                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.min(parent.width * 0.7, Enums.spacing.xxxl)
                    y: verticalBarItem.isPositiveValue ? verticalBarItem.zeroY - height : verticalBarItem.zeroY
                    height: root.animated ? 0 : verticalBarItem.barRatio * parent.height
                    
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        if (height <= 0) return
                        
                        var r = Math.min(Enums.radius.small, width / 2, height / 2)
                        
                        // Fluent Design: solid color with subtle hover lightening 纯色+微妙悬停变亮
                        ctx.fillStyle = barHovered ? Qt.lighter(barColor, 1.1) : barColor
                        
                        // Draw rounded rect (top corners only) 绘制圆角矩形（仅顶部圆角）
                        ctx.beginPath()
                        ctx.moveTo(r, 0)
                        ctx.lineTo(width - r, 0)
                        ctx.arcTo(width, 0, width, r, r)
                        ctx.lineTo(width, height)
                        ctx.lineTo(0, height)
                        ctx.lineTo(0, r)
                        ctx.arcTo(0, 0, r, 0, r)
                        ctx.closePath()
                        ctx.fill()
                    }
                    
                    onBarColorChanged: requestPaint()
                    onBarHoveredChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    
                    Behavior on height {
                        enabled: root.animated
                        NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutQuint }
                    }
                    
                    Component.onCompleted: {
                        if (root.animated) height = verticalBarItem.barRatio * parent.height
                    }
                }
                
                Label {
                    type: Enums.label.type_caption
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: verticalBarItem.isPositiveValue ? verticalBarRect.y - height - Enums.spacing.xs : verticalBarRect.y + verticalBarRect.height + Enums.spacing.xs
                    text: verticalBarItem.barValue
                    font.weight: verticalBarItem.hovered ? Font.DemiBold : Font.Normal
                    color: verticalBarItem.hovered ? Enums.textColor.primary : Enums.textColor.secondary
                    visible: root.showValues
                    HoverBehavior on color {
                        active: verticalBarItem.hovered
                        enterDuration: Enums.duration.fast
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: root.barHovered(index)
                    onExited: root.barHovered(-1)
                    onClicked: root.barClicked(index, modelData)
                }
            }
        }
    }

    // Single-series horizontal bar chart 单系列水平柱状图
    Column {
        id: horizontalBarColumn
        anchors.fill: parent
        spacing: Enums.spacing.xs
        visible: !root.isMultiSeries && root.isHorizontal
        
        Repeater {
            model: !root.isMultiSeries && root.isHorizontal ? root.chartData : []
            
            Item {
                id: horizontalBarItem

                property bool hovered: root.hoveredIndex === index
                property real barValue: modelData && modelData.value !== undefined ? modelData.value : 0
                property bool isPositiveValue: root.isPositive(barValue)
                property real barRatio: root.getBarRatio(barValue)
                property real zeroX: {
                    var range = root.valueRange
                    if (!range.hasNegative) return 0
                    if (!range.hasPositive) return width
                    return Math.abs(range.min) / (range.max - range.min) * width
                }

                width: horizontalBarColumn.width
                height: (horizontalBarColumn.height - horizontalBarColumn.spacing * (root.chartData.length - 1)) / Math.max(root.chartData.length, 1)

                // Fluent Design: simple horizontal bar 简洁水平柱子
                Canvas {
                    id: horizontalBarRect

                    property color barColor: root.getColor(index)
                    property bool barHovered: horizontalBarItem.hovered
                    property bool isPositive: horizontalBarItem.isPositiveValue

                    anchors.verticalCenter: parent.verticalCenter
                    height: Math.min(parent.height * 0.7, Enums.spacing.xxl)
                    x: horizontalBarItem.isPositiveValue ? horizontalBarItem.zeroX : horizontalBarItem.zeroX - width
                    width: root.animated ? 0 : horizontalBarItem.barRatio * parent.width
                    
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        if (width <= 0) return
                        
                        var r = Math.min(Enums.radius.small, width / 2, height / 2)
                        
                        // Fluent Design: solid color with subtle hover lightening 纯色+微妙悬停变亮
                        ctx.fillStyle = barHovered ? Qt.lighter(barColor, 1.1) : barColor
                        
                        // Horizontal gradient fill 水平渐变填充
                        var gradient = ctx.createLinearGradient(0, 0, width, 0)
                        if (isPositive) {
                            gradient.addColorStop(0, barHovered ? Qt.lighter(barColor, 1.05) : barColor)
                            gradient.addColorStop(1, barHovered ? Qt.lighter(barColor, 1.2) : Qt.lighter(barColor, 1.1))
                        } else {
                            gradient.addColorStop(0, barHovered ? Qt.lighter(barColor, 1.2) : Qt.lighter(barColor, 1.1))
                            gradient.addColorStop(1, barHovered ? Qt.lighter(barColor, 1.05) : barColor)
                        }
                        ctx.fillStyle = gradient
                        
                        // Draw rounded rect (end corners only) 绘制圆角矩形（仅末端圆角）
                        ctx.beginPath()
                        if (isPositive) {
                            // Right end rounded 右端圆角
                            ctx.moveTo(0, 0)
                            ctx.lineTo(width - r, 0)
                            ctx.arcTo(width, 0, width, r, r)
                            ctx.lineTo(width, height - r)
                            ctx.arcTo(width, height, width - r, height, r)
                            ctx.lineTo(0, height)
                            ctx.closePath()
                        } else {
                            // Left end rounded 左端圆角
                            ctx.moveTo(r, 0)
                            ctx.lineTo(width, 0)
                            ctx.lineTo(width, height)
                            ctx.lineTo(r, height)
                            ctx.arcTo(0, height, 0, height - r, r)
                            ctx.lineTo(0, r)
                            ctx.arcTo(0, 0, r, 0, r)
                            ctx.closePath()
                        }
                        ctx.fill()
                    }
                    
                    onBarColorChanged: requestPaint()
                    onBarHoveredChanged: requestPaint()
                    onWidthChanged: requestPaint()
                    
                    Behavior on width {
                        enabled: root.animated
                        NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutQuint }
                    }
                    
                    Component.onCompleted: {
                        if (root.animated) {
                            // Defer until layout is complete 延迟到布局完成后执行
                            Qt.callLater(function() {
                                horizontalBarRect.width = horizontalBarItem.barRatio * horizontalBarItem.width
                            })
                        }
                    }
                }
                
                Label {
                    type: Enums.label.type_caption
                    anchors.verticalCenter: parent.verticalCenter
                    x: horizontalBarItem.isPositiveValue ? horizontalBarRect.x + horizontalBarRect.width + Enums.spacing.xs : horizontalBarRect.x - width - Enums.spacing.xs
                    text: horizontalBarItem.barValue
                    font.weight: horizontalBarItem.hovered ? Font.DemiBold : Font.Normal
                    color: horizontalBarItem.hovered ? Enums.textColor.primary : Enums.textColor.secondary
                    visible: root.showValues
                    HoverBehavior on color {
                        active: horizontalBarItem.hovered
                        enterDuration: Enums.duration.fast
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: root.barHovered(index)
                    onExited: root.barHovered(-1)
                    onClicked: root.barClicked(index, modelData)
                }
            }
        }
    }

    // Multi-series mouse area 多系列鼠标区域
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        visible: root.isMultiSeries
        
        onPositionChanged: (mouse) => {
            if (!root.isMultiSeries || root.barPositions.length === 0) return
            var hit = root._nearestBarHit(mouse.x, mouse.y)
            root.hoveredIndex = hit.barIndex
            root.hoveredSeriesIndex = hit.seriesIndex
            root.seriesBarHovered(hit.seriesIndex, hit.barIndex)
        }
        
        onExited: {
            root.hoveredIndex = -1
            root.hoveredSeriesIndex = -1
            root.seriesBarHovered(-1, -1)
        }
        
        onClicked: {
            if (root.hoveredIndex >= 0 && root.hoveredSeriesIndex >= 0) {
                root.barClicked(root.hoveredIndex, {
                    seriesIndex: root.hoveredSeriesIndex,
                    barIndex: root.hoveredIndex,
                    value: root.series[root.hoveredSeriesIndex].values[root.hoveredIndex]
                })
            }
        }
    }
}
