// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Button showcase page 按钮展示页面
Item {
    id: root
    readonly property int _flowSpacing: Fluent.Enums.spacing.l
    readonly property var cascadeMenuItems: [
        {
            text: Fluent.Translator.tr("gallery_4b6ded8a7f181397", Fluent.Translator._v),
            children: [
                { text: Fluent.Translator.tr("gallery_e70b45ef67e88235", Fluent.Translator._v) },
                { text: Fluent.Translator.tr("gallery_a84df74251f7f8da", Fluent.Translator._v) }
            ]
        },
        {
            text: Fluent.Translator.tr("gallery_8c2a398b8ff2e713", Fluent.Translator._v),
            children: [
                { text: Fluent.Translator.tr("gallery_a59f733a80883766", Fluent.Translator._v) },
                { text: Fluent.Translator.tr("gallery_37a1933200b062da", Fluent.Translator._v) }
            ]
        },
        { text: Fluent.Translator.tr("gallery_f48d334495f6e4f4", Fluent.Translator._v) }
    ]

    MenuCore {
        id: externalButtonMenu
        Component.onCompleted: addNodes(root.cascadeMenuItems, [])
    }

    // Icon path resolver (portable via Enums.iconPath, no source-tree dependency) 图标路径解析函数 (用模块内 Enums.iconPath, 可移植: 不依赖源码树位置)
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xl
            
            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_ad1c50c9367c756d", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }
            
            // Button - 自动类型识别
            ExampleCard {
                title: Fluent.Translator.tr("gallery_9df73ba243d56878", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_4f8d02a998ca3cb8", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: Fluent.Translator.tr("gallery_176f5d049824c610", Fluent.Translator._v); Button { text: Fluent.Translator.tr("gallery_c757c9cc2dfaf9d5", Fluent.Translator._v) } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_f674860ca9d21976", Fluent.Translator._v); Button { icon: Fluent.Enums.icon.settings } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_b994c45127c39259", Fluent.Translator._v); Button { icon: Fluent.Enums.icon.settings; text: Fluent.Translator.tr("gallery_df3d58c7d84b85f2", Fluent.Translator._v) } }
                }
            }
            
            // Button - Style样式
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ea6e9be218124517", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "style_default"; Button { style: Fluent.Enums.button.style_default; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "style_primary"; Button { style: Fluent.Enums.button.style_primary; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "style_transparent"; Button { style: Fluent.Enums.button.style_transparent; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v) } }
                    ComponentCard { label: "style_filled"; Button { style: Fluent.Enums.button.style_filled; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "style_text"; Button { style: Fluent.Enums.button.style_text; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v) } }
                    ComponentCard { label: "style_hyperlink"; Button { style: Fluent.Enums.button.style_hyperlink; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v) } }
                }
            }
            
            // Button - Shape形状
            ExampleCard {
                title: Fluent.Translator.tr("gallery_601b9653de2a0d77", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "shape_default"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_default; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "shape_pill"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_a7a690751fb88395", Fluent.Translator._v) } }
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
                    ComponentCard { label: "feature_progress_ring"; Button { feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_52c9fc80fca532de", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "feature_indeterminate_bar"; Button { feature: Fluent.Enums.button.feature_indeterminate_bar; text: Fluent.Translator.tr("gallery_eb60ca993d7b9fc9", Fluent.Translator._v) } }
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
                            menu: externalButtonMenu
                            onMenuItemClicked: function(index, text) { console.log(Fluent.Translator.tr("gallery_667bc88022ff7f7b", Fluent.Translator._v), text) }
                        }
                    }
                    ComponentCard { 
                        label: "feature_split"
                        Button { 
                            style: Fluent.Enums.button.style_primary
                            feature: Fluent.Enums.button.feature_split
                            text: Fluent.Translator.tr("gallery_afbe69d8c5f55597", Fluent.Translator._v)
                            menu: externalButtonMenu
                            onClicked: console.log(Fluent.Translator.tr("gallery_6b3dc852457b0e1b", Fluent.Translator._v))
                            onMenuItemClicked: function(index, text) { console.log(Fluent.Translator.tr("gallery_5248f80383486038", Fluent.Translator._v), text) }
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
                    ComponentCard { label: "level: 0"; Button { style: Fluent.Enums.button.style_filled; level: 0; text: Fluent.Translator.tr("gallery_d1d5597337b36ff4", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 1"; Button { style: Fluent.Enums.button.style_filled; level: 1; text: Fluent.Translator.tr("gallery_053461ce86d26572", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 2"; Button { style: Fluent.Enums.button.style_filled; level: 2; text: Fluent.Translator.tr("gallery_a8b7a4480407ac8a", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 3"; Button { style: Fluent.Enums.button.style_filled; level: 3; text: Fluent.Translator.tr("gallery_0bc1fb72ae1be5c5", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 4"; Button { style: Fluent.Enums.button.style_filled; level: 4; text: Fluent.Translator.tr("gallery_4ffef8f3113a3a11", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 5"; Button { style: Fluent.Enums.button.style_filled; level: 5; text: Fluent.Translator.tr("gallery_694b71bc8013ff43", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 6"; Button { style: Fluent.Enums.button.style_filled; level: Fluent.Enums.statusLevel.caution; text: Fluent.Translator.tr("gallery_37dd4c91d1c5b6d9", Fluent.Translator._v) } }
                }
            }
            
            // Button - Text状态等级 (Filled变体：无背景，文字为状态色)
            ExampleCard {
                title: Fluent.Translator.tr("gallery_b860143490c75717", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_57b234af8b8c5664", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "level: 0"; Button { style: Fluent.Enums.button.style_text; level: 0; text: Fluent.Translator.tr("gallery_d1d5597337b36ff4", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 1"; Button { style: Fluent.Enums.button.style_text; level: 1; text: Fluent.Translator.tr("gallery_053461ce86d26572", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 2"; Button { style: Fluent.Enums.button.style_text; level: 2; text: Fluent.Translator.tr("gallery_a8b7a4480407ac8a", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 3"; Button { style: Fluent.Enums.button.style_text; level: 3; text: Fluent.Translator.tr("gallery_0bc1fb72ae1be5c5", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 4"; Button { style: Fluent.Enums.button.style_text; level: 4; text: Fluent.Translator.tr("gallery_4ffef8f3113a3a11", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 5"; Button { style: Fluent.Enums.button.style_text; level: 5; text: Fluent.Translator.tr("gallery_694b71bc8013ff43", Fluent.Translator._v) } }
                    ComponentCard { label: "level: 6"; Button { style: Fluent.Enums.button.style_text; level: Fluent.Enums.statusLevel.caution; text: Fluent.Translator.tr("gallery_37dd4c91d1c5b6d9", Fluent.Translator._v) } }
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
            
            // ==================== Glow 泛光（正交维度） ====================
            // Glow is its own axis, so it combines with every style, shape, and
            // feature instead of occupying one style slot.
            // 泛光是独立轴, 因此与所有样式、形状与功能组合, 而不是占用一个样式位.
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a9cdbb0c43394fc0", Fluent.Translator._v)
                description: "glow + style / shape / feature"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "glow+primary"; Button { style: Fluent.Enums.button.style_primary; glow: Fluent.Enums.button.glow_accent; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "glow+default"; Button { style: Fluent.Enums.button.style_default; glow: Fluent.Enums.button.glow_accent; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "glow+filled"; Button { style: Fluent.Enums.button.style_filled; level: 1; glow: Fluent.Enums.button.glow_accent; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "glow+pill"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; glow: Fluent.Enums.button.glow_accent; text: Fluent.Translator.tr("gallery_a7a690751fb88395", Fluent.Translator._v) } }
                    ComponentCard { label: "glow+toggle"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_toggle; glow: Fluent.Enums.button.glow_accent; text: "Toggle" } }
                    ComponentCard { label: "glow+progress"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_bar; progress: 0.6; showProgress: true; glow: Fluent.Enums.button.glow_accent; text: "Progress" } }
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
                    ComponentCard { label: "default+pill"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "primary+pill"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "transparent+pill"; Button { style: Fluent.Enums.button.style_transparent; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v) } }
                    ComponentCard { label: "filled+pill"; Button { style: Fluent.Enums.button.style_filled; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "text+pill"; Button { style: Fluent.Enums.button.style_text; shape: Fluent.Enums.button.shape_pill; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v) } }
                    ComponentCard { label: "hyperlink+pill"; Button { style: Fluent.Enums.button.style_hyperlink; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v) } }
                }
            }
            
            // ==================== Style + Feature 组合 (default shape) ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_75c35fc86861bed6", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+progress_bar"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_progress_bar; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "primary+progress_bar"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_bar; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "transparent+progress_bar"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_progress_bar; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "filled+progress_bar"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_progress_bar; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "text+progress_bar"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_progress_bar; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "hyperlink+progress_bar"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_progress_bar; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a8047b2e50f7a29e", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+indeterminate_bar"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_indeterminate_bar; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "primary+indeterminate_bar"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_indeterminate_bar; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "transparent+indeterminate_bar"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_indeterminate_bar; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v) } }
                    ComponentCard { label: "filled+indeterminate_bar"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_indeterminate_bar; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "text+indeterminate_bar"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_indeterminate_bar; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v) } }
                    ComponentCard { label: "hyperlink+indeterminate_bar"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_indeterminate_bar; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v) } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_cc632cfcf0dd35cd", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+progress_ring"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "primary+progress_ring"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "transparent+progress_ring"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "filled+progress_ring"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_progress_ring; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "text+progress_ring"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_progress_ring; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "hyperlink+progress_ring"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v); progress: 0.6 } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_2bc3f24e0d0af60e", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+indeterminate_ring"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_indeterminate_ring; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "primary+indeterminate_ring"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_indeterminate_ring; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "transparent+indeterminate_ring"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_indeterminate_ring; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v) } }
                    ComponentCard { label: "filled+indeterminate_ring"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_indeterminate_ring; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "text+indeterminate_ring"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_indeterminate_ring; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v) } }
                    ComponentCard { label: "hyperlink+indeterminate_ring"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_indeterminate_ring; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v) } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_b492250d3d055380", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+toggle"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "primary+toggle"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "transparent+toggle"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v) } }
                    ComponentCard { label: "filled+toggle"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_toggle; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "text+toggle"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_toggle; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v) } }
                    ComponentCard { label: "hyperlink+toggle"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v) } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_db17582db8989f94", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+dropdown"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_dropdown; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "primary+dropdown"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_dropdown; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "transparent+dropdown"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_dropdown; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "filled+dropdown"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_dropdown; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "text+dropdown"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_dropdown; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "hyperlink+dropdown"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_dropdown; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ba20d1ba26f732c1", Fluent.Translator._v)
                description: "Button"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+split"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "primary+split"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "transparent+split"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "filled+split"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_split; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "text+split"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_split; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "hyperlink+split"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v); menuItems: ["A", "B"] } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_c6980cd8e3dd8bce", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_26b67774bf5eb396", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+countdown"; Button { style: Fluent.Enums.button.style_default; feature: Fluent.Enums.button.feature_countdown; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); countdown: 5 } }
                    ComponentCard { label: "primary+countdown"; Button { style: Fluent.Enums.button.style_primary; feature: Fluent.Enums.button.feature_countdown; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); countdown: 5 } }
                    ComponentCard { label: "transparent+countdown"; Button { style: Fluent.Enums.button.style_transparent; feature: Fluent.Enums.button.feature_countdown; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v); countdown: 5 } }
                    ComponentCard { label: "filled+countdown"; Button { style: Fluent.Enums.button.style_filled; feature: Fluent.Enums.button.feature_countdown; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v); countdown: 5 } }
                    ComponentCard { label: "text+countdown"; Button { style: Fluent.Enums.button.style_text; feature: Fluent.Enums.button.feature_countdown; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v); countdown: 5 } }
                    ComponentCard { label: "hyperlink+countdown"; Button { style: Fluent.Enums.button.style_hyperlink; feature: Fluent.Enums.button.feature_countdown; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v); countdown: 5 } }
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
                    ComponentCard { label: "pill+progress_ring"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_52c9fc80fca532de", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "pill+indeterminate_bar"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_indeterminate_bar; text: Fluent.Translator.tr("gallery_9509d263aaa4902f", Fluent.Translator._v) } }
                    ComponentCard { label: "pill+indeterminate_ring"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_indeterminate_ring; text: Fluent.Translator.tr("gallery_54a6f40169f27dea", Fluent.Translator._v) } }
                    ComponentCard { label: "pill+toggle"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: "Toggle" } }
                    ComponentCard { label: "pill+dropdown"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: "DropDown"; menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "pill+split"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_afbe69d8c5f55597", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "pill+countdown"; Button { shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_countdown; text: Fluent.Translator.tr("gallery_a7cefeb048981afc", Fluent.Translator._v); countdown: 5 } }
                }
            }
            
            // ==================== Style + Shape(pill) + Feature 三维组合 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_629e20b073cb6a0d", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_d646a41804e706bd", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+pill+toggle"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v) } }
                    ComponentCard { label: "primary+pill+toggle"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v) } }
                    ComponentCard { label: "transparent+pill+toggle"; Button { style: Fluent.Enums.button.style_transparent; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_9dddd9f908b2b956", Fluent.Translator._v) } }
                    ComponentCard { label: "filled+pill+toggle"; Button { style: Fluent.Enums.button.style_filled; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; level: 1; text: Fluent.Translator.tr("gallery_05fb7cba476bd2e9", Fluent.Translator._v) } }
                    ComponentCard { label: "text+pill+toggle"; Button { style: Fluent.Enums.button.style_text; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; level: 1; text: Fluent.Translator.tr("gallery_dd81861811e57bf7", Fluent.Translator._v) } }
                    ComponentCard { label: "hyperlink+pill+toggle"; Button { style: Fluent.Enums.button.style_hyperlink; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_toggle; text: Fluent.Translator.tr("gallery_4a63f752884096b5", Fluent.Translator._v) } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_fc8572060fdb0ca5", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_5311b05e9da8a4bf", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+pill+progress_bar"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "primary+pill+progress_bar"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_bar; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); progress: 0.6; showProgress: true } }
                    ComponentCard { label: "default+pill+progress_ring"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_52c9fc80fca532de", Fluent.Translator._v); progress: 0.6 } }
                    ComponentCard { label: "primary+pill+progress_ring"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_progress_ring; text: Fluent.Translator.tr("gallery_52c9fc80fca532de", Fluent.Translator._v); progress: 0.6 } }
                }
            }
            
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3f0653334f872292", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_a92cafc0366f99a0", Fluent.Translator._v)
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default+pill+dropdown"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "primary+pill+dropdown"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_dropdown; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); menuItems: ["A", "B", "C"] } }
                    ComponentCard { label: "default+pill+split"; Button { style: Fluent.Enums.button.style_default; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); menuItems: ["A", "B"] } }
                    ComponentCard { label: "primary+pill+split"; Button { style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; feature: Fluent.Enums.button.feature_split; text: Fluent.Translator.tr("gallery_5ccd91f4181db651", Fluent.Translator._v); menuItems: ["A", "B"] } }
                }
            }
            
            // ==================== Badge combinations 带徽章的组合 ====================
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
                            Button { id: msgBtn; style: Fluent.Enums.button.style_default; text: Fluent.Translator.tr("gallery_4da199fae933d4fa", Fluent.Translator._v) }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 5 }
                        }
                    }
                    ComponentCard { 
                        label: "primary+badge"
                        Item {
                            width: notifBtn.width
                            height: notifBtn.height
                            Button { id: notifBtn; style: Fluent.Enums.button.style_primary; text: Fluent.Translator.tr("gallery_b41f4fa6f5efb208", Fluent.Translator._v) }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 12 }
                        }
                    }
                    ComponentCard { 
                        label: "pill+badge"
                        Item {
                            width: updateBtn.width
                            height: updateBtn.height
                            Button { id: updateBtn; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_3055a035f0eb7a8b", Fluent.Translator._v) }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 99 }
                        }
                    }
                    ComponentCard { 
                        label: "primary+pill+badge"
                        Item {
                            width: alertBtn.width
                            height: alertBtn.height
                            Button { id: alertBtn; style: Fluent.Enums.button.style_primary; shape: Fluent.Enums.button.shape_pill; text: Fluent.Translator.tr("gallery_3ae491fed865a4e3", Fluent.Translator._v) }
                            Badge { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: -Fluent.Enums.spacing.xs; count: 3 }
                        }
                    }
                }
            }

            // ==================== Leaf button variants 独立按钮变体 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_131bdbe2b285c116", Fluent.Translator._v)
                description: "size / iconSize / iconColor"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard { label: "default"; Button { style: Fluent.Enums.button.style_transparent; icon: Fluent.Enums.icon.dismiss; width: Fluent.Enums.controlSize.closeButtonSize; height: width; radius: width / 2; iconSize: Fluent.Enums.iconSize.s } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_9e2482625518dad2", Fluent.Translator._v); Button { style: Fluent.Enums.button.style_transparent; icon: Fluent.Enums.icon.dismiss; width: 36; height: 36; radius: width / 2; iconSize: Fluent.Enums.iconSize.s } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_815cd4bc67c5ebe3", Fluent.Translator._v); Button { style: Fluent.Enums.button.style_transparent; icon: Fluent.Enums.icon.dismiss; width: 32; height: 32; radius: width / 2; iconSize: Fluent.Enums.iconSize.s; iconColor: Fluent.Enums.accentColor; iconHoverColor: Fluent.Enums.accentColor } }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_4f9c612da866ec55", Fluent.Translator._v)
                description: "getBackgroundColor / getBorderColor / getTextColor"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: root._flowSpacing
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_f84e05423960c3a4", Fluent.Translator._v)
                        CustomButtonCore {
                            text: Fluent.Translator.tr("gallery_4eafa9e925b30bcd", Fluent.Translator._v)
                            getBackgroundColor: function() { return Fluent.Enums.accentColorLight }
                            getBorderColor: function() { return Fluent.Enums.accentColorDark }
                            getTextColor: function() { return Fluent.Enums.foregroundColor }
                        }
                    }
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_7dd698e4206d046a", Fluent.Translator._v)
                        CustomButtonCore {
                            text: Fluent.Translator.tr("gallery_adcb8080365dd1a5", Fluent.Translator._v)
                            flat: true
                            getBackgroundColor: function() { return Fluent.Enums.transparent }
                            getBorderColor: function() { return Fluent.Enums.accentColor }
                            getTextColor: function() { return Fluent.Enums.accentColor }
                        }
                    }
                }
            }
        }
    }
}
