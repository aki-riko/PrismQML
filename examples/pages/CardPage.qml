// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML as Fluent

// CardPage - Card and container gallery 卡片与容器展示页
Item {
    id: root

    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }

    Fluent.ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs

                Fluent.Label {
                    type: Fluent.Enums.label.type_title
                    text: "卡片与容器"
                }

                Fluent.Label {
                    type: Fluent.Enums.label.type_caption
                    text: "prismqml.controls.containers"
                    color: Fluent.Enums.textColor.secondary
                }
            }

            // Basic cards 基础卡片
            Fluent.ExampleCard {
                title: "基础卡片"
                description: "Card · contentPadding / autoHeight"

                Column {
                    spacing: Fluent.Enums.spacing.l

                    Fluent.ComponentCard {
                        label: "type_default"

                        Fluent.Card {
                            objectName: "galleryDefaultCard"
                            cardType: Fluent.Enums.card.type_default
                            autoHeight: true
                            width: Fluent.Enums.controlSize.cardContentWidth

                            Column {
                                objectName: "galleryDefaultContent"
                                width: parent.width
                                spacing: Fluent.Enums.spacing.xs

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_body_strong
                                    text: "简单卡片"
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: "无悬停效果"
                                    color: Fluent.Enums.textColor.secondary
                                }
                            }
                        }
                    }

                    Fluent.ComponentCard {
                        label: "type_hover"

                        Fluent.Card {
                            objectName: "galleryHoverCard"
                            cardType: Fluent.Enums.card.type_hover
                            autoHeight: true
                            width: Fluent.Enums.controlSize.cardContentWidth

                            Column {
                                objectName: "galleryHoverContent"
                                width: parent.width
                                spacing: Fluent.Enums.spacing.xs

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_body_strong
                                    text: "普通卡片"
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: "悬停变色，不上浮"
                                    color: Fluent.Enums.textColor.secondary
                                }
                            }
                        }
                    }

                    Fluent.ComponentCard {
                        label: "type_elevated"

                        Fluent.Card {
                            objectName: "galleryElevatedCard"
                            cardType: Fluent.Enums.card.type_elevated
                            autoHeight: true
                            width: Fluent.Enums.controlSize.cardContentWidth

                            Column {
                                objectName: "galleryElevatedContent"
                                width: parent.width
                                spacing: Fluent.Enums.spacing.xs

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_body_strong
                                    text: "悬浮卡片"
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: "悬停上浮并增强阴影"
                                    color: Fluent.Enums.textColor.secondary
                                }
                            }
                        }
                    }

                    Fluent.ComponentCard {
                        label: "type_header"

                        Fluent.Card {
                            objectName: "galleryHeaderCard"
                            cardType: Fluent.Enums.card.type_header
                            title: "标题卡片"
                            width: Fluent.Enums.controlSize.cardContentWidth

                            Fluent.Label {
                                objectName: "galleryHeaderContent"
                                type: Fluent.Enums.label.type_body
                                width: parent.width
                                text: "带独立标题区域的卡片"
                            }
                        }
                    }
                }
            }

            // Specialized cards 特殊卡片
            Fluent.ExampleCard {
                title: "特殊卡片"
                description: "SettingsCard / Expander"

                Column {
                    spacing: Fluent.Enums.spacing.l

                    Fluent.ComponentCard {
                        label: "SettingsCard"

                        Fluent.SettingsCard {
                            width: Fluent.Enums.controlSize.cardContentWidth
                            title: "SettingsCard"
                            content: "设置项卡片"
                            icon: root.iconPath("Settings")
                        }
                    }

                    Fluent.ComponentCard {
                        label: "Expander"

                        Fluent.Expander {
                            width: Fluent.Enums.controlSize.cardContentWidth
                            title: "Expander"
                            content: "点击展开"

                            Fluent.Label {
                                type: Fluent.Enums.label.type_body
                                text: "展开内容"
                            }
                        }
                    }
                }
            }
        }
    }
}
