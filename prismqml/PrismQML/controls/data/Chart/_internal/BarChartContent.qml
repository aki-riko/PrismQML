// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data/Label"

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
    
    // ==================== Props 属性 ====================
    property var series: []              // [{name: "", values: [], color: ""}, ...] - multi series 多系列
    property int hoveredIndex: -1
    property int hoveredSeriesIndex: -1
    property bool isHorizontal: false    // Horizontal bar chart 水平柱状图
    property var valueRange: ({ min: 0, max: maxValue, hasNegative: false, hasPositive: true })
    property real zeroLineRatio: 1.0     // Zero line position (0-1) 零轴线位置
    property bool showAverage: false     // Show average line (markLine) 显示平均线
    property bool showMinMax: false      // Show min/max markers (markPoint) 显示最大最小值标记
    property bool showBarGradient: false // Show gradient fill on bars 柱子渐变填充
    
    // ==================== Signals 信号 ====================
    signal barClicked(int index, var data)
    signal barHovered(int index)
    signal seriesBarHovered(int seriesIndex, int barIndex)
    
    // ==================== Internal 内部属性 ====================
    property var barPositions: []        // For markPoint positioning 用于markPoint定位
    
    // ==================== Computed Props 计算属性 ====================
    readonly property bool isMultiSeries: series.length > 0
    readonly property int dataLength: isMultiSeries ? (series[0].values ? series[0].values.length : 0) : chartData.length
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
    
    // ==================== Helper Functions 辅助函数 ====================
    function getSeriesColor(index) {
        if (series[index] && series[index].color) return series[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }
    
    function calculateAverage(values) {
        if (!values || values.length === 0) return 0
        var sum = 0
        for (var i = 0; i < values.length; i++) sum += values[i]
        return sum / values.length
    }
    
    function findMinMaxIndices(values) {
        if (!values || values.length === 0) return { minIdx: -1, maxIdx: -1, minVal: 0, maxVal: 0 }
        var minIdx = 0, maxIdx = 0
        for (var i = 1; i < values.length; i++) {
            if (values[i] < values[minIdx]) minIdx = i
            if (values[i] > values[maxIdx]) maxIdx = i
        }
        return { minIdx: minIdx, maxIdx: maxIdx, minVal: values[minIdx], maxVal: values[maxIdx] }
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

    // ==================== Canvas for Multi-Series 多系列画布 (Fluent Design) ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        visible: root.isMultiSeries && !root.isHorizontal
        
        property real animProgress: root.animated ? 0 : 1
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            if (!root.isMultiSeries || root.series.length === 0) return
            
            var seriesCount = root.series.length
            var dataLen = root.dataLength
            if (dataLen === 0) return
            
            var groupWidth = width / dataLen
            var barWidth = (groupWidth * 0.7) / seriesCount
            var barSpacing = barWidth * 0.1
            var allBarPositions = []
            
            // Draw bars 绘制柱子
            for (var s = 0; s < seriesCount; s++) {
                var seriesData = root.series[s]
                var values = seriesData.values || []
                var color = root.getSeriesColor(s)
                var seriesPositions = []
                
                for (var i = 0; i < values.length; i++) {
                    var value = values[i]
                    var barHeight = root.getBarRatio(value) * height * animProgress
                    var x = i * groupWidth + (groupWidth - barWidth * seriesCount - barSpacing * (seriesCount - 1)) / 2 + s * (barWidth + barSpacing)
                    var y = root.isPositive(value) ? root.valueToY(value) : root.valueToY(0)
                    
                    if (!root.isPositive(value)) {
                        y = root.valueToY(0)
                    } else {
                        y = root.valueToY(0) - barHeight
                    }
                    
                    var hovered = (s === root.hoveredSeriesIndex && i === root.hoveredIndex)
                    
                    // Fluent Design: simple color with subtle hover effect 简洁颜色+微妙悬停效果
                    ctx.fillStyle = hovered ? Qt.lighter(color, 1.1) : color
                    
                    // Draw bar with rounded top corners 绘制顶部圆角柱子
                    drawRoundedRect(ctx, x, y, barWidth, barHeight, Enums.radius.small)
                    ctx.fill()
                    
                    seriesPositions.push({
                        x: x + barWidth / 2,
                        y: root.isPositive(value) ? y : y + barHeight,
                        value: value,
                        barTop: y,
                        barBottom: y + barHeight
                    })
                }
                allBarPositions.push(seriesPositions)
                
                // Fluent Design: simple average line 简洁平均线
                if (root.showAverage && values.length > 0) {
                    var avg = root.calculateAverage(values)
                    var avgY = root.valueToY(avg)
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(Qt.color(color).r, Qt.color(color).g, Qt.color(color).b, Enums.stateColor.chartStrokeAlpha)
                    ctx.lineWidth = 1
                    ctx.setLineDash([4, 4])
                    ctx.moveTo(0, avgY)
                    ctx.lineTo(width, avgY)
                    ctx.stroke()
                    ctx.setLineDash([])
                }
            }
            root.barPositions = allBarPositions
        }
        
        // Draw rounded rectangle with only top corners rounded 只有顶部圆角的矩形
        function drawRoundedRect(ctx, x, y, w, h, r) {
            if (w < 2 * r) r = w / 2
            if (h < 2 * r) r = h / 2
            ctx.beginPath()
            ctx.moveTo(x + r, y)
            ctx.lineTo(x + w - r, y)
            ctx.arcTo(x + w, y, x + w, y + r, r)
            ctx.lineTo(x + w, y + h)
            ctx.lineTo(x, y + h)
            ctx.lineTo(x, y + r)
            ctx.arcTo(x, y, x + r, y, r)
            ctx.closePath()
        }
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                animTimer.start()
            } else {
                requestPaint()
            }
        }
        
        Timer {
            id: animTimer
            interval: Enums.duration.tick  // High-refresh tick 高刷定时器
            repeat: true
            property real t: 0  // Normalized time 归一化时间
            onTriggered: {
                t += 0.04  // ~400ms total duration 总时长约400ms
                if (t >= 1) {
                    t = 1
                    canvas.animProgress = 1
                    stop()
                } else {
                    // Fluent Design: OutQuint easing for smooth deceleration 平滑减速
                    canvas.animProgress = 1 - Math.pow(1 - t, 5)
                }
                canvas.requestPaint()
            }
        }
    }
    
    // Repaint triggers 重绘触发
    onHoveredIndexChanged: {
        canvas.requestPaint()
        if (!isMultiSeries && !isHorizontal) singleBarIndicator.requestPaint()
    }
    onHoveredSeriesIndexChanged: canvas.requestPaint()
    onSeriesChanged: canvas.requestPaint()
    onShowAverageChanged: canvas.requestPaint()
    onShowBarGradientChanged: canvas.requestPaint()

    // ==================== Min/Max Bubble Markers 最大最小值气泡标记 ====================
    Repeater {
        model: root.isMultiSeries && root.showMinMax ? root.series : []
        
        Item {
            id: markerItem
            anchors.fill: parent
            
            property int seriesIdx: index
            property var values: modelData.values || []
            property var minMax: root.findMinMaxIndices(values)
            property color seriesColor: root.getSeriesColor(index)
            
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
                    color: "white"
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
                    color: "white"
                }
            }
        }
    }
    
    // ==================== Average Value Labels (right side) 平均值标签（右侧） ====================
    Repeater {
        model: root.isMultiSeries && root.showAverage ? root.series : []
        
        Label {
            type: Enums.label.type_caption
            property var values: modelData.values || []
            property real avg: root.calculateAverage(values)
            property color seriesColor: root.getSeriesColor(index)
            
            x: root.width + 4
            y: root.valueToY(avg) - height / 2
            text: avg.toFixed(1)
            color: seriesColor
            visible: values.length > 0
        }
    }

    // ==================== Single Series Vertical Bar Chart 单系列垂直柱状图 ====================
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
            model: root.chartData
            
            Item {
                id: verticalBarItem
                width: (verticalBarRow.width - verticalBarRow.spacing * (root.chartData.length - 1)) / Math.max(root.chartData.length, 1)
                height: verticalBarRow.height
                
                property bool hovered: root.hoveredIndex === index
                property real barValue: modelData && modelData.value !== undefined ? modelData.value : 0
                property bool isPositiveValue: root.isPositive(barValue)
                property real barRatio: root.getBarRatio(barValue)
                property real zeroY: root.zeroLineRatio * height
                
                // Fluent Design: simple bar with rounded top corners 简洁柱子+顶部圆角
                Canvas {
                    id: verticalBarRect
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.min(parent.width * 0.7, Enums.spacing.xxxl)
                    y: verticalBarItem.isPositiveValue ? verticalBarItem.zeroY - height : verticalBarItem.zeroY
                    height: root.animated ? 0 : verticalBarItem.barRatio * parent.height
                    
                    property color barColor: root.getColor(index)
                    property bool barHovered: verticalBarItem.hovered
                    
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
                    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
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

    // ==================== Single Series Horizontal Bar Chart 单系列水平柱状图 ====================
    Column {
        id: horizontalBarColumn
        anchors.fill: parent
        spacing: Enums.spacing.xs
        visible: !root.isMultiSeries && root.isHorizontal
        
        Repeater {
            model: root.chartData
            
            Item {
                id: horizontalBarItem
                width: horizontalBarColumn.width
                height: (horizontalBarColumn.height - horizontalBarColumn.spacing * (root.chartData.length - 1)) / Math.max(root.chartData.length, 1)
                
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
                
                // Fluent Design: simple horizontal bar 简洁水平柱子
                Canvas {
                    id: horizontalBarRect
                    anchors.verticalCenter: parent.verticalCenter
                    height: Math.min(parent.height * 0.7, Enums.spacing.xxl)
                    x: horizontalBarItem.isPositiveValue ? horizontalBarItem.zeroX : horizontalBarItem.zeroX - width
                    width: root.animated ? 0 : horizontalBarItem.barRatio * parent.width
                    
                    property color barColor: root.getColor(index)
                    property bool barHovered: horizontalBarItem.hovered
                    property bool isPositive: horizontalBarItem.isPositiveValue
                    
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
                            // Use Timer to ensure layout is complete 使用定时器确保布局完成
                            delayTimer.start()
                        }
                    }
                    
                    Timer {
                        id: delayTimer
                        interval: Enums.duration.tick
                        repeat: false
                        onTriggered: {
                            horizontalBarRect.width = horizontalBarItem.barRatio * horizontalBarItem.width
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
                    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
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

    // ==================== Multi-Series Mouse Area 多系列鼠标区域 ====================
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        visible: root.isMultiSeries
        
        onPositionChanged: (mouse) => {
            if (!root.isMultiSeries || root.barPositions.length === 0) return
            
            var minDist = 30
            var foundIndex = -1
            var foundSeriesIndex = -1
            
            for (var s = 0; s < root.barPositions.length; s++) {
                var positions = root.barPositions[s]
                for (var i = 0; i < positions.length; i++) {
                    var pos = positions[i]
                    var dist = Math.abs(mouse.x - pos.x)
                    if (dist < minDist && mouse.y >= pos.barTop && mouse.y <= pos.barBottom) {
                        minDist = dist
                        foundIndex = i
                        foundSeriesIndex = s
                    }
                }
            }
            
            root.hoveredIndex = foundIndex
            root.hoveredSeriesIndex = foundSeriesIndex
            root.seriesBarHovered(foundSeriesIndex, foundIndex)
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
