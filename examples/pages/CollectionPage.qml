// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Collection view components page 集合视图组件页面
Item {
    id: root

    // ==================== Internal Props 内部属性 ====================
    readonly property var sampleRows: [
        { "name": "Alpha" }, { "name": "Beta" }, { "name": "Gamma" },
        { "name": "Delta" }, { "name": "Epsilon" }, { "name": "Zeta" },
        { "name": "Eta" }, { "name": "Theta" }
    ]

    // ==================== Content 内容 ====================
    Component {
        id: rowDelegate

        Rectangle {
            required property int index
            required property var modelData

            color: Fluent.Enums.accentColor
            opacity: 0.25
            radius: Fluent.Enums.radius.small

            Text {
                anchors.centerIn: parent
                text: modelData.name
                color: Fluent.Enums.textColor.primary
                font.family: Fluent.Enums.fontFamily
                font.pixelSize: Fluent.Enums.typography.caption
            }
        }
    }

    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_528e5174c2d4e5c8", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }

            // ItemsView 集合视图
            ExampleCard {
                title: Fluent.Translator.tr("gallery_87877acbacde82be", Fluent.Translator._v)
                description: "selectionMode / layout / delegate"
                GalleryFlow {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "selection_single"
                        ItemsView {
                            width: 220
                            height: 200
                            model: root.sampleRows
                            selectionMode: Fluent.Enums.scroll.selection_single
                            layout: ItemsStackLayout { itemExtent: 34 }
                            delegate: rowDelegate
                        }
                    }
                    ComponentCard {
                        label: "selection_extended"
                        ItemsView {
                            width: 220
                            height: 200
                            model: root.sampleRows
                            selectionMode: Fluent.Enums.scroll.selection_extended
                            layout: ItemsStackLayout { itemExtent: 34 }
                            delegate: rowDelegate
                        }
                    }
                }
            }

            // ItemsRepeater 虚拟化重复器
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ab3bf40c6b190cd8", Fluent.Translator._v)
                description: "layout: ItemsStackLayout / ItemsUniformGridLayout"
                GalleryFlow {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "ItemsStackLayout"
                        ItemsRepeater {
                            width: 220
                            height: 200
                            model: root.sampleRows
                            layout: ItemsStackLayout { itemExtent: 34 }
                            delegate: rowDelegate
                        }
                    }
                    ComponentCard {
                        label: "ItemsUniformGridLayout"
                        ItemsRepeater {
                            width: 220
                            height: 200
                            model: root.sampleRows
                            layout: ItemsUniformGridLayout { minItemWidth: 66; itemHeight: 56 }
                            delegate: rowDelegate
                        }
                    }
                }
            }

            // StandardUICommand 标准命令
            ExampleCard {
                title: Fluent.Translator.tr("gallery_670e50d7d0ba9c9b", Fluent.Translator._v)
                description: "kind / text / shortcut / trigger()"
                GalleryFlow {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "kind: copy"
                        Column {
                            spacing: Fluent.Enums.spacing.s
                            Button { text: "trigger()"; onClicked: standardCopyCommand.trigger() }
                            Text {
                                text: standardCopyCommand.text + "  " + standardCopyCommand.shortcut
                                color: Fluent.Enums.textColor.secondary
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.caption
                            }
                            StandardUICommand { id: standardCopyCommand; kind: "copy" }
                        }
                    }
                    ComponentCard {
                        label: "kind: cut"
                        Column {
                            spacing: Fluent.Enums.spacing.s
                            Button { text: "trigger()"; onClicked: standardCutCommand.trigger() }
                            Text {
                                text: standardCutCommand.text + "  " + standardCutCommand.shortcut
                                color: Fluent.Enums.textColor.secondary
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.caption
                            }
                            StandardUICommand { id: standardCutCommand; kind: "cut" }
                        }
                    }
                    ComponentCard {
                        label: "kind: paste"
                        Column {
                            spacing: Fluent.Enums.spacing.s
                            Button { text: "trigger()"; onClicked: standardPasteCommand.trigger() }
                            Text {
                                text: standardPasteCommand.text + "  " + standardPasteCommand.shortcut
                                color: Fluent.Enums.textColor.secondary
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.caption
                            }
                            StandardUICommand { id: standardPasteCommand; kind: "paste" }
                        }
                    }
                }
            }
        }
    }
}
