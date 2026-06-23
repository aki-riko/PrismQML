// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."

// MatrixRain - The Matrix digital rain effect 黑客帝国数字雨效果
// Usage 使用方式:
//   MatrixRain { anchors.fill: parent }
//   MatrixRain { direction: "up"; glowEnabled: true; charsetPreset: "binary" }

Rectangle {
    id: root
    color: backgroundColor
    clip: true
    
    // ==================== Public Props 公开属性 ====================
    // Basic 基础属性
    property bool running: true                         // Animation running 动画运行
    property bool paused: false                         // Animation paused 动画暂停
    property real speed: 1.0                            // Fall speed (0.1-5.0) 下落速度
    property int fontSize: 14                           // Character size 字符大小
    property real density: 1.0                          // Column density (0.5-2.0) 列密度
    property real fadeSpeed: 0.05                       // Trail fade (0.01-0.2) 拖尾消隐
    
    // Colors 颜色属性
    property color mainColor: "#00ff00"                 // Main color 主颜色
    property color headColor: "#aaffaa"                 // Head character color 头部字符颜色
    property color backgroundColor: "#000000"           // Background color 背景颜色
    
    // Direction 方向控制
    property string direction: "down"                   // Direction: down/up/left/right 方向
    
    // Character set 字符集
    property string charset: "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ012345789Z:・.=*+-<>¦"
    property string charsetPreset: ""                   // Preset: japanese/binary/digits/chinese/katakana/symbols/ascii 预设字符集
    
    // Effects 效果
    property bool glowEnabled: false                    // Glow effect 发光效果
    property real glowIntensity: 1.0                    // Glow intensity (0.5-3.0) 发光强度
    property bool flickerEnabled: false                 // Random flicker 随机闪烁
    property real flickerRate: 0.1                      // Flicker rate (0-1) 闪烁频率
    property real perspective: 0.0                      // 3D perspective (0-1) 3D透视
    
    // Interaction 交互
    property bool interactive: false                    // Mouse interaction 鼠标交互
    property real interactionRadius: 100                // Interaction radius 交互半径
    
    // Trail 拖尾
    property int trailLength: 20                        // Trail length 拖尾长度
    property bool rainbowMode: false                    // Rainbow color mode 彩虹模式
    
    // ==================== Signals 信号 ====================
    signal themeApplied(string themeName)
    
    // ==================== Internal 内部 ====================
    property var drops: []
    property int cols: 0
    property int rows: 0
    property int cellSize: Math.max(10, fontSize + 2)
    property point mousePos: Qt.point(-1000, -1000)
    property bool isHorizontal: direction === "left" || direction === "right"
    
    // Charset presets 预设字符集
    readonly property var _charsetPresets: ({
        "japanese": "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ",
        "katakana": "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン",
        "binary": "01",
        "digits": "0123456789",
        "hex": "0123456789ABCDEF",
        "chinese": "中国日本韩国美丽世界和平发展科技未来数据矩阵代码程序",
        "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?/~`",
        "ascii": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        "greek": "αβγδεζηθικλμνξοπρστυφχψω",
        "runic": "ᚠᚡᚢᚣᚤᚥᚦᚧᚨᚩᚪᚫᚬᚭᚮᚯᚰᚱᚲᚳᚴᚵᚶᚷᚸᚹᚺᚻᚼᚽᚾᚿᛀᛁᛂᛃᛄᛅᛆᛇᛈᛉᛊᛋᛌᛍᛎᛏᛐᛑᛒᛓᛔᛕᛖᛗᛘᛙᛚᛛᛜᛝᛞᛟᛠᛡᛢᛣᛤᛥᛦᛧᛨᛩᛪ"
    })
    
    // Active charset 当前使用的字符集
    readonly property string _activeCharset: charsetPreset && _charsetPresets[charsetPreset] 
        ? _charsetPresets[charsetPreset] : charset
    
    // Rainbow hue offset 彩虹色相偏移
    property real _rainbowOffset: 0

    // ==================== Public Methods 公开方法 ====================

    // Control methods 控制方法
    function start() { running = true; paused = false }
    function stop() { running = false }
    function pause() { paused = true }
    function resume() { paused = false }
    function reset() { canvas.initDrops() }
    function toggle() { paused = !paused }

    // Direction methods 方向方法
    function setDirection(dir) {
        if (["down", "up", "left", "right"].indexOf(dir) !== -1) {
            direction = dir
        }
    }
    // Theme presets 主题预设
    function setTheme(name) {
        var themes = {
            "classic":  { main: "#00ff00", head: "#aaffaa", bg: "#000000" },
            "cyan":     { main: "#00ffff", head: "#aaffff", bg: "#000011" },
            "amber":    { main: "#ffaa00", head: "#ffff00", bg: "#0a0500" },
            "red":      { main: "#ff0040", head: "#ff8888", bg: "#0a0000" },
            "purple":   { main: "#aa00ff", head: "#ffaaff", bg: "#050005" },
            "blue":     { main: "#0088ff", head: "#88ccff", bg: "#000510" },
            "white":    { main: "#ffffff", head: "#ffffff", bg: "#111111" },
            "pink":     { main: "#ff69b4", head: "#ffb6c1", bg: "#0a0008" },
            "gold":     { main: "#ffd700", head: "#ffec8b", bg: "#0a0800" },
            "lime":     { main: "#32cd32", head: "#90ee90", bg: "#000a00" },
            "orange":   { main: "#ff6600", head: "#ffaa66", bg: "#0a0300" },
            "teal":     { main: "#008080", head: "#40e0d0", bg: "#000505" },
            "neon":     { main: "#39ff14", head: "#7fff00", bg: "#000000" },
            "sunset":   { main: "#ff4500", head: "#ff8c00", bg: "#1a0a00" },
            "ocean":    { main: "#006994", head: "#00ced1", bg: "#001015" },
            "forest":   { main: "#228b22", head: "#98fb98", bg: "#000800" },
            "midnight": { main: "#191970", head: "#6495ed", bg: "#000008" }
        }

        if (themes[name]) {
            mainColor = themes[name].main
            headColor = themes[name].head
            backgroundColor = themes[name].bg
            themeApplied(name)
        }
    }

    // Charset preset methods 字符集预设方法
    function setCharsetPreset(preset) {
        if (_charsetPresets[preset]) {
            charsetPreset = preset
        }
    }

    function setCustomCharset(chars) {
        charsetPreset = ""
        charset = chars
    }
    // Effect methods 效果方法
    function enableGlow(intensity) {
        glowEnabled = true
        if (intensity !== undefined) glowIntensity = intensity
    }

    function disableGlow() {
        glowEnabled = false
    }

    function enableFlicker(rate) {
        flickerEnabled = true
        if (rate !== undefined) flickerRate = rate
    }

    function disableFlicker() {
        flickerEnabled = false
    }

    function enableInteraction(radius) {
        interactive = true
        if (radius !== undefined) interactionRadius = radius
    }

    function disableInteraction() {
        interactive = false
    }

    function enableRainbow() {
        rainbowMode = true
    }

    function disableRainbow() {
        rainbowMode = false
    }

    function setPerspective(value) {
        perspective = Math.max(0, Math.min(1, value))
    }
    // Batch configuration 批量配置
    function configure(options) {
        if (options.speed !== undefined) speed = options.speed
        if (options.fontSize !== undefined) fontSize = options.fontSize
        if (options.density !== undefined) density = options.density
        if (options.fadeSpeed !== undefined) fadeSpeed = options.fadeSpeed
        if (options.direction !== undefined) direction = options.direction
        if (options.mainColor !== undefined) mainColor = options.mainColor
        if (options.headColor !== undefined) headColor = options.headColor
        if (options.backgroundColor !== undefined) backgroundColor = options.backgroundColor
        if (options.glowEnabled !== undefined) glowEnabled = options.glowEnabled
        if (options.glowIntensity !== undefined) glowIntensity = options.glowIntensity
        if (options.flickerEnabled !== undefined) flickerEnabled = options.flickerEnabled
        if (options.flickerRate !== undefined) flickerRate = options.flickerRate
        if (options.perspective !== undefined) perspective = options.perspective
        if (options.interactive !== undefined) interactive = options.interactive
        if (options.interactionRadius !== undefined) interactionRadius = options.interactionRadius
        if (options.rainbowMode !== undefined) rainbowMode = options.rainbowMode
        if (options.charsetPreset !== undefined) charsetPreset = options.charsetPreset
        if (options.charset !== undefined) charset = options.charset
        if (options.theme !== undefined) setTheme(options.theme)
    }

    // Get available presets 获取可用预设
    function getAvailableThemes() {
        return ["classic", "cyan", "amber", "red", "purple", "blue", "white",
                "pink", "gold", "lime", "orange", "teal", "neon", "sunset",
                "ocean", "forest", "midnight"]
    }

    function getAvailableCharsets() {
        return Object.keys(_charsetPresets)
    }

    function getAvailableDirections() {
        return ["down", "up", "left", "right"]
    }

    onDirectionChanged: canvas.initDrops()
    
    onCharsetPresetChanged: canvas.requestPaint()
    
    Canvas {
        id: canvas
        anchors.fill: parent
        
        onWidthChanged: if (available) initDrops()
        onHeightChanged: if (available) initDrops()
        onAvailableChanged: if (available) initDrops()
        
        // Respond to property changes 响应属性变化
        Connections {
            target: root
            function onMainColorChanged() { canvas.clearCanvas() }
            function onHeadColorChanged() { canvas.clearCanvas() }
            function onBackgroundColorChanged() { canvas.clearCanvas() }
            function onDensityChanged() { canvas.initDrops() }
        }
        
        function clearCanvas() {
            if (!available) return
            var ctx = getContext("2d")
            if (ctx) {
                ctx.fillStyle = root.backgroundColor
                ctx.fillRect(0, 0, width, height)
            }
        }
        
        function initDrops() {
            if (width <= 0 || height <= 0 || !available) return
            
            var arr = []
            if (root.isHorizontal) {
                root.rows = Math.ceil(height / root.cellSize / root.density)
                for (var i = 0; i < root.rows; i++) {
                    arr.push(Math.random() * -50)
                }
            } else {
                root.cols = Math.ceil(width / root.cellSize / root.density)
                for (var j = 0; j < root.cols; j++) {
                    arr.push(Math.random() * -50)
                }
            }
            root.drops = arr
            clearCanvas()
        }
        
        onPaint: {
            var ctx = getContext("2d")
            if (!ctx || root.drops.length === 0) return
            
            // Extract background RGB for fade 提取背景色用于渐隐
            var bgColor = root.backgroundColor.toString()
            var fadeAlpha = root.fadeSpeed
            
            // Fade trail 拖尾效果
            ctx.fillStyle = Qt.rgba(
                root.backgroundColor.r, 
                root.backgroundColor.g, 
                root.backgroundColor.b, 
                fadeAlpha
            )
            ctx.fillRect(0, 0, width, height)
            
            ctx.font = root.fontSize + "px monospace"
            
            var w = width, h = height
            var cs = root.cellSize * root.density
            var localDrops = root.drops
            var charLen = root._activeCharset.length
            var isHoriz = root.isHorizontal
            var dir = root.direction
            var count = isHoriz ? root.rows : root.cols
            var maxDim = isHoriz ? w : h
            
            // Note: Glow is applied per-character for head only (performance) 发光只应用于头部字符
            
            for (var i = 0; i < count; i++) {
                // Flicker skip 闪烁跳过
                if (root.flickerEnabled && Math.random() < root.flickerRate) continue
                
                var character = root._activeCharset[Math.floor(Math.random() * charLen)]
                var pos = localDrops[i] * root.cellSize
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
                if (root.perspective > 0) {
                    var centerX = w / 2, centerY = h / 2
                    var distX = (x - centerX) / centerX
                    var distY = (y - centerY) / centerY
                    var scale = 1 - root.perspective * 0.3 * (Math.abs(distX) + Math.abs(distY))
                    ctx.save()
                    ctx.translate(x, y)
                    ctx.scale(scale, scale)
                    ctx.translate(-x, -y)
                }
                
                // Interactive repulsion 交互排斥
                if (root.interactive) {
                    var dx = x - root.mousePos.x
                    var dy = y - root.mousePos.y
                    var dist = Math.sqrt(dx * dx + dy * dy)
                    if (dist < root.interactionRadius) {
                        var force = (1 - dist / root.interactionRadius) * 30
                        x += dx / dist * force
                        y += dy / dist * force
                    }
                }
                
                // Rainbow mode color 彩虹模式颜色
                var currentMainColor = root.mainColor
                var currentHeadColor = root.headColor
                if (root.rainbowMode) {
                    var hue = (root._rainbowOffset + i * 10) % 360
                    currentMainColor = Qt.hsla(hue / 360, 1, 0.5, 1)
                    currentHeadColor = Qt.hsla(hue / 360, 0.8, 0.7, 1)
                }
                
                // Glow effect (lightweight simulation) 发光效果（轻量模拟）
                if (root.glowEnabled) {
                    ctx.globalAlpha = 0.3 * root.glowIntensity
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
                var trailOffset = (dir === "up" ? -root.cellSize : root.cellSize) * 0.5
                ctx.fillText(character, x, y - trailOffset)
                
                if (root.perspective > 0) {
                    ctx.restore()
                }
                
                // Move based on direction 根据方向移动
                localDrops[i] += 0.5 + Math.random() * 0.5
                
                // Reset check 重置检查
                var shouldReset = false
                if (dir === "down" && y > h) shouldReset = true
                else if (dir === "up" && y < 0) shouldReset = true
                else if (dir === "right" && x > w) shouldReset = true
                else if (dir === "left" && x < 0) shouldReset = true
                
                if (shouldReset && Math.random() > 0.975) {
                    localDrops[i] = 0
                }
            }
            
            root.drops = localDrops
            
            // Update rainbow offset 更新彩虹偏移
            if (root.rainbowMode) {
                root._rainbowOffset = (root._rainbowOffset + 2) % 360
            }
        }
    }
    
    // Mouse tracking for interaction 鼠标交互追踪
    MouseArea {
        anchors.fill: parent
        hoverEnabled: root.interactive
        onPositionChanged: (mouse) => {
            if (root.interactive) {
                root.mousePos = Qt.point(mouse.x, mouse.y)
            }
        }
        onExited: root.mousePos = Qt.point(-1000, -1000)
    }
    
    Timer {
        interval: Math.max(16, 50 / root.speed)
        running: root.running && !root.paused && root.visible
        repeat: true
        onTriggered: canvas.requestPaint()
    }
}
