// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 特效展示页面 Effects showcase page
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.xxl
            
            // 页面标题 Page title
            Column {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.xs
                Text { text: "特效"; font.pixelSize: Enums.typography.displayLarge; font.bold: true; color: Enums.textColor.primary; font.family: Enums.fontFamily }
                Text { text: "prismqml.effects"; font.pixelSize: Enums.typography.caption; color: Enums.textColor.secondary; font.family: Enums.fontFamily }
            }
            
            // MatrixRain 展示 MatrixRain showcase
            ExampleCard {
                title: "MatrixRain - 数字雨效果"
                description: "经典黑客帝国数字雨特效，支持多种配置"
                
                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.l
                    
                    // 效果展示区域 Effect display area
                    Rectangle {
                        width: parent.width
                        height: 300
                        radius: Enums.radius.large
                        color: "transparent"
                        clip: true
                        
                        MatrixRain {
                            id: matrixRain
                            anchors.fill: parent
                            running: runningSwitch.checked
                            speed: speedSlider.value
                            fontSize: fontSizeSlider.value
                            density: densitySlider.value
                            fadeSpeed: fadeSlider.value
                        }
                        
                        // 边框 Border
                        Rectangle {
                            anchors.fill: parent
                            color: "transparent"
                            radius: Enums.radius.large
                            border.color: Enums.isDark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.1)
                            border.width: 1
                        }
                    }
                    
                    // 控制面板 Control panel
                    Row {
                        spacing: Enums.spacing.xxl
                        
                        // 运行开关 Running switch
                        ComponentCard {
                            label: "运行"
                            Toggle { id: runningSwitch; controlType: Enums.toggle.control_switch; checked: true }
                        }
                        
                        // 速度 Speed
                        ComponentCard {
                            label: "速度: " + speedSlider.value.toFixed(1)
                            Slider { id: speedSlider; width: 150; from: 0.2; to: 4.0; value: 1.0 }
                        }
                        
                        // 字体大小 Font size
                        ComponentCard {
                            label: "字体: " + Math.round(fontSizeSlider.value) + "px"
                            Slider { id: fontSizeSlider; width: 150; from: 8; to: 28; value: 14 }
                        }
                        
                        // 密度 Density
                        ComponentCard {
                            label: "密度: " + densitySlider.value.toFixed(1)
                            Slider { id: densitySlider; width: 150; from: 0.5; to: 2.0; value: 1.0 }
                        }
                        
                        // 拖尾 Fade
                        ComponentCard {
                            label: "拖尾: " + fadeSlider.value.toFixed(2)
                            Slider { id: fadeSlider; width: 150; from: 0.02; to: 0.15; value: 0.05 }
                        }
                    }
                    
                    // 主题预设 Theme presets
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: "颜色主题"; color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Repeater {
                            model: ["classic", "cyan", "amber", "red", "purple", "blue", "neon", "pink", "gold", "ocean"]
                            Button { text: modelData; onClicked: matrixRain.setTheme(modelData) }
                        }
                    }
                    
                    // 方向控制 Direction control
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: "方向"; color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Button { text: "↓ 向下"; onClicked: matrixRain.setDirection("down") }
                        Button { text: "↑ 向上"; onClicked: matrixRain.setDirection("up") }
                        Button { text: "← 向左"; onClicked: matrixRain.setDirection("left") }
                        Button { text: "→ 向右"; onClicked: matrixRain.setDirection("right") }
                    }
                    
                    // 字符集预设 Charset presets
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: "字符集"; color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Repeater {
                            model: ["japanese", "katakana", "binary", "digits", "hex", "chinese", "ascii", "greek", "runic"]
                            Button { text: modelData; onClicked: matrixRain.setCharsetPreset(modelData) }
                        }
                    }
                    
                    // 特效开关 Effect toggles
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: "特效"; color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        
                        Button {
                            id: glowBtn
                            property bool active: false
                            text: active ? "✓ 发光" : "发光"
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableGlow(1.5); else matrixRain.disableGlow() }
                        }
                        
                        Button {
                            id: flickerBtn
                            property bool active: false
                            text: active ? "✓ 闪烁" : "闪烁"
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableFlicker(0.15); else matrixRain.disableFlicker() }
                        }
                        
                        Button {
                            id: interactBtn
                            property bool active: false
                            text: active ? "✓ 鼠标交互" : "鼠标交互"
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableInteraction(80); else matrixRain.disableInteraction() }
                        }
                        
                        Button {
                            id: rainbowBtn
                            property bool active: false
                            text: active ? "✓ 彩虹模式" : "彩虹模式"
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableRainbow(); else matrixRain.disableRainbow() }
                        }
                        
                        Button {
                            id: perspectiveBtn
                            property bool active: false
                            text: active ? "✓ 3D透视" : "3D透视"
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; matrixRain.setPerspective(active ? 0.5 : 0) }
                        }
                    }
                    
                    // 控制按钮 Control buttons
                    Row {
                        spacing: Enums.spacing.l
                        Button { text: "暂停/继续"; icon: iconPath("Pause"); onClicked: matrixRain.toggle() }
                        Button { text: "重置"; icon: iconPath("ArrowSync"); onClicked: matrixRain.reset() }
                    }
                }
            }
            
            // API说明 API documentation
            ExampleCard {
                title: "MatrixRain API"
                description: "组件属性和方法说明"
                
                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.m
                    
                    Text {
                        width: parent.width
                        text: "属性: running, paused, speed, fontSize, density, fadeSpeed, direction, mainColor, headColor, backgroundColor, charset, charsetPreset, glowEnabled, glowIntensity, flickerEnabled, flickerRate, perspective, interactive, interactionRadius, rainbowMode"
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                    
                    Text {
                        width: parent.width
                        text: "方法: start(), stop(), pause(), resume(), toggle(), reset(), setTheme(name), setDirection(dir), setCharsetPreset(preset), setCustomCharset(chars), enableGlow(intensity), disableGlow(), enableFlicker(rate), disableFlicker(), enableInteraction(radius), disableInteraction(), enableRainbow(), disableRainbow(), setPerspective(value), configure(options)"
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                    
                    Text {
                        width: parent.width
                        text: "主题: classic, cyan, amber, red, purple, blue, white, pink, gold, lime, orange, teal, neon, sunset, ocean, forest, midnight"
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                    
                    Text {
                        width: parent.width
                        text: "字符集预设: japanese, katakana, binary, digits, hex, chinese, symbols, ascii, greek, runic"
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }
}
