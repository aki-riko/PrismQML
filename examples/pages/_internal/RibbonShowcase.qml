// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import PrismQML as Fluent

// RibbonShowcase - Gallery card for the ribbon and app bar family
// 功能区与应用栏展示卡
// Extracted from NavigationPage so that page stays inside its line budget.
// 从 NavigationPage 抽出, 使该页面保持在行数预算内。
// Text and labels stay ASCII on purpose: the Gallery i18n contract only localizes
// user-visible literals. 文本刻意保持 ASCII: 画廊 i18n 合同只本地化用户可见文案。
ExampleCard {
    id: showcase

    title: Fluent.Translator.tr("gallery_06f15683ddc4c17a", Fluent.Translator._v)
    description: "RibbonTab / RibbonGroup / AppBarButton"

    Column {
        width: parent ? parent.width : 0
        spacing: Fluent.Enums.spacing.l

        RibbonBar {
            width: parent ? parent.width : 0

            RibbonTab {
                title: Fluent.Translator.tr("gallery_d2bb025a2e51c410", Fluent.Translator._v)
                key: "home"
                icon: Fluent.Enums.icon.ribbon

                RibbonGroup {
                    title: Fluent.Translator.tr("gallery_8c10e2c1728ddf8e", Fluent.Translator._v)

                    AppBarButton {
                        text: Fluent.Translator.tr("gallery_33517926747180e6", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.clipboard
                        menuItems: [
                            { "text": Fluent.Translator.tr("gallery_33517926747180e6", Fluent.Translator._v), "icon": Fluent.Enums.icon.clipboard },
                            { "text": Fluent.Translator.tr("gallery_9348ec48422196cd", Fluent.Translator._v), "icon": Fluent.Enums.icon.copy }
                        ]
                    }

                    AppBarButton {
                        checkable: true
                        text: Fluent.Translator.tr("gallery_5ceac65ed8ee2ca6", Fluent.Translator._v)
                        icon: Fluent.Enums.icon.text_bold
                    }
                }

                RibbonGroup {
                    title: Fluent.Translator.tr("gallery_051836569928a9f9", Fluent.Translator._v)

                    AppBarButton { text: Fluent.Translator.tr("gallery_410a8e8a6bf253ac", Fluent.Translator._v); icon: Fluent.Enums.icon.cut }
                    AppBarButton { text: Fluent.Translator.tr("gallery_63d90d977348ab1f", Fluent.Translator._v); icon: Fluent.Enums.icon.copy }
                }
            }

            RibbonTab {
                title: Fluent.Translator.tr("gallery_4268493cd34f6f48", Fluent.Translator._v)
                key: "insert"

                RibbonGroup {
                    title: Fluent.Translator.tr("gallery_c11330b85234f9c0", Fluent.Translator._v)

                    AppBarButton { text: Fluent.Translator.tr("gallery_3a5040b68abf75f9", Fluent.Translator._v); icon: Fluent.Enums.icon.select_all_on }
                    AppBarButton { text: Fluent.Translator.tr("gallery_926a50b98ece2667", Fluent.Translator._v); icon: Fluent.Enums.icon.arrow_undo }
                }
            }
        }
    }
}
