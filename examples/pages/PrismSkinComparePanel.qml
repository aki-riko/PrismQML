// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// PrismSkinComparePanel - Runtime switch and screenshot evidence 运行时切换与截图证据
Item {
    id: control

    // ==================== Signals 信号 ====================
    signal skinRequested(string value)
    signal themeRequested(string value)

    // ==================== Size 尺寸 ====================
    implicitWidth: panelColumn.implicitWidth
    implicitHeight: panelColumn.implicitHeight

    // ==================== Content 内容 ====================
    Column {
        id: panelColumn
        width: parent ? parent.width : 0
        spacing: Enums.spacing.l

        Flow {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.l

            ComponentCard {
                label: "skin"

                SegmentedControl {
                    items: [
                        { "key": "fluent", "text": "Fluent" },
                        { "key": "neo", "text": "Neo" },
                        { "key": "prism", "text": "Prism" }
                    ]
                    currentIndex: Enums.isPrismDesign ? 2 : (Enums.isNeobrutalism ? 1 : 0)
                    onItemClicked: function(index) {
                        if (index === 0) control.skinRequested("fluent")
                        if (index === 1) control.skinRequested("neobrutalism")
                        if (index === 2) control.skinRequested("prism_design")
                    }
                }
            }

            ComponentCard {
                label: "theme"

                SegmentedControl {
                    items: [
                        { "key": "light", "text": "Light" },
                        { "key": "dark", "text": "Dark" }
                    ]
                    currentIndex: Enums.isDark ? 1 : 0
                    onItemClicked: function(index) {
                        control.themeRequested(index === 0 ? "light" : "dark")
                    }
                }
            }

            ComponentCard { label: "primary"; Button { style: Enums.button.style_primary; text: "Run" } }
            ComponentCard { label: "input"; LineEdit { width: 180; placeholderText: "Search tokens" } }
            ComponentCard { label: "combo"; ComboBox { width: 160; model: ["Layer", "State", "Density"]; currentIndex: 0 } }
        }

        PrismSkinCompareStrip {
            width: parent ? parent.width : 0
        }
    }
}
