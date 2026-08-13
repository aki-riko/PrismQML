// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 标签与展示页面
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_16b20b501f767193", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: Fluent.Translator.tr("gallery_6eb5be42af0c58be", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.tertiary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 文本标签
            ExampleCard {
                title: Fluent.Translator.tr("gallery_8e0daec2a60a370c", Fluent.Translator._v)
                description: "Label + type"
                Column {
                    spacing: Fluent.Enums.spacing.s
                    ComponentCard { label: "type_display"; Label { type: Fluent.Enums.label.type_display; text: "Display" } }
                    ComponentCard { label: "type_title_large"; Label { type: Fluent.Enums.label.type_title_large; text: Fluent.Translator.tr("gallery_dfab9636ca22e6df", Fluent.Translator._v) } }
                    ComponentCard { label: "type_title"; Label { type: Fluent.Enums.label.type_title; text: Fluent.Translator.tr("gallery_c3405f8c7d9d392a", Fluent.Translator._v) } }
                    ComponentCard { label: "type_subtitle"; Label { type: Fluent.Enums.label.type_subtitle; text: Fluent.Translator.tr("gallery_7370212371b50c9a", Fluent.Translator._v) } }
                    ComponentCard { label: "type_body"; Label { type: Fluent.Enums.label.type_body; text: Fluent.Translator.tr("gallery_d661c3d96d53ebc0", Fluent.Translator._v) } }
                    ComponentCard { label: "type_body_strong"; Label { type: Fluent.Enums.label.type_body_strong; text: Fluent.Translator.tr("gallery_5281d52a99cf24d1", Fluent.Translator._v) } }
                    ComponentCard { label: "type_caption"; Label { type: Fluent.Enums.label.type_caption; text: Fluent.Translator.tr("gallery_0a89ad696a763093", Fluent.Translator._v) } }
                    ComponentCard { label: "type_hyperlink"; Label { type: Fluent.Enums.label.type_hyperlink; text: Fluent.Translator.tr("gallery_8f9a5b6031177e4e", Fluent.Translator._v); url: "https://github.com/aki-riko/PrismQML" } }
                }
            }
            
            // 徽章
            ExampleCard {
                title: Fluent.Translator.tr("gallery_2007e7c457991125", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_ed154f2610a9fa4f", Fluent.Translator._v)
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        ComponentCard { label: "count: 5"; Badge { count: 5 } }
                        ComponentCard { label: "count: 99"; Badge { count: 99 } }
                        ComponentCard { label: "dot"; Badge { dot: true } }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.l
                        ComponentCard { label: "info"; Badge { text: "New"; level: Fluent.Enums.statusLevel.info } }
                        ComponentCard { label: "attention"; Badge { text: Fluent.Translator.tr("gallery_4ffef8f3113a3a11", Fluent.Translator._v); level: Fluent.Enums.statusLevel.attention } }
                        ComponentCard { label: "success"; Badge { text: Fluent.Translator.tr("gallery_053461ce86d26572", Fluent.Translator._v); level: Fluent.Enums.statusLevel.success } }
                        ComponentCard { label: "error"; Badge { text: Fluent.Translator.tr("gallery_0bc1fb72ae1be5c5", Fluent.Translator._v); level: Fluent.Enums.statusLevel.error } }
                    }
                    Row {
                        spacing: Fluent.Enums.spacing.xl
                        ComponentCard { 
                            label: "Button+Badge"
                            Item {
                                width: btn1.width
                                height: btn1.height
                                Button { 
                                    id: btn1
                                    text: Fluent.Translator.tr("gallery_4da199fae933d4fa", Fluent.Translator._v)
                                }
                                Badge {
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.margins: -Fluent.Enums.spacing.xs
                                    count: 5
                                }
                            }
                        }
                        ComponentCard { 
                            label: "Button+dot"
                            Item {
                                width: btn2.width
                                height: btn2.height
                                Button { 
                                    id: btn2
                                    icon: Fluent.Enums.icon.alert
                                }
                                Badge {
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.margins: -Fluent.Enums.spacing.xxs
                                    dot: true
                                }
                            }
                        }
                    }
                }
            }
            
            // Chip（可切换芯片）
            ExampleCard {
                title: "Chip"
                description: Fluent.Translator.tr("gallery_e2040891d0422823", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.m
                    ComponentCard { label: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); Chip { text: "Attach camera"; icon: Fluent.Enums.icon.camera } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_45c21a9e1fe271db", Fluent.Translator._v); Chip { text: "Add friend"; icon: Fluent.Enums.icon.people; checked: true } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_eb6bb0da552629b5", Fluent.Translator._v); Chip { text: Fluent.Translator.tr("gallery_1d0fd5f9336d9103", Fluent.Translator._v); closable: false } }
                }
            }
            
            // Tag（状态标签）
            ExampleCard {
                title: "Tag"
                description: Fluent.Translator.tr("gallery_3cf45f685654a77b", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.m
                    ComponentCard { label: "info"; Tag { text: Fluent.Translator.tr("gallery_e7028601e7da793d", Fluent.Translator._v); status: Fluent.Enums.statusLevel.info } }
                    ComponentCard { label: "success"; Tag { text: Fluent.Translator.tr("gallery_053461ce86d26572", Fluent.Translator._v); status: Fluent.Enums.statusLevel.success } }
                    ComponentCard { label: "warning"; Tag { text: Fluent.Translator.tr("gallery_a8b7a4480407ac8a", Fluent.Translator._v); status: Fluent.Enums.statusLevel.warning } }
                    ComponentCard { label: "error"; Tag { text: Fluent.Translator.tr("gallery_0bc1fb72ae1be5c5", Fluent.Translator._v); status: Fluent.Enums.statusLevel.error } }
                    ComponentCard { label: "processing"; Tag { text: Fluent.Translator.tr("gallery_694b71bc8013ff43", Fluent.Translator._v); status: Fluent.Enums.statusLevel.processing } }
                }
            }
            
            // 头像
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3ea2d23c902cfa31", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_f2706f98edc1da71", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.xxl
                    ComponentCard { label: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); Avatar { size: 64 } }
                    ComponentCard { label: "text"; Avatar { size: 64; text: Fluent.Translator.tr("gallery_f56a049fcc23f1eb", Fluent.Translator._v) } }
                    ComponentCard { label: "source"; Avatar { size: 64; source: "qrc:/image/avatar/avatar.png" } }
                    ComponentCard { label: "size: 32"; Avatar { size: 32; text: "A" } }
                    ComponentCard { label: "size: 48"; Avatar { size: 48; text: "B" } }
                    ComponentCard { label: "size: 64"; Avatar { size: 64; text: "C" } }
                    ComponentCard { label: "size: 80"; Avatar { size: 80; text: "D" } }
                    ComponentCard { label: "Picker"; AvatarSelector { size: 64; source: "qrc:/image/avatar/avatar.png" } }
                }
            }

            // IndicatorBar（动画指示器条，三枚举组合）
            ExampleCard {
                title: "IndicatorBar"
                description: Fluent.Translator.tr("gallery_ca4db65187fdc1b1", Fluent.Translator._v)

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l

                    // 竖向
                    Row {
                        spacing: Fluent.Enums.spacing.xxl
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_7ac8a25212e4053c", Fluent.Translator._v)
                            Item {
                                width: 50; height: 56
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _vMouse1.containsMouse
                                    colorStyle: Fluent.Enums.indicatorBar.style_solid
                                    animationStyle: Fluent.Enums.indicatorBar.animation_normal
                                }
                                MouseArea { id: _vMouse1; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_33c2d796630bf460", Fluent.Translator._v)
                            Item {
                                width: 50; height: 56
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _vMouse2.containsMouse
                                    colorStyle: Fluent.Enums.indicatorBar.style_solid
                                    animationStyle: Fluent.Enums.indicatorBar.animation_bounce
                                }
                                MouseArea { id: _vMouse2; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_e8ce785b87b632cd", Fluent.Translator._v)
                            Item {
                                width: 50; height: 56
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _vMouse3.containsMouse
                                    colorStyle: Fluent.Enums.indicatorBar.style_gradient
                                    animationStyle: Fluent.Enums.indicatorBar.animation_normal
                                }
                                MouseArea { id: _vMouse3; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_9bb8e4cbe796aab6", Fluent.Translator._v)
                            Item {
                                width: 50; height: 56
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _vMouse4.containsMouse
                                    colorStyle: Fluent.Enums.indicatorBar.style_gradient
                                    animationStyle: Fluent.Enums.indicatorBar.animation_bounce
                                }
                                MouseArea { id: _vMouse4; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                    }

                    // 横向
                    Row {
                        spacing: Fluent.Enums.spacing.xxl
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_a12cb7ce87a381d7", Fluent.Translator._v)
                            Item {
                                width: 56; height: 50
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _hMouse1.containsMouse
                                    orientation: Fluent.Enums.indicatorBar.orientation_horizontal
                                    colorStyle: Fluent.Enums.indicatorBar.style_solid
                                    animationStyle: Fluent.Enums.indicatorBar.animation_bounce
                                }
                                MouseArea { id: _hMouse1; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_6555f7fe51a66978", Fluent.Translator._v)
                            Item {
                                width: 56; height: 50
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _hMouse2.containsMouse
                                    orientation: Fluent.Enums.indicatorBar.orientation_horizontal
                                    colorStyle: Fluent.Enums.indicatorBar.style_gradient
                                    animationStyle: Fluent.Enums.indicatorBar.animation_normal
                                }
                                MouseArea { id: _hMouse2; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_f63bc03b6f334002", Fluent.Translator._v)
                            Item {
                                width: 56; height: 50
                                IndicatorBar {
                                    anchors.centerIn: parent
                                    active: _hMouse3.containsMouse
                                    orientation: Fluent.Enums.indicatorBar.orientation_horizontal
                                    colorStyle: Fluent.Enums.indicatorBar.style_gradient
                                    animationStyle: Fluent.Enums.indicatorBar.animation_bounce
                                }
                                MouseArea { id: _hMouse3; anchors.fill: parent; hoverEnabled: true }
                            }
                        }
                    }
                }
            }

        }
    }
}
