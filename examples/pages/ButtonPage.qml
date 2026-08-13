// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 按钮展示页面
Item {
    id: root
    readonly property int _flowSpacing: Fluent.Enums.spacing.l

    MenuCore {
        id: externalButtonMenu
        Action { text: Fluent.Translator.tr("gallery_d54f1a0703d99975", Fluent.Translator._v) }
        Action { text: Fluent.Translator.tr("gallery_b03fab65bf7cae21", Fluent.Translator._v) }
    }

    // 图标路径解析函数 (用模块内 Enums.iconPath, 可移植: 不依赖源码树位置)
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xl
            
            // 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_ad1c50c9367c756d", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.buttons"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.tertiary; font.family: Fluent.Enums.fontFamily }
            }
            
            // Button - 自动类型识别
            ExampleCard {
                title: Fluent.Translator.tr("gallery_9df73ba243d56878", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_4f8d02a998ca3cb8", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: Fluent.Translator.tr("gallery_176f5d049824c610", Fluent.Translator._v); Button { text: "Push" } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_f674860ca9d21976", Fluent.Translator._v); Button { icon: Fluent.Enums.icon.settings } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_b994c45127c39259", Fluent.Translator._v); Button { icon: Fluent.Enums.icon.settings; text: "Settings" } }
                }
            }
            
            // Button - Style样式
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ea6e9be218124517", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "style_default"; Button { style: Fluent.Enums.button.style_default; text: "Default" } }
                    ComponentCard { label: "style_primary"; Button { style: Fluent.Enums.button.style_primary; text: "Primary" } }
                    ComponentCard { label: "style_transparent"; Button { style: Fluent.Enums.button.style_transparent; text: "Transparent" } }
                    ComponentCard { label: "style_filled"; Button { style: Fluent.Enums.button.style_filled; text: "Filled" } }
                    ComponentCard { label: "style_text"; Button { style: Fluent.Enums.button.style_text; level: 1; text: "Text" } }
                    ComponentCard { label: "style_hyperlink"; Button { style: Fluent.Enums.button.style_hyperlink; text: "Hyperlink" } }
                }
            }
            
            // Button - Shape形状
            ExampleCard {
                title: Fluent.Translator.tr("gallery_601b9653de2a0d77", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "shape_default"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_default; text: "Default" } }
                    ComponentCard { label: "shape_pill"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: "Pill" } }
                }
            }
            
            // Button - Feature功能
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a84744df3f2acf0e", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "feature_progress_bar"; Button { feature: Fluent.Enums.button.feature_progress_bar; text: "Progress"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "feature_progress_ring"; Button { feature: Fluent.Enums.button.feature_progress_ring; text: "Ring"; progress: 0.6 } }
                    ComponentCard { label: "feature_indeterminate_bar"; Button { feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Indeterminate" } }
                    ComponentCard { label: "feature_indeterminate_ring"; Button { feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Indet. Ring" } }
                    ComponentCard { 
                        label: "Badge"
                        Item {
                            width: badgeBtn.width
                            height: badgeBtn.height
                            Button { 
                                id: badgeBtn
                                text: "Badge"
                            }
                            Badge {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: -Fluent.Enums.spacing.xs
                                count: 5
                            }
                        }
                    }
                    ComponentCard { label: "feature_toggle"; Button { feature: Fluent.Enums.button.feature_toggle; text: "Toggle" } }
                    ComponentCard { 
                        label: "feature_dropdown"
                        Button { 
                            feature: Fluent.Enums.button.feature_dropdown
                            text: "DropDown"
                            menuItems: [Fluent.Translator.tr("gallery_96198518dab609f0", Fluent.Translator._v), Fluent.Translator.tr("gallery_5f04a01fe105bb4d", Fluent.Translator._v), "-", Fluent.Translator.tr("gallery_74b97119bee5c66d", Fluent.Translator._v)]
                            onMenuItemClicked: function(index, text) { console.log(Fluent.Translator.tr("gallery_667bc88022ff7f7b", Fluent.Translator._v), text) }
                        }
                    }
                    ComponentCard { 
                        label: "feature_split"
                        Button { 
                            style: Fluent.Enums.button.style_primary
                            feature: Fluent.Enums.button.feature_split
                            text: "Split"
                            menuItems: [Fluent.Translator.tr("gallery_661302e956cba192", Fluent.Translator._v), Fluent.Translator.tr("gallery_353ad4f734d73cdd", Fluent.Translator._v)]
                            onClicked: console.log(Fluent.Translator.tr("gallery_6b3dc852457b0e1b", Fluent.Translator._v))
                            onMenuItemClicked: function(index, text) { console.log(Fluent.Translator.tr("gallery_5248f80383486038", Fluent.Translator._v), text) }
                        }
                    }
                    ComponentCard {
                        label: "feature_split + MenuCore"
                        Button {
                            style: Fluent.Enums.button.style_primary
                            feature: Fluent.Enums.button.feature_split
                            text: Fluent.Translator.tr("gallery_c0dd9864b2f72353", Fluent.Translator._v)
                            menu: externalButtonMenu
                            onClicked: console.log(Fluent.Translator.tr("gallery_69b751f934f21944", Fluent.Translator._v))
                        }
                    }
                    ComponentCard { 
                        label: "feature_countdown"
                        Button { 
                            style: Fluent.Enums.button.style_primary
                            feature: Fluent.Enums.button.feature_countdown
                            text: Fluent.Translator.tr("gallery_4656fed515ae8f99", Fluent.Translator._v)
                            countdown: 5
                            countdownText: "s"
                        }
                    }
                }
            }
            
            // Button - Filled状态等级
            ExampleCard {
                title: Fluent.Translator.tr("gallery_7f767ea033795bff", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "level: 0"; Button { style: Fluent.Enums.button.style_filled; level: 0; text: "Info" } }
                    ComponentCard { label: "level: 1"; Button { style: Fluent.Enums.button.style_filled; level: 1; text: "Success" } }
                    ComponentCard { label: "level: 2"; Button { style: Fluent.Enums.button.style_filled; level: 2; text: "Warning" } }
                    ComponentCard { label: "level: 3"; Button { style: Fluent.Enums.button.style_filled; level: 3; text: "Error" } }
                    ComponentCard { label: "level: 4"; Button { style: Fluent.Enums.button.style_filled; level: 4; text: "Attention" } }
                    ComponentCard { label: "level: 5"; Button { style: Fluent.Enums.button.style_filled; level: 5; text: "Processing" } }
                }
            }
            
            // Button - Text状态等级 (Filled变体：无背景，文字为状态色)
            ExampleCard {
                title: Fluent.Translator.tr("gallery_b860143490c75717", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_57b234af8b8c5664", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "level: 0"; Button { style: Fluent.Enums.button.style_text; level: 0; text: "Info" } }
                    ComponentCard { label: "level: 1"; Button { style: Fluent.Enums.button.style_text; level: 1; text: "Success" } }
                    ComponentCard { label: "level: 2"; Button { style: Fluent.Enums.button.style_text; level: 2; text: "Warning" } }
                    ComponentCard { label: "level: 3"; Button { style: Fluent.Enums.button.style_text; level: 3; text: "Error" } }
                    ComponentCard { label: "level: 4"; Button { style: Fluent.Enums.button.style_text; level: 4; text: "Attention" } }
                    ComponentCard { label: "level: 5"; Button { style: Fluent.Enums.button.style_text; level: 5; text: "Processing" } }
                }
            }
            
            // Button - ToolButton变体 (仅图标自动识别)
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3491313cdeed61bd", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_d78dacc24620346e", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "style_default"; Button { style: Fluent.Enums.button.style_default; icon: Fluent.Enums.icon.settings } }
                    ComponentCard { label: "style_primary"; Button { style: Fluent.Enums.button.style_primary; icon: Fluent.Enums.icon.sparkle } }
                    ComponentCard { label: "style_transparent"; Button { style: Fluent.Enums.button.style_transparent; icon: Fluent.Enums.icon.eye } }
                    ComponentCard { label: "style_filled"; Button { style: Fluent.Enums.button.style_filled; level: 1; icon: Fluent.Enums.icon.checkmark } }
                    ComponentCard { label: "style_text"; Button { style: Fluent.Enums.button.style_text; level: 1; icon: Fluent.Enums.icon.heart } }
                    ComponentCard { label: "style_hyperlink"; Button { style: Fluent.Enums.button.style_hyperlink; icon: Fluent.Enums.icon.link } }
                }
            }
            
            // Button - ToolButton + Feature组合
            ExampleCard {
                title: Fluent.Translator.tr("gallery_00522ef617a7739f", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_d52c6910f1028bbf", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "tool+toggle"; Button { feature: Fluent.Enums.button.feature_toggle; icon: Fluent.Enums.icon.pin } }
                    ComponentCard { label: "tool+toggle+primary"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_toggle; icon: Fluent.Enums.icon.star } }
                    ComponentCard { label: "tool+toggle+transparent"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_toggle; icon: Fluent.Enums.icon.heart } }
                    ComponentCard { 
                        label: "tool+badge"
                        Item {
                            width: toolBadgeBtn.width
                            height: toolBadgeBtn.height
                            Button { 
                                id: toolBadgeBtn
                                icon: Fluent.Enums.icon.mail
                            }
                            Badge {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: -Fluent.Enums.spacing.xs
                                count: 5
                            }
                        }
                    }
                    ComponentCard { label: "tool+dropdown"; Button { feature: Fluent.Enums.button.feature_dropdown; icon: Fluent.Enums.icon.more_vertical; menuItems: [Fluent.Translator.tr("gallery_051836569928a9f9", Fluent.Translator._v), Fluent.Translator.tr("gallery_2f9daa828907b93f", Fluent.Translator._v), "-", Fluent.Translator.tr("gallery_86de52d178203799", Fluent.Translator._v)] } }
                }
            }
            
            // ==================== Style + Shape 组合 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_9da0be8d3424c2f6", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    // default + pill
                    ComponentCard { label: "default+pill"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; text: "Default" } }
                    ComponentCard { label: "primary+pill"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: "Primary" } }
                    ComponentCard { label: "transparent+pill"; Button { style: Fluent.Enums.button.style_transparent; shape: Fluent.Enums.button.shape_pill; text: "Transparent" } }
                    ComponentCard { label: "filled+pill"; Button { style: Fluent.Enums.button.style_filled; shape: Fluent.Enums.button.shape_pill; text: "Filled" } }
                    ComponentCard { label: "text+pill"; Button { style: Fluent.Enums.button.style_text; shape: Fluent.Enums.button.shape_pill; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+pill"; Button { style: Fluent.Enums.button.style_hyperlink; shape: Fluent.Enums.button.shape_pill; text: "Hyperlink" } }
                }
            }
            
            // ==================== Style + Feature 组合 (default shape) ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_75c35fc86861bed6", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+progress_bar"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_progress_bar; text: "Default"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "primary+progress_bar"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_bar; text: "Primary"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "transparent+progress_bar"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_progress_bar; text: "Transparent"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "filled+progress_bar"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_progress_bar; level: 1; text: "Filled"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "text+progress_bar"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_progress_bar; level: 1; text: "Text"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "hyperlink+progress_bar"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_progress_bar; text: "Hyperlink"; progress: 0.6; showProgress: true } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a8047b2e50f7a29e", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+indeterminate_bar"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Default" } }
                    ComponentCard { label: "primary+indeterminate_bar"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Primary" } }
                    ComponentCard { label: "transparent+indeterminate_bar"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Transparent" } }
                    ComponentCard { label: "filled+indeterminate_bar"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_indeterminate_bar; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+indeterminate_bar"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_indeterminate_bar; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+indeterminate_bar"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_cc632cfcf0dd35cd", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+progress_ring"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_progress_ring; text: "Default"; progress: 0.6 } }
                    ComponentCard { label: "primary+progress_ring"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_ring; text: "Primary"; progress: 0.6 } }
                    ComponentCard { label: "transparent+progress_ring"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_progress_ring; text: "Transparent"; progress: 0.6 } }
                    ComponentCard { label: "filled+progress_ring"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_progress_ring; level: 1; text: "Filled"; progress: 0.6 } }
                    ComponentCard { label: "text+progress_ring"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_progress_ring; level: 1; text: "Text"; progress: 0.6 } }
                    ComponentCard { label: "hyperlink+progress_ring"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_progress_ring; text: "Hyperlink"; progress: 0.6 } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_2bc3f24e0d0af60e", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+indeterminate_ring"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Default" } }
                    ComponentCard { label: "primary+indeterminate_ring"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Primary" } }
                    ComponentCard { label: "transparent+indeterminate_ring"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Transparent" } }
                    ComponentCard { label: "filled+indeterminate_ring"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_indeterminate_ring; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+indeterminate_ring"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_indeterminate_ring; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+indeterminate_ring"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_b492250d3d055380", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+toggle"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_toggle; text: "Default" } }
                    ComponentCard { label: "primary+toggle"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_toggle; text: "Primary" } }
                    ComponentCard { label: "transparent+toggle"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_toggle; text: "Transparent" } }
                    ComponentCard { label: "filled+toggle"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+toggle"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+toggle"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_toggle; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_db17582db8989f94", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+dropdown"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_dropdown; text: "Default"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "primary+dropdown"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_dropdown; text: "Primary"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "transparent+dropdown"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_dropdown; text: "Transparent"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "filled+dropdown"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_dropdown; level: 1; text: "Filled"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "text+dropdown"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_dropdown; level: 1; text: "Text"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "hyperlink+dropdown"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_dropdown; text: "Hyperlink"; menuItems: ["A", "B", "C"] } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ba20d1ba26f732c1", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+split"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_split; text: "Default"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "primary+split"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_split; text: "Primary"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "transparent+split"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_split; text: "Transparent"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "filled+split"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_split; level: 1; text: "Filled"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "text+split"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_split; level: 1; text: "Text"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "hyperlink+split"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_split; text: "Hyperlink"; menuItems: ["A", "B"] } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_c6980cd8e3dd8bce", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_26b67774bf5eb396", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+countdown"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_countdown; text: "Default"; countdown: 5 } }
                    ComponentCard { label: "primary+countdown"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_countdown; text: "Primary"; countdown: 5 } }
                    ComponentCard { label: "transparent+countdown"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_countdown; text: "Transparent"; countdown: 5 } }
                    ComponentCard { label: "filled+countdown"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_countdown; level: 1; text: "Filled"; countdown: 5 } }
                    ComponentCard { label: "text+countdown"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_countdown; level: 1; text: "Text"; countdown: 5 } }
                    ComponentCard { label: "hyperlink+countdown"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_countdown; text: "Hyperlink"; countdown: 5 } }
                }
            }
            
            // ==================== Shape + Feature 组合 (pill shape) ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_fbe90a9a175d9f91", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "pill+progress_bar"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: "Progress"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "pill+progress_ring"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: "Ring"; progress: 0.6 } }
                    ComponentCard { label: "pill+indeterminate_bar"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Indet Bar" } }
                    ComponentCard { label: "pill+indeterminate_ring"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Indet Ring" } }
                    ComponentCard { label: "pill+toggle"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Toggle" } }
                    ComponentCard { label: "pill+dropdown"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: "DropDown"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "pill+split"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: "Split"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "pill+countdown"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_countdown; text: "Countdown"; countdown: 5 } }
                }
            }
            
            // ==================== Style + Shape(pill) + Feature 三维组合 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_629e20b073cb6a0d", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_d646a41804e706bd", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+pill+toggle"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Default" } }
                    ComponentCard { label: "primary+pill+toggle"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Primary" } }
                    ComponentCard { label: "transparent+pill+toggle"; Button { style: Fluent.Enums.button.style_transparent; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Transparent" } }
                    ComponentCard { label: "filled+pill+toggle"; Button { style: Fluent.Enums.button.style_filled; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+pill+toggle"; Button { style: Fluent.Enums.button.style_text; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+pill+toggle"; Button { style: Fluent.Enums.button.style_hyperlink; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_fc8572060fdb0ca5", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_5311b05e9da8a4bf", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+pill+progress_bar"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: "Default"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "primary+pill+progress_bar"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: "Primary"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "default+pill+progress_ring"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: "Ring"; progress: 0.6 } }
                    ComponentCard { label: "primary+pill+progress_ring"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: "Ring"; progress: 0.6 } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3f0653334f872292", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_a92cafc0366f99a0", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+pill+dropdown"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: "Default"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "primary+pill+dropdown"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: "Primary"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "default+pill+split"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: "Default"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "primary+pill+split"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: "Primary"; menuItems: ["A", "B"] } }
                }
            }
            
            // ==================== 带徽章的组合 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_1eefca4b4783ce1d", Fluent.Translator._v)
                description: "Button + Badge"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { 
                        label: "default+badge"
                        Item {
                            width: msgBtn.width
                            height: msgBtn.height
                            Button { id: msgBtn; style: Fluent.Enums.button.style_default; text: "Messages" }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 5 }
                        }
                    }
                    ComponentCard { 
                        label: "primary+badge"
                        Item {
                            width: notifBtn.width
                            height: notifBtn.height
                            Button { id: notifBtn; style: Fluent.Enums.button.style_primary; text: "Notifications" }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 12 }
                        }
                    }
                    ComponentCard { 
                        label: "pill+badge"
                        Item {
                            width: updateBtn.width
                            height: updateBtn.height
                            Button { id: updateBtn; shape: Fluent.Enums.button.shape_pill; text: "Updates" }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 99 }
                        }
                    }
                    ComponentCard { 
                        label: "primary+pill+badge"
                        Item {
                            width: alertBtn.width
                            height: alertBtn.height
                            Button { id: alertBtn; style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: "Alerts" }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 3 }
                        }
                    }
                }
            }
        }
    }
}
