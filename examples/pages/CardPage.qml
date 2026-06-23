// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../../prismqml/PrismQML/controls/containers"
import "../../prismqml/PrismQML/controls/settings"

// 卡片与容器页面
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
                Text { text: "卡片与容器"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.containers"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 基础卡片
            ExampleCard {
                title: "基础卡片"
                description: "Card"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "type_default"
                        Card {
                            cardType: Fluent.Enums.card.type_default
                            width: 280; height: 60
                            Column {
                                anchors.fill: parent; anchors.margins: Fluent.Enums.spacing.l; spacing: Fluent.Enums.spacing.xs
                                Text { text: "简单卡片"; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                                Text { text: "无悬停效果"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                            }
                        }
                    }
                    ComponentCard {
                        label: "type_hover"
                        Card {
                            cardType: Fluent.Enums.card.type_hover
                            width: 280; height: 60
                            Column {
                                anchors.fill: parent; anchors.margins: Fluent.Enums.spacing.l; spacing: Fluent.Enums.spacing.xs
                                Text { text: "普通卡片"; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                                Text { text: "悬停变色，不上浮"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                            }
                        }
                    }
                    ComponentCard {
                        label: "type_elevated"
                        Card {
                            cardType: Fluent.Enums.card.type_elevated
                            borderRadius: Fluent.Enums.radius.large
                            width: 280; height: 60
                            Column {
                                anchors.fill: parent; anchors.margins: Fluent.Enums.spacing.l; spacing: Fluent.Enums.spacing.xs
                                Text { text: "悬浮卡片"; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                                Text { text: "悬停上浮+阴影增强"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                            }
                        }
                    }
                    ComponentCard {
                        label: "type_header"
                        Card {
                            cardType: Fluent.Enums.card.type_header
                            borderRadius: Fluent.Enums.radius.large
                            title: "HeaderCard"
                            width: 300
                            Text { text: "带标题头的卡片"; color: Fluent.Enums.textColor.strong; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                }
            }
            
            // 特殊卡片
            ExampleCard {
                title: "特殊卡片"
                description: "SettingsCard / Expander"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "SettingsCard"
                        SettingsCard { width: 300; title: "SettingsCard"; content: "设置项卡片"; icon: iconPath("Settings") }
                    }
                    ComponentCard {
                        label: "Expander"
                        Expander { width: 300; title: "Expander"; content: "点击展开"; Text { text: "展开内容"; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily } }
                    }
                }
            }
            
        }
    }
}
