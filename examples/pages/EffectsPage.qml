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
                Text { text: Fluent.Translator.tr("gallery_8829dbcbcfce6e54", Fluent.Translator._v); font.pixelSize: Enums.typography.displayLarge; font.bold: true; color: Enums.textColor.primary; font.family: Enums.fontFamily }
                Text { text: "prismqml.effects"; font.pixelSize: Enums.typography.caption; color: Enums.textColor.secondary; font.family: Enums.fontFamily }
            }
            
            // MatrixRain 展示 MatrixRain showcase
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a86e3cd741ce3630", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_c8c2816d5022e045", Fluent.Translator._v)
                
                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.l
                    
                    // 效果展示区域 Effect display area
                    Rectangle {
                        width: parent.width
                        height: 300
                        radius: Enums.radius.large
                        color: Enums.transparent
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
                            color: Enums.transparent
                            radius: Enums.radius.large
                            border.color: Enums.stateColor.dialogBorder
                            border.width: 1
                        }
                    }
                    
                    // 控制面板 Control panel
                    Row {
                        spacing: Enums.spacing.xxl
                        
                        // 运行开关 Running switch
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_75b269496f698fae", Fluent.Translator._v)
                            Toggle { id: runningSwitch; controlType: Enums.toggle.control_switch; checked: true }
                        }
                        
                        // 速度 Speed
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_2c46293d126101da", Fluent.Translator._v) + speedSlider.value.toFixed(1)
                            Slider {
                                id: speedSlider

                                width: 150
                                from: 0.2
                                to: 4.0
                                value: 1.0
                                stepSize: 0.1
                                decimals: 1
                            }
                        }
                        
                        // 字体大小 Font size
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_800b0e9e70229d11", Fluent.Translator._v) + Math.round(fontSizeSlider.value) + "px"
                            Slider {
                                id: fontSizeSlider

                                width: 150
                                from: 8
                                to: 28
                                value: 14
                                stepSize: 1
                            }
                        }
                        
                        // 密度 Density
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_76d9b92538f405c9", Fluent.Translator._v) + densitySlider.value.toFixed(1)
                            Slider {
                                id: densitySlider

                                width: 150
                                from: 0.5
                                to: 2.0
                                value: 0.7
                                stepSize: 0.1
                                decimals: 1
                            }
                        }
                        
                        // 拖尾 Fade
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_728f1239d38766e4", Fluent.Translator._v) + fadeSlider.value.toFixed(2)
                            Slider {
                                id: fadeSlider

                                width: 150
                                from: 0.02
                                to: 0.15
                                value: 0.05
                                stepSize: 0.01
                                decimals: 2
                            }
                        }
                    }
                    
                    // 主题预设 Theme presets
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_ddb3b7159fd24042", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Repeater {
                            model: ["classic", "cyan", "amber", "red", "purple", "blue", "neon", "pink", "gold", "ocean"]
                            Button { text: modelData; onClicked: matrixRain.setTheme(modelData) }
                        }
                    }
                    
                    // 方向控制 Direction control
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_1121471a0ff440f8", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Button { text: Fluent.Translator.tr("gallery_42baa17ce25435d1", Fluent.Translator._v); onClicked: matrixRain.setDirection("down") }
                        Button { text: Fluent.Translator.tr("gallery_e6f1c5af9e031419", Fluent.Translator._v); onClicked: matrixRain.setDirection("up") }
                        Button { text: Fluent.Translator.tr("gallery_9498cfdf181eed8c", Fluent.Translator._v); onClicked: matrixRain.setDirection("left") }
                        Button { text: Fluent.Translator.tr("gallery_07abb4fb7aaea2e0", Fluent.Translator._v); onClicked: matrixRain.setDirection("right") }
                    }
                    
                    // 字符集预设 Charset presets
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_1e61cd479c3866e9", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Repeater {
                            model: ["japanese", "katakana", "binary", "digits", "hex", "chinese", "ascii", "greek", "runic"]
                            Button { text: modelData; onClicked: matrixRain.setCharsetPreset(modelData) }
                        }
                    }
                    
                    // 特效开关 Effect toggles
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_8829dbcbcfce6e54", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        
                        Button {
                            id: glowBtn
                            property bool active: false
                            text: active ? Fluent.Translator.tr("gallery_320fce2a1eac1564", Fluent.Translator._v) : Fluent.Translator.tr("gallery_a9cdbb0c43394fc0", Fluent.Translator._v)
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableGlow(1.5); else matrixRain.disableGlow() }
                        }
                        
                        Button {
                            id: flickerBtn
                            property bool active: false
                            text: active ? Fluent.Translator.tr("gallery_2031e54aa0454ad2", Fluent.Translator._v) : Fluent.Translator.tr("gallery_d92003913fab9394", Fluent.Translator._v)
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableFlicker(0.15); else matrixRain.disableFlicker() }
                        }
                        
                        Button {
                            id: interactBtn
                            property bool active: false
                            text: active ? Fluent.Translator.tr("gallery_82cb35632071e977", Fluent.Translator._v) : Fluent.Translator.tr("gallery_ee9f47411e646a11", Fluent.Translator._v)
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableInteraction(80); else matrixRain.disableInteraction() }
                        }
                        
                        Button {
                            id: rainbowBtn
                            property bool active: false
                            text: active ? Fluent.Translator.tr("gallery_613a2116d3182104", Fluent.Translator._v) : Fluent.Translator.tr("gallery_1369f06017f76658", Fluent.Translator._v)
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; if (active) matrixRain.enableRainbow(); else matrixRain.disableRainbow() }
                        }
                        
                        Button {
                            id: perspectiveBtn
                            property bool active: false
                            text: active ? Fluent.Translator.tr("gallery_e233477de649edec", Fluent.Translator._v) : Fluent.Translator.tr("gallery_be3025b2d55c342d", Fluent.Translator._v)
                            style: active ? Enums.button.style_primary : Enums.button.style_default
                            onClicked: { active = !active; matrixRain.setPerspective(active ? 0.5 : 0) }
                        }
                    }
                    
                    // 控制按钮 Control buttons
                    Row {
                        spacing: Enums.spacing.l
                        Button { text: Fluent.Translator.tr("gallery_2acba087ac8fa1a0", Fluent.Translator._v); icon: iconPath("Pause"); onClicked: matrixRain.toggle() }
                        Button { text: Fluent.Translator.tr("gallery_cb5d682bac3d1a2d", Fluent.Translator._v); icon: iconPath("ArrowSync"); onClicked: matrixRain.reset() }
                    }
                }
            }
            
            // API说明 API documentation
            ExampleCard {
                title: "MatrixRain API"
                description: Fluent.Translator.tr("gallery_b27231378b8b3464", Fluent.Translator._v)
                
                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.m
                    
                    Text {
                        width: parent.width
                        text: Fluent.Translator.tr("gallery_739f3990c6763895", Fluent.Translator._v)
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                    
                    Text {
                        width: parent.width
                        text: Fluent.Translator.tr("gallery_5c9b1d8fa61c7e35", Fluent.Translator._v)
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                    
                    Text {
                        width: parent.width
                        text: Fluent.Translator.tr("gallery_01dd841942c87e0e", Fluent.Translator._v)
                        color: Enums.textColor.secondary
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        wrapMode: Text.Wrap
                    }
                    
                    Text {
                        width: parent.width
                        text: Fluent.Translator.tr("gallery_51f8c4f9e6a3e1c7", Fluent.Translator._v)
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
