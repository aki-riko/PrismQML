// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import PrismQML as Fluent

// CommandSurfaceShowcase - Shared navigation command composition 统一导航命令组合展示
// The demo uses the public TabBar, CommandBar, Button and Separator contracts.
// 展示直接使用公开的 TabBar、CommandBar、Button 与 Separator 合同。
ExampleCard {
    id: showcase

    title: Fluent.Translator.tr("gallery_7e97e91f3221fc25", Fluent.Translator._v)
    description: "TabBar / CommandBar / Button"

    Column {
        width: parent ? parent.width : 0
        spacing: Fluent.Enums.spacing.l

        TabBar {
            id: commandTabs

            width: parent ? parent.width : 0
            tabs: [
                { title: Fluent.Translator.tr("gallery_d2bb025a2e51c410", Fluent.Translator._v), icon: Fluent.Enums.icon.ribbon },
                { title: Fluent.Translator.tr("gallery_4268493cd34f6f48", Fluent.Translator._v), icon: Fluent.Enums.icon.add }
            ]
        }

        Row {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.m
            visible: commandTabs.currentIndex === 0

            Column {
                spacing: Fluent.Enums.spacing.xs

                Label {
                    text: Fluent.Translator.tr("gallery_8c10e2c1728ddf8", Fluent.Translator._v)
                    type: Fluent.Enums.label.type_caption
                }

                Row {
                    spacing: Fluent.Enums.spacing.xs

                    Button {
                        text: Fluent.Translator.tr("gallery_33517926747180e6", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.clipboard
                        feature: Fluent.Enums.button.feature_dropdown
                        menuItems: [
                            { text: Fluent.Translator.tr("gallery_33517926747180e6", Fluent.Translator._v), icon: Fluent.Enums.icon.clipboard },
                            { text: Fluent.Translator.tr("gallery_9348ec48422196cd", Fluent.Translator._v), icon: Fluent.Enums.icon.copy }
                        ]
                    }
                    Button {
                        text: Fluent.Translator.tr("gallery_9348ec48422196cd", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.copy
                    }
                }
            }

            Separator {
                type: Fluent.Enums.separator.vertical
                lineLength: Fluent.Enums.controlSize.commandBarButtonSize * 2
            }

            Column {
                spacing: Fluent.Enums.spacing.xs

                Label {
                    text: Fluent.Translator.tr("gallery_051836569928a9f9", Fluent.Translator._v)
                    type: Fluent.Enums.label.type_caption
                }

                Row {
                    spacing: Fluent.Enums.spacing.xs

                    Button {
                        text: Fluent.Translator.tr("gallery_5ceac65ed8ee2ca6", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.text_bold
                        feature: Fluent.Enums.button.feature_toggle
                    }
                    Button {
                        text: Fluent.Translator.tr("gallery_410a8e8a6bf253ac", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.cut
                    }
                    Button {
                        text: Fluent.Translator.tr("gallery_63d90d977348ab1f", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.copy
                    }
                }
            }
        }

        Row {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.m
            visible: commandTabs.currentIndex === 1

            Column {
                spacing: Fluent.Enums.spacing.xs

                Label {
                    text: Fluent.Translator.tr("gallery_c11330b85234f9c0", Fluent.Translator._v)
                    type: Fluent.Enums.label.type_caption
                }

                CommandBar {
                    type: Fluent.Enums.commandBar.type_view
                    showLabels: true
                    primaryCommands: [
                        { text: Fluent.Translator.tr("gallery_3a5040b68abf75f9", Fluent.Translator._v), icon: Fluent.Enums.icon.select_all_on },
                        { text: Fluent.Translator.tr("gallery_926a50b98ece2667", Fluent.Translator._v), icon: Fluent.Enums.icon.arrow_undo }
                    ]
                }
            }
        }
    }
}
