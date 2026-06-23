// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../../prismqml/PrismQML/controls/buttons"
import "../../prismqml/PrismQML/controls/data"
import "../../prismqml/PrismQML/controls/containers"
import "../../prismqml/PrismQML/controls/icons"
import "../../prismqml/PrismQML/controls/feedback"
import "../../prismqml/PrismQML/controls/inputs"

// 标签与展示页面
Item {
    id: root
    
    function iconPath(name) {
        return Qt.resolvedUrl("../../prismqml/PrismQML/controls/icons/fluent/" + name + ".svg")
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
                Text { text: "标签与徽章"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "Labels, Badges, Chips, Tags"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.tertiary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 文本标签
            ExampleCard {
                title: "文本标签"
                description: "Label + type"
                Column {
                    spacing: Fluent.Enums.spacing.s
                    ComponentCard { label: "type_display"; Label { type: Fluent.Enums.label.type_display; text: "Display" } }
                    ComponentCard { label: "type_title_large"; Label { type: Fluent.Enums.label.type_title_large; text: "大标题" } }
                    ComponentCard { label: "type_title"; Label { type: Fluent.Enums.label.type_title; text: "标题" } }
                    ComponentCard { label: "type_subtitle"; Label { type: Fluent.Enums.label.type_subtitle; text: "副标题" } }
                    ComponentCard { label: "type_body"; Label { type: Fluent.Enums.label.type_body; text: "正文" } }
                    ComponentCard { label: "type_body_strong"; Label { type: Fluent.Enums.label.type_body_strong; text: "正文加粗" } }
                    ComponentCard { label: "type_caption"; Label { type: Fluent.Enums.label.type_caption; text: "辅助文字" } }
                    ComponentCard { label: "type_hyperlink"; Label { type: Fluent.Enums.label.type_hyperlink; text: "超链接文本"; url: "https://example.com" } }
                }
            }
            
            // 徽章
            ExampleCard {
                title: "徽章"
                description: "Badge - 统一徽章组件"
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
                        ComponentCard { label: "attention"; Badge { text: "注意"; level: Fluent.Enums.statusLevel.attention } }
                        ComponentCard { label: "success"; Badge { text: "成功"; level: Fluent.Enums.statusLevel.success } }
                        ComponentCard { label: "error"; Badge { text: "错误"; level: Fluent.Enums.statusLevel.error } }
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
                                    text: "消息"
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
                description: "可切换芯片标签"
                Row {
                    spacing: Fluent.Enums.spacing.m
                    ComponentCard { label: "默认"; Chip { text: "Attach camera"; icon: Fluent.Enums.icon.camera } }
                    ComponentCard { label: "选中"; Chip { text: "Add friend"; icon: Fluent.Enums.icon.people; checked: true } }
                    ComponentCard { label: "无关闭"; Chip { text: "标签"; closable: false } }
                }
            }
            
            // Tag（状态标签）
            ExampleCard {
                title: "Tag"
                description: "状态标签"
                Row {
                    spacing: Fluent.Enums.spacing.m
                    ComponentCard { label: "info"; Tag { text: "信息"; status: Fluent.Enums.statusLevel.info } }
                    ComponentCard { label: "success"; Tag { text: "成功"; status: Fluent.Enums.statusLevel.success } }
                    ComponentCard { label: "warning"; Tag { text: "警告"; status: Fluent.Enums.statusLevel.warning } }
                    ComponentCard { label: "error"; Tag { text: "错误"; status: Fluent.Enums.statusLevel.error } }
                    ComponentCard { label: "processing"; Tag { text: "处理中"; status: Fluent.Enums.statusLevel.processing } }
                }
            }
            
            // 头像
            ExampleCard {
                title: "头像"
                description: "Avatar / AvatarSelector - source(图片) / text(文字) / size(尺寸)"
                Flow {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.xxl
                    ComponentCard { label: "默认"; Avatar { size: 64 } }
                    ComponentCard { label: "text"; Avatar { size: 64; text: "张" } }
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
                description: "动画指示器/重音条 - colorStyle × animationStyle × orientation，点击卡片切换 active 状态"

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l

                    // 竖向
                    Row {
                        spacing: Fluent.Enums.spacing.xxl
                        ComponentCard {
                            label: "纯色 · 普通"
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
                            label: "纯色 · 回弹"
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
                            label: "渐变 · 普通"
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
                            label: "渐变 · 回弹"
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
                            label: "横向 · 纯色 · 回弹"
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
                            label: "横向 · 渐变 · 普通"
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
                            label: "横向 · 渐变 · 回弹"
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
