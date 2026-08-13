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
                    text: Fluent.Translator.tr("gallery_e49c9ff56ab3ff33", Fluent.Translator._v)
                }

                Fluent.Label {
                    type: Fluent.Enums.label.type_caption
                    text: "prismqml.controls.containers"
                    color: Fluent.Enums.textColor.secondary
                }
            }

            // Basic cards 基础卡片
            Fluent.ExampleCard {
                title: Fluent.Translator.tr("gallery_8f4182dc6776fdf7", Fluent.Translator._v)
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
                                    text: Fluent.Translator.tr("gallery_df57da586612dd9c", Fluent.Translator._v)
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: Fluent.Translator.tr("gallery_04c86b844e5aafcd", Fluent.Translator._v)
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
                                    text: Fluent.Translator.tr("gallery_e24fa4e9e43c92ef", Fluent.Translator._v)
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: Fluent.Translator.tr("gallery_533d082728a974dd", Fluent.Translator._v)
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
                                    text: Fluent.Translator.tr("gallery_08ca5ffe51355ae3", Fluent.Translator._v)
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: Fluent.Translator.tr("gallery_a9386c7967197a97", Fluent.Translator._v)
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
                            title: Fluent.Translator.tr("gallery_f58a5cac5007dcae", Fluent.Translator._v)
                            width: Fluent.Enums.controlSize.cardContentWidth

                            Fluent.Label {
                                objectName: "galleryHeaderContent"
                                type: Fluent.Enums.label.type_body
                                width: parent.width
                                text: Fluent.Translator.tr("gallery_b23a61f0161cbed6", Fluent.Translator._v)
                            }
                        }
                    }
                }
            }

            // Specialized cards 特殊卡片
            Fluent.ExampleCard {
                title: Fluent.Translator.tr("gallery_39eeb2728ba92eaa", Fluent.Translator._v)
                description: "SettingsCard / Expander"

                Column {
                    spacing: Fluent.Enums.spacing.l

                    Fluent.ComponentCard {
                        label: "SettingsCard"

                        Fluent.SettingsCard {
                            width: Fluent.Enums.controlSize.cardContentWidth
                            title: "SettingsCard"
                            content: Fluent.Translator.tr("gallery_7f04cfa92e2a13eb", Fluent.Translator._v)
                            icon: root.iconPath("Settings")
                        }
                    }

                    Fluent.ComponentCard {
                        label: "Expander"

                        Fluent.Expander {
                            width: Fluent.Enums.controlSize.cardContentWidth
                            title: "Expander"
                            content: Fluent.Translator.tr("gallery_59c9e9c47dd38531", Fluent.Translator._v)

                            Fluent.Label {
                                type: Fluent.Enums.label.type_body
                                text: Fluent.Translator.tr("gallery_6ad8768c2dfe934f", Fluent.Translator._v)
                            }
                        }
                    }
                }
            }
        }
    }
}
