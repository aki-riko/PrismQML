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
                Text { text: "按钮"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.buttons"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.tertiary; font.family: Fluent.Enums.fontFamily }
            }
            
            // Button - 自动类型识别
            ExampleCard {
                title: "Button - 自动类型识别"
                description: "仅图标→ToolButton样式，文本/图标+文本→PushButton样式"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "仅文本 (Push)"; Button { text: "Push" } }
                    ComponentCard { label: "仅图标 (Tool)"; Button { icon: Fluent.Enums.icon.settings } }
                    ComponentCard { label: "图标+文本 (Push)"; Button { icon: Fluent.Enums.icon.settings; text: "Settings" } }
                }
            }
            
            // Button - Style样式
            ExampleCard {
                title: "Button - Style样式 (6种)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Button - Shape形状 (2种)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "shape_default"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_default; text: "Default" } }
                    ComponentCard { label: "shape_pill"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: "Pill" } }
                }
            }
            
            // Button - Feature功能
            ExampleCard {
                title: "Button - Feature功能 (9种)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                            menuItems: ["选项1", "选项2", "-", "选项3"]
                            onMenuItemClicked: function(index, text) { console.log("选中:", text) }
                        }
                    }
                    ComponentCard { 
                        label: "feature_split"
                        Button { 
                            style: Fluent.Enums.button.style_primary
                            feature: Fluent.Enums.button.feature_split
                            text: "Split"
                            menuItems: ["操作A", "操作B"]
                            onClicked: console.log("主按钮点击")
                            onMenuItemClicked: function(index, text) { console.log("菜单:", text) }
                        }
                    }
                    ComponentCard { 
                        label: "feature_countdown"
                        Button { 
                            style: Fluent.Enums.button.style_primary
                            feature: Fluent.Enums.button.feature_countdown
                            text: "发送验证码"
                            countdown: 5
                            countdownText: "s"
                        }
                    }
                }
            }
            
            // Button - Filled状态等级
            ExampleCard {
                title: "Button - Filled状态等级 (6种)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Button - Text状态等级 (6种)"
                description: "Button - Filled变体：无背景，文字为状态色"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Button - ToolButton样式 (6种)"
                description: "仅图标时自动识别为ToolButton"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Button - ToolButton + Feature组合"
                description: "仅图标 + feature"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                    ComponentCard { label: "tool+dropdown"; Button { feature: Fluent.Enums.button.feature_dropdown; icon: Fluent.Enums.icon.more_vertical; menuItems: ["编辑", "删除", "-", "属性"] } }
                }
            }
            
            // ==================== Style + Shape 组合 ====================
            ExampleCard {
                title: "Style + Shape 组合"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Style + Feature 组合 (progress_bar)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+progress_bar"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_progress_bar; text: "Default"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "primary+progress_bar"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_bar; text: "Primary"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "transparent+progress_bar"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_progress_bar; text: "Transparent"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "filled+progress_bar"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_progress_bar; level: 1; text: "Filled"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "text+progress_bar"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_progress_bar; level: 1; text: "Text"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "hyperlink+progress_bar"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_progress_bar; text: "Hyperlink"; progress: 0.6; showProgress: true } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (indeterminate_bar)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+indeterminate_bar"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Default" } }
                    ComponentCard { label: "primary+indeterminate_bar"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Primary" } }
                    ComponentCard { label: "transparent+indeterminate_bar"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Transparent" } }
                    ComponentCard { label: "filled+indeterminate_bar"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_indeterminate_bar; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+indeterminate_bar"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_indeterminate_bar; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+indeterminate_bar"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_indeterminate_bar; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (progress_ring)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+progress_ring"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_progress_ring; text: "Default"; progress: 0.6 } }
                    ComponentCard { label: "primary+progress_ring"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_ring; text: "Primary"; progress: 0.6 } }
                    ComponentCard { label: "transparent+progress_ring"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_progress_ring; text: "Transparent"; progress: 0.6 } }
                    ComponentCard { label: "filled+progress_ring"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_progress_ring; level: 1; text: "Filled"; progress: 0.6 } }
                    ComponentCard { label: "text+progress_ring"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_progress_ring; level: 1; text: "Text"; progress: 0.6 } }
                    ComponentCard { label: "hyperlink+progress_ring"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_progress_ring; text: "Hyperlink"; progress: 0.6 } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (indeterminate_ring)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+indeterminate_ring"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Default" } }
                    ComponentCard { label: "primary+indeterminate_ring"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Primary" } }
                    ComponentCard { label: "transparent+indeterminate_ring"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Transparent" } }
                    ComponentCard { label: "filled+indeterminate_ring"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_indeterminate_ring; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+indeterminate_ring"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_indeterminate_ring; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+indeterminate_ring"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_indeterminate_ring; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (toggle)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+toggle"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_toggle; text: "Default" } }
                    ComponentCard { label: "primary+toggle"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_toggle; text: "Primary" } }
                    ComponentCard { label: "transparent+toggle"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_toggle; text: "Transparent" } }
                    ComponentCard { label: "filled+toggle"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+toggle"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+toggle"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_toggle; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (dropdown)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+dropdown"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_dropdown; text: "Default"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "primary+dropdown"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_dropdown; text: "Primary"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "transparent+dropdown"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_dropdown; text: "Transparent"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "filled+dropdown"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_dropdown; level: 1; text: "Filled"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "text+dropdown"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_dropdown; level: 1; text: "Text"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "hyperlink+dropdown"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_dropdown; text: "Hyperlink"; menuItems: ["A", "B", "C"] } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (split)"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+split"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_split; text: "Default"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "primary+split"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_split; text: "Primary"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "transparent+split"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_split; text: "Transparent"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "filled+split"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_split; level: 1; text: "Filled"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "text+split"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_split; level: 1; text: "Text"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "hyperlink+split"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_split; text: "Hyperlink"; menuItems: ["A", "B"] } }
                }
            }
            
            ExampleCard {
                title: "Style + Feature 组合 (countdown)"
                description: "Button - 倒计时按钮与各样式组合"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Shape(pill) + Feature 组合"
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
                title: "Style + Pill + Toggle 组合"
                description: "Button - 7种样式 × pill形状 × toggle功能"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+pill+toggle"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Default" } }
                    ComponentCard { label: "primary+pill+toggle"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Primary" } }
                    ComponentCard { label: "transparent+pill+toggle"; Button { style: Fluent.Enums.button.style_transparent; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Transparent" } }
                    ComponentCard { label: "filled+pill+toggle"; Button { style: Fluent.Enums.button.style_filled; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Filled" } }
                    ComponentCard { label: "text+pill+toggle"; Button { style: Fluent.Enums.button.style_text; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; level: 1; text: "Text" } }
                    ComponentCard { label: "hyperlink+pill+toggle"; Button { style: Fluent.Enums.button.style_hyperlink; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Hyperlink" } }
                }
            }
            
            ExampleCard {
                title: "Style + Pill + Progress 组合"
                description: "Button - 样式 × pill形状 × 进度功能"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+pill+progress_bar"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: "Default"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "primary+pill+progress_bar"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: "Primary"; progress: 0.6; showProgress: true } }
                    ComponentCard { label: "default+pill+progress_ring"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: "Ring"; progress: 0.6 } }
                    ComponentCard { label: "primary+pill+progress_ring"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: "Ring"; progress: 0.6 } }
                }
            }
            
            ExampleCard {
                title: "Style + Pill + Dropdown/Split 组合"
                description: "Button - 样式 × pill形状 × 下拉/分割功能"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "default+pill+dropdown"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: "Default"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "primary+pill+dropdown"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: "Primary"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "default+pill+split"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: "Default"; menuItems: ["A", "B"] } }
                    ComponentCard { label: "primary+pill+split"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: "Primary"; menuItems: ["A", "B"] } }
                }
            }
            
            // ==================== 带徽章的组合 ====================
            ExampleCard {
                title: "带徽章的组合 (Badge)"
                description: "Button + Badge"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
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
