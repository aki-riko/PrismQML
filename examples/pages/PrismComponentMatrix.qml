// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// PrismComponentMatrix - Prism Design component family evidence Prism Design组件族证据
ExampleCard {
    id: control

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : 0

    // ==================== Content 内容 ====================
    title: "Component Matrix"
    description: "按钮、输入、菜单、弹层、表格、进度与骨架屏共用 Prism token。"
    orientation: Qt.Vertical

    Column {
        width: parent ? parent.width : 0
        spacing: Enums.spacing.l

        Row {
            spacing: Enums.spacing.l

            ComponentCard { label: "combo"; ComboBox { width: 180; model: ["Prism Design", "Fluent", "Neobrutalism"]; currentIndex: 0 } }
            ComponentCard { label: "toggle"; Toggle { text: "Live preview"; checked: true } }
            ComponentCard { label: "slider"; Slider { width: 180; value: 64 } }
            ComponentCard { label: "progress"; Progress { type: Enums.progress.type_bar; width: 160; value: 72 } }
        }

        Row {
            spacing: Enums.spacing.l

            ComponentCard { label: "checkbox"; CheckBox { text: "Checked"; checked: true } }
            ComponentCard { label: "radio"; RadioButton { text: "Selected"; checked: true } }
            ComponentCard { label: "switch"; ToggleSwitch { text: "Enabled"; checked: true } }
            ComponentCard { label: "rating"; Rating { value: Enums.demoMetrics.ratingDefaultValue } }
        }

        Row {
            spacing: Enums.spacing.l

            ComponentCard {
                label: "menu"

                Column {
                    width: 190
                    spacing: Enums.spacing.xxs

                    MenuDelegate {
                        width: parent.width
                        text: "Open command"
                        icon: "FolderOpen"
                        selected: true
                    }

                    MenuDelegate {
                        width: parent.width
                        text: "Disabled item"
                        icon: "LockClosed"
                        itemEnabled: false
                    }
                }
            }

            ComponentCard {
                label: "tooltip"

                ShadowedRectangle {
                    width: 190
                    height: 60
                    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.large
                    color: Enums.dialogColor
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.dialogBorder
                    shadowLevel: Enums.shadow.level8

                    Label {
                        anchors.centerIn: parent
                        type: Enums.label.type_caption
                        text: "Overlay surface"
                        color: Enums.textColor.primary
                    }
                }
            }

            ComponentCard {
                label: "table"

                TableWidget {
                    width: 260
                    height: 150
                    columns: [
                        { "text": "Token", "role": "name", "width": 140 },
                        { "text": "State", "role": "state", "width": 100 }
                    ]
                    tableData: [
                        { "name": "overlay", "state": "ready" },
                        { "name": "menu item", "state": "hover" },
                        { "name": "focus ring", "state": "visible" }
                    ]
                }
            }
        }

        Row {
            spacing: Enums.spacing.l

            InfoBar { title: "Info"; content: "Overlay token"; severity: "info"; width: 280; duration: 0 }
            InfoBar { title: "Success"; content: "Semantic token"; severity: "success"; width: 280; duration: 0 }
        }

        Row {
            spacing: Enums.spacing.l

            Skeleton { width: 180; height: 14 }
            Skeleton { width: 120; height: 14 }
            Skeleton { shape: Enums.skeleton.shape_circle; width: 42; height: 42 }
        }
    }
}
