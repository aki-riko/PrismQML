// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent
// NeoShadow is registered in the effects subdirectory module only
// NeoShadow 仅注册在 effects 子目录模块
import "../../prismqml/PrismQML/effects" as Effects

// Effects showcase page 特效展示页面
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
            
            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_8829dbcbcfce6e54", Fluent.Translator._v); font.pixelSize: Enums.typography.displayLarge; font.bold: true; color: Enums.textColor.primary; font.family: Enums.fontFamily }
            }
            
            // MatrixRain 展示 MatrixRain showcase
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a86e3cd741ce3630", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_c8c2816d5022e045", Fluent.Translator._v)
                
                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.l
                    
                    // Effect display area 效果展示区域
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
                        
                        // Border 边框
                        Rectangle {
                            anchors.fill: parent
                            color: Enums.transparent
                            radius: Enums.radius.large
                            border.color: Enums.stateColor.dialogBorder
                            border.width: 1
                        }
                    }
                    
                    // Control panel 控制面板
                    Row {
                        spacing: Enums.spacing.xxl
                        
                        // Running switch 运行开关
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_75b269496f698fae", Fluent.Translator._v)
                            Toggle { id: runningSwitch; controlType: Enums.toggle.control_switch; checked: true }
                        }
                        
                        // Speed 速度
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
                        
                        // Font size 字体大小
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
                        
                        // Density 密度
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
                        
                        // Fade trail 拖尾
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
                    
                    // Theme presets 主题预设
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_ddb3b7159fd24042", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Repeater {
                            model: ["classic", "cyan", "amber", "red", "purple", "blue", "neon", "pink", "gold", "ocean"]
                            Button { text: modelData; onClicked: matrixRain.setTheme(modelData) }
                        }
                    }
                    
                    // Direction control 方向控制
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_1121471a0ff440f8", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Button { text: Fluent.Translator.tr("gallery_42baa17ce25435d1", Fluent.Translator._v); onClicked: matrixRain.setDirection("down") }
                        Button { text: Fluent.Translator.tr("gallery_e6f1c5af9e031419", Fluent.Translator._v); onClicked: matrixRain.setDirection("up") }
                        Button { text: Fluent.Translator.tr("gallery_9498cfdf181eed8c", Fluent.Translator._v); onClicked: matrixRain.setDirection("left") }
                        Button { text: Fluent.Translator.tr("gallery_07abb4fb7aaea2e0", Fluent.Translator._v); onClicked: matrixRain.setDirection("right") }
                    }
                    
                    // Charset presets 字符集预设
                    Row {
                        spacing: Enums.spacing.l
                        Text { text: Fluent.Translator.tr("gallery_1e61cd479c3866e9", Fluent.Translator._v); color: Enums.textColor.primary; font.family: Enums.fontFamily; font.pixelSize: Enums.typography.body; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Repeater {
                            model: ["japanese", "katakana", "binary", "digits", "hex", "chinese", "ascii", "greek", "runic"]
                            Button { text: modelData; onClicked: matrixRain.setCharsetPreset(modelData) }
                        }
                    }
                    
                    // Effect toggles 特效开关
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
                    
                    // Control buttons 控制按钮
                    Row {
                        spacing: Enums.spacing.l
                        Button { text: Fluent.Translator.tr("gallery_2acba087ac8fa1a0", Fluent.Translator._v); icon: iconPath("Pause"); onClicked: matrixRain.toggle() }
                        Button { text: Fluent.Translator.tr("gallery_cb5d682bac3d1a2d", Fluent.Translator._v); icon: iconPath("ArrowSync"); onClicked: matrixRain.reset() }
                    }
                }
            }

            // ShadowedRectangle elevation levels 阴影矩形层级
            ExampleCard {
                title: Fluent.Translator.tr("gallery_505a22b51f382d76", Fluent.Translator._v)
                description: "shadowLevel: level2 / level4 / level8 / level16 / level28"
                GalleryFlow {
                    ComponentCard { label: "level2"; ShadowedRectangle { width: 104; height: 52; color: Enums.cardColor; radius: Enums.radius.large; shadowLevel: Enums.shadow.level2 } }
                    ComponentCard { label: "level4"; ShadowedRectangle { width: 104; height: 52; color: Enums.cardColor; radius: Enums.radius.large; shadowLevel: Enums.shadow.level4 } }
                    ComponentCard { label: "level8"; ShadowedRectangle { width: 104; height: 52; color: Enums.cardColor; radius: Enums.radius.large; shadowLevel: Enums.shadow.level8 } }
                    ComponentCard { label: "level16"; ShadowedRectangle { width: 104; height: 52; color: Enums.cardColor; radius: Enums.radius.large; shadowLevel: Enums.shadow.level16 } }
                    ComponentCard { label: "level28"; ShadowedRectangle { width: 104; height: 52; color: Enums.cardColor; radius: Enums.radius.large; shadowLevel: Enums.shadow.level28 } }
                }
            }

            // MultiEffect based layer effects 基于 MultiEffect 的图层效果
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a0fb1c62d0e8ce9e", Fluent.Translator._v)
                description: "layer.effect: Shadow (blur / color / verticalOffset)"
                GalleryFlow {
                    ComponentCard {
                        label: "blur 0.35"
                        Rectangle {
                            width: 96; height: 52
                            radius: Enums.radius.large
                            color: Enums.cardColor
                            layer.enabled: true
                            layer.effect: Shadow { blur: 0.35; color: Enums.shadow.level8.color; verticalOffset: 6 }
                        }
                    }
                    ComponentCard {
                        label: "blur 0.8"
                        Rectangle {
                            width: 96; height: 52
                            radius: Enums.radius.large
                            color: Enums.cardColor
                            layer.enabled: true
                            layer.effect: Shadow { blur: 0.8; color: Enums.shadow.level16.color; verticalOffset: 12 }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_0e134f5a85ab8047", Fluent.Translator._v)
                description: "layer.effect: GaussianBlur (radius / samples)"
                GalleryFlow {
                    ComponentCard {
                        label: "source"
                        Image { source: iconPath("Image"); sourceSize.width: 56; sourceSize.height: 56; width: 56; height: 56 }
                    }
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_1a352ad76d7df01f", Fluent.Translator._v)
                        Image {
                            source: iconPath("Image")
                            sourceSize.width: 56
                            sourceSize.height: 56
                            width: 56
                            height: 56
                            layer.enabled: true
                            layer.effect: GaussianBlur { radius: 8 }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_660b0a6eaaca9866", Fluent.Translator._v)
                description: "layer.effect: ColorOverlay (color)"
                GalleryFlow {
                    ComponentCard {
                        label: "source"
                        Image { source: iconPath("Color"); sourceSize.width: 56; sourceSize.height: 56; width: 56; height: 56 }
                    }
                    ComponentCard {
                        label: "accentColor"
                        Image {
                            source: iconPath("Color")
                            sourceSize.width: 56
                            sourceSize.height: 56
                            width: 56
                            height: 56
                            layer.enabled: true
                            layer.effect: ColorOverlay { color: Enums.accentColor }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_d635541163c14bd3", Fluent.Translator._v)
                description: "layer.effect: OpacityMask (mask / invert)"
                GalleryFlow {
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_82960027b0d5bcb9", Fluent.Translator._v)
                        Item {
                            width: 120; height: 56
                            Rectangle {
                                id: opacityMaskSource
                                width: 120
                                height: 56
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: Enums.accentColor }
                                    GradientStop { position: 1.0; color: Enums.transparent }
                                }
                            }
                            Rectangle {
                                anchors.fill: parent
                                color: Enums.accentColor
                                layer.enabled: true
                                layer.effect: OpacityMask { mask: opacityMaskSource }
                            }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_a206505aaa32a7d7", Fluent.Translator._v)
                description: "inset: false / true (target / blur / offset)"
                GalleryFlow {
                    ComponentCard {
                        label: "raised"
                        Rectangle {
                            id: neumorphicRaised
                            width: 96; height: 52
                            radius: Enums.radius.large
                            color: Enums.cardColor
                            NeumorphicShadow { target: neumorphicRaised }
                        }
                    }
                    ComponentCard {
                        label: "inset"
                        Rectangle {
                            id: neumorphicInset
                            width: 96; height: 52
                            radius: Enums.radius.large
                            color: Enums.cardColor
                            NeumorphicShadow { target: neumorphicInset; inset: true }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_f1c14011f0d5e40a", Fluent.Translator._v)
                description: "neobrutalism hard shadow (target / accent / offset)"
                GalleryFlow {
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_efcbe79b09214efa", Fluent.Translator._v)
                        Item {
                            width: 104; height: 60
                            Effects.NeoShadow { target: neoShadowSurface }
                            Rectangle {
                                id: neoShadowSurface
                                width: 88; height: 48
                                radius: Enums.radius.small
                                color: Enums.cardColor
                                border.width: Enums.border.thin
                                border.color: Enums.borderStrongColor
                            }
                        }
                    }
                    ComponentCard {
                        label: "accent"
                        Item {
                            width: 104; height: 60
                            Effects.NeoShadow { target: neoShadowAccentSurface; accent: true }
                            Rectangle {
                                id: neoShadowAccentSurface
                                width: 88; height: 48
                                radius: Enums.radius.small
                                color: Enums.cardColor
                                border.width: Enums.border.thin
                                border.color: Enums.borderStrongColor
                            }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_33b842f6a1293354", Fluent.Translator._v)
                description: "vintage ticket surface (patternOriginX / patternOriginY)"
                GalleryFlow {
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_e3fd227593a14aa7", Fluent.Translator._v)
                        SkinScope {
                            id: ticketPaperScope
                            width: 180
                            height: 72
                            skin: "vintage_ticket"

                            Rectangle {
                                anchors.fill: parent
                                color: ticketPaperScope.context.cardColor
                                border.width: ticketPaperScope.context.border.thin
                                border.color: ticketPaperScope.context.borderColor

                                TicketPaper {
                                    objectName: "effectsTicketPaper"
                                    anchors.fill: parent
                                    patternOriginX: 12
                                    patternOriginY: 8
                                }

                                Text {
                                    anchors.centerIn: parent
                                    text: "TicketPaper"
                                    color: ticketPaperScope.context.textColor.primary
                                    font.family: ticketPaperScope.context.fontFamily
                                    font.pixelSize: ticketPaperScope.context.typography.body
                                }
                            }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_d0c45db5a7a82f27", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_f44b8cddc2aec745", Fluent.Translator._v)
                GalleryFlow {
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_1fc0c0492445b92a", Fluent.Translator._v)
                        Rectangle {
                            id: hoverBehaviorSurface
                            width: 120; height: 52
                            radius: Enums.radius.small
                            color: hoverBehaviorArea.containsMouse ? Enums.accentColor : Enums.cardColor
                            border.width: Enums.border.thin
                            border.color: Enums.borderColor
                            HoverBehavior on color { active: hoverBehaviorArea.containsMouse }
                            MouseArea { id: hoverBehaviorArea; anchors.fill: parent; hoverEnabled: true }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_7459e7da0ad47fc7", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_a93f090d345176ea", Fluent.Translator._v)
                GalleryFlow {
                    ComponentCard {
                        label: "toggle"
                        Item {
                            width: 120; height: 68
                            Rectangle {
                                id: toggleAnimationTarget
                                anchors.horizontalCenter: parent.horizontalCenter
                                y: 4
                                width: 88; height: 36
                                radius: Enums.radius.small
                                color: toggleAnimationSwitch.checked ? Enums.accentColor : Enums.cardColor
                                border.width: Enums.border.thin
                                border.color: Enums.borderColor
                            }
                            ToggleAnimation { target: toggleAnimationTarget; running: toggleAnimationSwitch.checked }
                            Toggle {
                                id: toggleAnimationSwitch
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.bottom: parent.bottom
                                controlType: Enums.toggle.control_switch
                            }
                        }
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_dd83ba7958d4a07e", Fluent.Translator._v)
                description: "focus ring (focusSource / radius)"
                GalleryFlow {
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_4bd3a78e64b8f16f", Fluent.Translator._v)
                        Rectangle {
                            id: focusVisualTarget
                            width: 120; height: 52
                            radius: Enums.radius.small
                            color: Enums.cardColor
                            border.width: Enums.border.thin
                            border.color: Enums.borderColor
                            activeFocusOnTab: true
                            MouseArea {
                                anchors.fill: parent
                                onClicked: focusVisualTarget.forceActiveFocus()
                            }
                            FocusVisual {
                                anchors.fill: parent
                                radius: Enums.radius.small
                                focusSource: focusVisualTarget
                            }
                        }
                    }
                }
            }

        }
    }
}
