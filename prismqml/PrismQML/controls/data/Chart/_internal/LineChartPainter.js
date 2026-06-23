// LineChartPainter.js - Line chart painting functions 折线图绑定函数
// Extracted from LineChartContent.qml for modularity 从 LineChartContent.qml 提取以实现模块化

.pragma library

// ==================== Line Drawing 线条绘制 ====================

/**
 * Draw line with optional smooth curve 绘制线条（可选平滑曲线）
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} points - [{x, y}, ...] point array
 * @param {string} color - Line color
 * @param {number} lineWidth - Line width
 * @param {boolean} smooth - Use bezier curve
 */
function drawLine(ctx, points, color, lineWidth, smooth) {
    if (points.length < 2) return
    
    ctx.beginPath()
    ctx.strokeStyle = color
    ctx.lineWidth = lineWidth
    ctx.lineCap = "round"
    ctx.lineJoin = "round"
    
    if (smooth && points.length > 2) {
        ctx.moveTo(points[0].x, points[0].y)
        for (var j = 0; j < points.length - 1; j++) {
            var xc = (points[j].x + points[j + 1].x) / 2
            var yc = (points[j].y + points[j + 1].y) / 2
            ctx.quadraticCurveTo(points[j].x, points[j].y, xc, yc)
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y)
    } else {
        ctx.moveTo(points[0].x, points[0].y)
        for (var n = 1; n < points.length; n++) {
            ctx.lineTo(points[n].x, points[n].y)
        }
    }
    ctx.stroke()
}

// ==================== Area Fill 面积填充 ====================

/**
 * Draw area fill under line 绘制线条下方面积填充
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} points - Point array
 * @param {color} color - Fill color (Qt color object)
 * @param {number} bottomY - Bottom Y coordinate
 * @param {boolean} smooth - Use bezier curve
 * @param {number} fillMedium - Medium fill opacity
 * @param {number} fillSubtle - Subtle fill opacity
 */
function drawAreaFill(ctx, points, color, bottomY, smooth, fillMedium, fillSubtle) {
    if (points.length < 2) return
    
    ctx.beginPath()
    ctx.moveTo(points[0].x, bottomY)
    
    if (smooth && points.length > 2) {
        ctx.lineTo(points[0].x, points[0].y)
        for (var k = 0; k < points.length - 1; k++) {
            var xc = (points[k].x + points[k + 1].x) / 2
            var yc = (points[k].y + points[k + 1].y) / 2
            ctx.quadraticCurveTo(points[k].x, points[k].y, xc, yc)
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y)
    } else {
        for (var m = 0; m < points.length; m++) {
            ctx.lineTo(points[m].x, points[m].y)
        }
    }
    
    ctx.lineTo(points[points.length - 1].x, bottomY)
    ctx.closePath()
    
    var gradient = ctx.createLinearGradient(0, 0, 0, bottomY)
    gradient.addColorStop(0, Qt.rgba(color.r, color.g, color.b, fillMedium))
    gradient.addColorStop(1, Qt.rgba(color.r, color.g, color.b, fillSubtle))
    ctx.fillStyle = gradient
    ctx.fill()
}

/**
 * Draw gradient area fill 绘制渐变面积填充
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} points - Point array
 * @param {string} colorStr - Color string
 * @param {number} bottomY - Bottom Y coordinate
 * @param {boolean} smooth - Use bezier curve
 * @param {number} fillMedium - Medium fill opacity
 * @param {number} fillLight - Light fill opacity
 * @param {number} fillFaint - Faint fill opacity
 */
function drawAreaGradient(ctx, points, colorStr, bottomY, smooth, fillMedium, fillLight, fillFaint) {
    if (points.length < 2) return
    
    ctx.beginPath()
    ctx.moveTo(points[0].x, bottomY)
    
    if (smooth && points.length > 2) {
        ctx.lineTo(points[0].x, points[0].y)
        for (var k = 0; k < points.length - 1; k++) {
            var xc = (points[k].x + points[k + 1].x) / 2
            var yc = (points[k].y + points[k + 1].y) / 2
            ctx.quadraticCurveTo(points[k].x, points[k].y, xc, yc)
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y)
    } else {
        for (var m = 0; m < points.length; m++) {
            ctx.lineTo(points[m].x, points[m].y)
        }
    }
    
    ctx.lineTo(points[points.length - 1].x, bottomY)
    ctx.closePath()
    
    var c = Qt.color(colorStr)
    var gradient = ctx.createLinearGradient(0, 0, 0, bottomY)
    gradient.addColorStop(0, Qt.rgba(c.r, c.g, c.b, fillMedium))
    gradient.addColorStop(0.5, Qt.rgba(c.r, c.g, c.b, fillLight))
    gradient.addColorStop(1, Qt.rgba(c.r, c.g, c.b, fillFaint))
    ctx.fillStyle = gradient
    ctx.fill()
}

/**
 * Draw stacked area fill 绘制堆叠面积填充
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} points - Current series points
 * @param {Array} prevPoints - Previous series points (bottom boundary)
 * @param {string} colorStr - Color string
 * @param {number} bottomY - Bottom Y coordinate
 * @param {boolean} smooth - Use bezier curve
 * @param {number} fillStrong - Strong fill opacity
 */
function drawStackedArea(ctx, points, prevPoints, colorStr, bottomY, smooth, fillStrong) {
    if (points.length < 2) return
    
    ctx.beginPath()
    
    // Draw top line (current series) 绘制顶部线（当前系列）
    if (smooth && points.length > 2) {
        ctx.moveTo(points[0].x, points[0].y)
        for (var k = 0; k < points.length - 1; k++) {
            var xc = (points[k].x + points[k + 1].x) / 2
            var yc = (points[k].y + points[k + 1].y) / 2
            ctx.quadraticCurveTo(points[k].x, points[k].y, xc, yc)
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y)
    } else {
        ctx.moveTo(points[0].x, points[0].y)
        for (var m = 1; m < points.length; m++) {
            ctx.lineTo(points[m].x, points[m].y)
        }
    }
    
    // Draw bottom line 绘制底部线
    if (prevPoints && prevPoints.length > 0) {
        if (smooth && prevPoints.length > 2) {
            ctx.lineTo(prevPoints[prevPoints.length - 1].x, prevPoints[prevPoints.length - 1].y)
            for (var j = prevPoints.length - 2; j >= 0; j--) {
                var xc2 = (prevPoints[j].x + prevPoints[j + 1].x) / 2
                var yc2 = (prevPoints[j].y + prevPoints[j + 1].y) / 2
                ctx.quadraticCurveTo(prevPoints[j + 1].x, prevPoints[j + 1].y, xc2, yc2)
            }
            ctx.lineTo(prevPoints[0].x, prevPoints[0].y)
        } else {
            for (var n = prevPoints.length - 1; n >= 0; n--) {
                ctx.lineTo(prevPoints[n].x, prevPoints[n].y)
            }
        }
    } else {
        ctx.lineTo(points[points.length - 1].x, bottomY)
        ctx.lineTo(points[0].x, bottomY)
    }
    
    ctx.closePath()
    
    var c = Qt.color(colorStr)
    ctx.fillStyle = Qt.rgba(c.r, c.g, c.b, fillStrong)
    ctx.fill()
}

// ==================== Point Drawing 点绘制 ====================

/**
 * Draw hollow point 绘制空心点
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @param {string} color - Point color
 * @param {boolean} isHighlighted - Is point highlighted
 * @param {string} bgColor - Background color for fill
 */
function drawHollowPoint(ctx, x, y, color, isHighlighted, bgColor) {
    var radius = isHighlighted ? 5 : 3
    
    // White fill 白色填充
    ctx.beginPath()
    ctx.fillStyle = bgColor
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.fill()
    
    // Color border 彩色边框
    ctx.beginPath()
    ctx.strokeStyle = color
    ctx.lineWidth = isHighlighted ? 2 : 1.5
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.stroke()
}

/**
 * Draw solid point 绘制实心点
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @param {string} color - Point color
 * @param {boolean} isHighlighted - Is point highlighted
 * @param {string} bgColor - Background color for center
 */
function drawSolidPoint(ctx, x, y, color, isHighlighted, bgColor) {
    var radius = isHighlighted ? 5 : 3
    
    // Solid fill 实心填充
    ctx.beginPath()
    ctx.fillStyle = color
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.fill()
    
    // White center for highlighted 高亮时白色中心
    if (isHighlighted) {
        ctx.beginPath()
        ctx.fillStyle = bgColor
        ctx.arc(x, y, 2, 0, Math.PI * 2)
        ctx.fill()
    }
}

// ==================== Indicator Drawing 指示器绘制 ====================

/**
 * Draw vertical indicator line 绘制垂直指示线
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {number} x - X coordinate
 * @param {number} height - Canvas height
 * @param {string} color - Line color
 */
function drawVerticalIndicator(ctx, x, height, color) {
    ctx.beginPath()
    ctx.strokeStyle = color
    ctx.lineWidth = 1
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
}

/**
 * Draw average line (dashed) 绘制平均线（虚线）
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {number} y - Y coordinate
 * @param {number} width - Canvas width
 * @param {string} colorStr - Color string
 * @param {number} alpha - Line alpha
 */
function drawAverageLine(ctx, y, width, colorStr, alpha) {
    var c = Qt.color(colorStr)
    ctx.beginPath()
    ctx.strokeStyle = Qt.rgba(c.r, c.g, c.b, alpha)
    ctx.lineWidth = 1
    ctx.setLineDash([4, 4])
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
    ctx.setLineDash([])
}

// ==================== Utility Functions 工具函数 ====================

/**
 * Calculate average of values 计算平均值
 * @param {Array} values - Number array
 * @returns {number} Average value
 */
function calculateAverage(values) {
    if (!values || values.length === 0) return 0
    var sum = 0
    for (var i = 0; i < values.length; i++) sum += values[i]
    return sum / values.length
}

/**
 * Find min/max indices in values 查找最大最小值索引
 * @param {Array} values - Number array
 * @returns {Object} {minIdx, maxIdx, minVal, maxVal}
 */
function findMinMaxIndices(values) {
    if (!values || values.length === 0) {
        return { minIdx: -1, maxIdx: -1, minVal: 0, maxVal: 0 }
    }
    var minIdx = 0, maxIdx = 0
    for (var i = 1; i < values.length; i++) {
        if (values[i] < values[minIdx]) minIdx = i
        if (values[i] > values[maxIdx]) maxIdx = i
    }
    return { 
        minIdx: minIdx, 
        maxIdx: maxIdx, 
        minVal: values[minIdx], 
        maxVal: values[maxIdx] 
    }
}
