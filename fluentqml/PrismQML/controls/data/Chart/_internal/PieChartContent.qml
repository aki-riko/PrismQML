// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."

// PieChartContent - Pie/Donut chart rendering component 饼图/环形图渲染组件
// Fluent Design style: clean, subtle hover effects Fluent Design 风格：简洁、微妙的悬停效果


Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    required property var chartData      // [{label: "", value: 0, color: ""}, ...]
    required property real totalValue    // Sum of all values 所有值的总和
    required property bool animated      // Enable animation 启用动画
    required property bool showValues    // Show percentage labels 显示百分比标签
    required property bool isDonut       // Is donut chart 是否环形图
    required property real donutRatio    // Inner radius ratio 内径比例
    required property var getColor       // Function to get color 获取颜色函数
    
    // ==================== Props 属性 ====================
    property int hoveredIndex: -1
    property int previousHoveredIndex: -1  // Track previous hover for transition 追踪上一个悬停索引用于过渡
    property bool labelOutside: false    // Label position: "outside" 标签在外部
    
    // ==================== Signals 信号 ====================
    signal sliceClicked(int index, var data)
    signal sliceHovered(int index)
    
    // ==================== Canvas 画布 ====================
    Canvas {
        id: canvas
        anchors.fill: parent
        
        property real animProgress: 0
        property real hoverOffset: 0
        property real transitionProgress: 1.0  // Slice transition animation progress 扇区切换动画进度
        
        Behavior on hoverOffset {
            NumberAnimation { 
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic 
            }
        }
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            if (root.chartData.length === 0) return
            
            var centerX = width / 2
            var centerY = height / 2
            var outerRadius = Math.min(width, height) / 2 - Enums.spacing.l
            var innerRadius = root.isDonut ? outerRadius * root.donutRatio : 0
            
            var startAngle = -Math.PI / 2  // Start from top 从顶部开始
            
            // Draw all slices 绘制所有扇区
            for (var i = 0; i < root.chartData.length; i++) {
                var sliceAngle = (root.chartData[i].value / root.totalValue) * Math.PI * 2
                var endAngle = startAngle + sliceAngle * (root.animated ? animProgress : 1)
                
                var hovered = (i === root.hoveredIndex)
                var isPreviousHovered = (i === root.previousHoveredIndex)
                var offsetX = 0, offsetY = 0
                
                // Fluent Design: subtle offset on hover 悬停时微妙偏移
                var midAngle = startAngle + sliceAngle / 2
                if (hovered && hoverOffset > 0) {
                    var currentOffset = hoverOffset * transitionProgress * 0.5  // Reduced offset 减少偏移量
                    offsetX = Math.cos(midAngle) * currentOffset
                    offsetY = Math.sin(midAngle) * currentOffset
                } else if (isPreviousHovered && hoverOffset > 0 && transitionProgress < 1) {
                    var prevOffset = hoverOffset * (1 - transitionProgress) * 0.5
                    offsetX = Math.cos(midAngle) * prevOffset
                    offsetY = Math.sin(midAngle) * prevOffset
                }
                
                ctx.beginPath()
                if (innerRadius > 0) {
                    // Donut chart 环形图
                    ctx.arc(centerX + offsetX, centerY + offsetY, innerRadius, startAngle, endAngle, false)
                    ctx.arc(centerX + offsetX, centerY + offsetY, outerRadius, endAngle, startAngle, true)
                } else {
                    // Pie chart 饼图
                    ctx.moveTo(centerX + offsetX, centerY + offsetY)
                    ctx.arc(centerX + offsetX, centerY + offsetY, outerRadius, startAngle, endAngle, false)
                }
                ctx.closePath()
                
                var sliceColor = root.getColor(i)
                // Fluent Design: subtle brightness change on hover 悬停时微妙亮度变化
                if (hovered) {
                    ctx.fillStyle = Qt.lighter(sliceColor, 1.08)
                } else if (isPreviousHovered && transitionProgress < 1) {
                    var prevLightness = 1.0 + 0.08 * (1 - transitionProgress)
                    ctx.fillStyle = Qt.lighter(sliceColor, prevLightness)
                } else {
                    ctx.fillStyle = sliceColor
                }
                ctx.fill()
                
                // Draw white border between slices 扇区间白色边框
                ctx.strokeStyle = Enums.cardColor
                ctx.lineWidth = 2
                ctx.stroke()
                
                // Draw percentage label inside slice 在扇区内绘制百分比标签
                if (root.showValues && animProgress >= 1) {
                    var percent = Math.round(root.chartData[i].value / root.totalValue * 100)
                    if (percent >= 5) {  // Only show if >= 5% 仅显示>=5%的
                        var labelAngle = startAngle + sliceAngle / 2
                        
                        if (root.labelOutside) {
                            // Draw line from slice to outside label 绘制从扇区到外部标签的连接线

                            var innerLabelRadius = outerRadius + 5
                            var outerLabelRadius = outerRadius + 25
                            var lineStartX = centerX + offsetX + Math.cos(labelAngle) * innerLabelRadius
                            var lineStartY = centerY + offsetY + Math.sin(labelAngle) * innerLabelRadius
                            var lineEndX = centerX + offsetX + Math.cos(labelAngle) * outerLabelRadius
                            var lineEndY = centerY + offsetY + Math.sin(labelAngle) * outerLabelRadius
                            
                            // Draw label line 绘制标签线
                            ctx.beginPath()
                            ctx.strokeStyle = root.getColor(i)
                            ctx.lineWidth = 1
                            ctx.moveTo(lineStartX, lineStartY)
                            ctx.lineTo(lineEndX, lineEndY)
                            
                            // Horizontal extension 水平延伸
                            var extendX = labelAngle > -Math.PI / 2 && labelAngle < Math.PI / 2 ? 15 : -15
                            ctx.lineTo(lineEndX + extendX, lineEndY)
                            ctx.stroke()
                            
                            // Draw outside label 绘制外部标签
                            ctx.fillStyle = Enums.textColor.secondary
                            ctx.font = Enums.typography.caption + "px " + Enums.canvasFontFamily
                            ctx.textAlign = extendX > 0 ? "left" : "right"
                            ctx.textBaseline = "middle"
                            var labelText = (root.chartData[i].label || "") + " " + percent + "%"
                            ctx.fillText(labelText, lineEndX + extendX + (extendX > 0 ? 4 : -4), lineEndY)
                        } else {
                            // Inside label 内部标签
                            var labelRadius = innerRadius > 0 ? (innerRadius + outerRadius) / 2 : outerRadius * 0.65
                            var labelX = centerX + offsetX + Math.cos(labelAngle) * labelRadius
                            var labelY = centerY + offsetY + Math.sin(labelAngle) * labelRadius
                            
                            ctx.fillStyle = "white"
                            ctx.font = "bold " + Enums.typography.caption + "px " + Enums.canvasFontFamily
                            ctx.textAlign = "center"
                            ctx.textBaseline = "middle"
                            ctx.fillText(percent + "%", labelX, labelY)
                        }
                    }
                }
                
                startAngle += sliceAngle * (root.animated ? animProgress : 1)
            }
        }
        
        Component.onCompleted: {
            if (root.animated) {
                animProgress = 0
                animTimer.start()
            } else {
                animProgress = 1
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
        
        onHoverOffsetChanged: requestPaint()
        
        // Slice transition animation timer 扇区切换动画计时器
        Timer {
            id: transitionTimer
            interval: Enums.duration.tick  // High-refresh tick 高刷定时器
            repeat: true
            onTriggered: {
                canvas.transitionProgress += 0.12
                if (canvas.transitionProgress >= 1) {
                    canvas.transitionProgress = 1
                    root.previousHoveredIndex = -1  // Clear previous after transition 过渡完成后清除
                    stop()
                }
                canvas.requestPaint()
            }
        }
    }
    
    // Hover animation trigger with slice transition 悬浮动画触发（带扇区过渡）
    onHoveredIndexChanged: {
        // Start transition animation when switching between slices 扇区切换时启动过渡动画
        if (hoveredIndex >= 0 && previousHoveredIndex >= 0 && hoveredIndex !== previousHoveredIndex) {
            canvas.transitionProgress = 0
            transitionTimer.start()
        } else if (hoveredIndex >= 0 && previousHoveredIndex < 0) {
            // First hover, no transition needed 首次悬停，无需过渡
            canvas.transitionProgress = 1
            canvas.hoverOffset = Enums.spacing.s
        } else if (hoveredIndex < 0) {
            // Mouse left, animate out 鼠标离开，向内动画
            canvas.hoverOffset = 0
            canvas.transitionProgress = 1
        }
        
        // Update previous index for next transition 更新上一个索引用于下次过渡
        if (hoveredIndex >= 0) {
            previousHoveredIndex = hoveredIndex
            canvas.hoverOffset = Enums.spacing.s
        }
        
        canvas.requestPaint()
    }
    
    onChartDataChanged: canvas.requestPaint()
    
    // ==================== Mouse Area 鼠标区域 ====================
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onPositionChanged: (mouse) => {
            var centerX = width / 2
            var centerY = height / 2
            var dx = mouse.x - centerX
            var dy = mouse.y - centerY
            var dist = Math.sqrt(dx * dx + dy * dy)
            var outerRadius = Math.min(width, height) / 2 - Enums.spacing.l
            var innerRadius = root.isDonut ? outerRadius * root.donutRatio : 0
            
            if (dist < innerRadius || dist > outerRadius) {
                root.sliceHovered(-1)
                return
            }
            
            // Calculate angle 计算角度
            var angle = Math.atan2(dy, dx)
            if (angle < -Math.PI / 2) angle += Math.PI * 2
            angle += Math.PI / 2
            if (angle > Math.PI * 2) angle -= Math.PI * 2
            
            // Find which slice 查找扇区
            var cumAngle = 0
            for (var i = 0; i < root.chartData.length; i++) {
                var sliceAngle = (root.chartData[i].value / root.totalValue) * Math.PI * 2
                if (angle >= cumAngle && angle < cumAngle + sliceAngle) {
                    root.sliceHovered(i)
                    return
                }
                cumAngle += sliceAngle
            }
            root.sliceHovered(-1)
        }
        
        onExited: root.sliceHovered(-1)
        onClicked: {
            if (root.hoveredIndex >= 0) {
                root.sliceClicked(root.hoveredIndex, root.chartData[root.hoveredIndex])
            }
        }
    }
}
