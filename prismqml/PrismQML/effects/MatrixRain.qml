// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal" as MatrixRainInternal
import "_internal/MatrixRainPresets.js" as MatrixRainPresets
import "_internal/MatrixRainCharsets.js" as MatrixRainCharsets

// MatrixRain - The Matrix digital rain effect 黑客帝国数字雨效果
// Usage 使用方式:
//   MatrixRain { anchors.fill: parent }
//   MatrixRain { direction: "up"; glowEnabled: true; charsetPreset: "binary" }

Rectangle {
    id: root
    
    // ==================== Public Props 公开属性 ====================
    // Basic 基础属性
    property bool running: true                         // Animation running 动画运行
    property bool paused: false                         // Animation paused 动画暂停
    property real speed: 1.0                            // Fall speed (0.1-5.0) 下落速度
    property int fontSize: 14                           // Character size 字符大小
    property real density: 1.0                          // Column density (0.5-2.0) 列密度
    property real fadeSpeed: 0.05                       // Trail fade (0.01-0.2) 拖尾消隐
    
    // Colors 颜色属性
    property color mainColor: Enums.isVintageTicket
        ? Enums.ticket.dividerColor : MatrixRainPresets.themes.classic.main
    property color headColor: Enums.isVintageTicket
        ? Enums.ticket.foreground : MatrixRainPresets.themes.classic.head
    property color backgroundColor: Enums.isVintageTicket
        ? Enums.ticket.background : MatrixRainPresets.themes.classic.bg
    
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
    
    // ==================== Internal Props 内部属性 ====================
    // Clamp runtime inputs before geometry, timer, and interaction math 在几何、定时器和交互计算前钳制运行时输入
    readonly property real _safeDensity: {
        if (!isFinite(density)) return 0.5
        return Math.max(0.5, density)
    }
    readonly property real _safeSpeed: {
        if (!isFinite(speed)) return 0.1
        return Math.max(0.1, speed)
    }
    readonly property real _safeInteractionRadius: {
        if (!isFinite(interactionRadius)) return 0
        return Math.max(0, interactionRadius)
    }
    property var drops: []
    property var characterSeeds: []
    property int cols: 0
    property int rows: 0
    property int cellSize: Math.max(10, fontSize + 2)
    property point mousePos: Qt.point(-1000, -1000)
    property bool isHorizontal: direction === "left" || direction === "right"
    
    // Charset presets 预设字符集
    readonly property var _charsetPresets: MatrixRainCharsets.presets
    
    // Active charset 当前使用的字符集
    readonly property string _activeCharset: charsetPreset && _charsetPresets[charsetPreset] 
        ? _charsetPresets[charsetPreset] : charset
    
    // Rainbow hue offset 彩虹色相偏移
    property real _rainbowOffset: 0

    // ==================== Signals 信号 ====================
    signal themeApplied(string themeName)

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
        var theme = MatrixRainPresets.themes[name]
        if (theme) {
            mainColor = theme.main
            headColor = theme.head
            backgroundColor = theme.bg
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
        return MatrixRainPresets.themeNames.slice()
    }

    function getAvailableCharsets() {
        return Object.keys(_charsetPresets)
    }

    function getAvailableDirections() {
        return ["down", "up", "left", "right"]
    }

    color: backgroundColor
    clip: true

    onDirectionChanged: canvas.initDrops()
    onCharsetPresetChanged: canvas.requestPaint()
    onMainColorChanged: canvas.clearCanvas()
    onHeadColorChanged: canvas.clearCanvas()
    onBackgroundColorChanged: canvas.clearCanvas()
    onDensityChanged: canvas.initDrops()
    
    MatrixRainInternal.MatrixRainCanvas {
        id: canvas
        host: root
        animationDriver: animationTimer
        anchors.fill: parent
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
    
    MatrixRainInternal.MatrixRainAnimationTimer {
        id: animationTimer
        host: root
        targetCanvas: canvas
    }
}
