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

    title: "RibbonBar"
    description: "RibbonTab / RibbonGroup / AppBarButton / AppBarToggleButton / AppBarSeparator"

    Column {
        width: parent ? parent.width : 0
        spacing: Fluent.Enums.spacing.l

        RibbonBar {
            width: parent ? parent.width : 0

            RibbonTab {
                title: "Home"
                key: "home"
                icon: Fluent.Enums.icon.ribbon

                RibbonGroup {
                    title: "Clipboard"

                    AppBarButton {
                        text: "Paste"
                        icon: Fluent.Enums.icon.clipboard
                        menuItems: [
                            { "text": "Paste", "icon": Fluent.Enums.icon.clipboard },
                            { "text": "Paste special", "icon": Fluent.Enums.icon.copy }
                        ]
                    }

                    AppBarToggleButton {
                        text: "Bold"
                        icon: Fluent.Enums.icon.text_bold
                    }

                    AppBarSeparator { }
                }

                RibbonGroup {
                    title: "Edit"

                    AppBarButton { text: "Cut"; icon: Fluent.Enums.icon.cut }
                    AppBarButton { text: "Copy"; icon: Fluent.Enums.icon.copy }
                }
            }

            RibbonTab {
                title: "Insert"
                key: "insert"

                RibbonGroup {
                    title: "Selection"

                    AppBarButton { text: "Select all"; icon: Fluent.Enums.icon.select_all_on }
                    AppBarButton { text: "Undo"; icon: Fluent.Enums.icon.arrow_undo }
                }
            }
        }
    }
}
