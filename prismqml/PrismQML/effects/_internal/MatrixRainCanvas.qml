// MatrixRainCanvas - digital rain rendering surface 数字雨绘制表面
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick

Canvas {
    id: canvas

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var animationDriver

    function _scaledProbability(probability, stepScale) {
        var boundedProbability = Math.max(0, Math.min(1, probability))
        return 1 - Math.pow(1 - boundedProbability, stepScale)
    }

    function clearCanvas() {
        if (!available) return
        var ctx = getContext("2d")
        if (ctx) {
            ctx.fillStyle = host.backgroundColor
            ctx.fillRect(0, 0, width, height)
        }
    }

    function initDrops() {
        if (width <= 0 || height <= 0 || !available) return

        var arr = []
        var seeds = []
        if (host.isHorizontal) {
            host.rows = Math.ceil(height / host.cellSize / host._safeDensity)
            for (var i = 0; i < host.rows; i++) {
                arr.push(Math.random() * -50)
                seeds.push(Math.random())
            }
        } else {
            host.cols = Math.ceil(width / host.cellSize / host._safeDensity)
            for (var j = 0; j < host.cols; j++) {
                arr.push(Math.random() * -50)
                seeds.push(Math.random())
            }
        }
        host.drops = arr
        host.characterSeeds = seeds
        clearCanvas()
    }

    anchors.fill: parent

    onWidthChanged: if (available) initDrops()
    onHeightChanged: if (available) initDrops()
    onAvailableChanged: if (available) initDrops()

    onPaint: {
        var ctx = getContext("2d")
        if (!ctx) return

        var stepScale = animationDriver.takeStepScale()
        var localDrops = host.drops
        var localCharacterSeeds = host.characterSeeds
        var activeCharset = host._activeCharset
        if (localDrops.length === 0 || activeCharset.length === 0) return

        var backgroundColor = host.backgroundColor

        // Fade trail 拖尾效果
        ctx.fillStyle = Qt.rgba(
            backgroundColor.r,
            backgroundColor.g,
            backgroundColor.b,
            _scaledProbability(host.fadeSpeed, stepScale)
        )
        ctx.fillRect(0, 0, width, height)

        ctx.font = host.fontSize + "px monospace"

        var w = width, h = height
        var cellSize = host.cellSize
        var cs = cellSize * host._safeDensity
        var charLen = activeCharset.length
        var isHoriz = host.isHorizontal
        var dir = host.direction
        var count = isHoriz ? host.rows : host.cols
        var flickerEnabled = host.flickerEnabled
        var flickerRate = host.flickerRate
        var scaledFlickerRate = _scaledProbability(flickerRate, stepScale)
        var scaledResetProbability = _scaledProbability(0.025, stepScale)
        var characterUpdateProbability = Math.min(1, stepScale)
        var perspective = host.perspective
        var interactive = host.interactive
        var interactionRadius = host._safeInteractionRadius
        var mousePos = host.mousePos
        var mainColor = host.mainColor
        var headColor = host.headColor
        var rainbowMode = host.rainbowMode
        var rainbowOffset = host._rainbowOffset
        var glowEnabled = host.glowEnabled
        var glowIntensity = host.glowIntensity
        var trailOffset = (dir === "up" ? -cellSize : cellSize) * 0.5

        // Note: Glow is applied per-character for head only (performance) 发光只应用于头部字符

        for (var i = 0; i < count; i++) {
            // Flicker skip 闪烁跳过
            if (flickerEnabled && Math.random() < scaledFlickerRate) continue

            if (localCharacterSeeds[i] === undefined
                    || Math.random() < characterUpdateProbability) {
                localCharacterSeeds[i] = Math.random()
            }
            var character = activeCharset[
                Math.floor(localCharacterSeeds[i] * charLen)]
            var pos = localDrops[i] * cellSize
            var x, y

            // Calculate position based on direction 根据方向计算位置
            if (dir === "down") {
                x = i * cs
                y = pos
            } else if (dir === "up") {
                x = i * cs
                y = h - pos
            } else if (dir === "right") {
                x = pos
                y = i * cs
            } else { // left
                x = w - pos
                y = i * cs
            }

            // Perspective transform 透视变换
            if (perspective > 0) {
                var centerX = w / 2, centerY = h / 2
                var distX = (x - centerX) / centerX
                var distY = (y - centerY) / centerY
                var scale = 1 - perspective * 0.3 * (Math.abs(distX) + Math.abs(distY))
                ctx.save()
                ctx.translate(x, y)
                ctx.scale(scale, scale)
                ctx.translate(-x, -y)
            }

            // Interactive repulsion 交互排斥
            if (interactive && interactionRadius > 0) {
                var dx = x - mousePos.x
                var dy = y - mousePos.y
                var dist = Math.sqrt(dx * dx + dy * dy)
                if (dist > 0 && dist < interactionRadius) {
                    var force = (1 - dist / interactionRadius) * 30
                    x += dx / dist * force
                    y += dy / dist * force
                }
            }

            // Rainbow mode color 彩虹模式颜色
            var currentMainColor = mainColor
            var currentHeadColor = headColor
            if (rainbowMode) {
                var hue = (rainbowOffset + i * 10) % 360
                currentMainColor = Qt.hsla(hue / 360, 1, 0.5, 1)
                currentHeadColor = Qt.hsla(hue / 360, 0.8, 0.7, 1)
            }

            // Glow effect (lightweight simulation) 发光效果（轻量模拟）
            if (glowEnabled) {
                ctx.globalAlpha = 0.3 * glowIntensity
                ctx.fillStyle = currentHeadColor
                ctx.fillText(character, x - 1, y)
                ctx.fillText(character, x + 1, y)
                ctx.fillText(character, x, y - 1)
                ctx.fillText(character, x, y + 1)
                ctx.globalAlpha = 1.0
            }

            // Head character (brighter) 头部字符（更亮）
            ctx.fillStyle = currentHeadColor
            ctx.fillText(character, x, y)

            // Main trail 主拖尾
            ctx.fillStyle = currentMainColor
            ctx.fillText(character, x, y - trailOffset)

            if (perspective > 0) {
                ctx.restore()
            }

            // Move based on direction 根据方向移动
            localDrops[i] += (0.5 + Math.random() * 0.5) * stepScale

            // Reset check 重置检查
            var shouldReset = false
            if (dir === "down" && y > h) shouldReset = true
            else if (dir === "up" && y < 0) shouldReset = true
            else if (dir === "right" && x > w) shouldReset = true
            else if (dir === "left" && x < 0) shouldReset = true

            if (shouldReset && Math.random() < scaledResetProbability) {
                localDrops[i] = 0
            }
        }

        // Update rainbow offset 更新彩虹偏移
        if (rainbowMode) {
            host._rainbowOffset = (rainbowOffset + 2 * stepScale) % 360
        }
    }
}
