// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// PrismDarkAudit - Dark mode gallery audit evidence Prism Design深色审计证据
ExampleCard {
    id: control

    // ==================== Internal Props 内部属性 ====================
    readonly property string darkAuditEvidenceKeys: "input|table|overlay|semantic|focus|selection"
    readonly property int _panelWidth: 760
    readonly property int _controlWidth: 220
    readonly property int _overlayWidth: 260

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : 0

    // ==================== Content 内容 ====================
    title: "Dark Audit"
    description: "真实输入、表格、弹层和语义反馈证明深色模式下仍有边界、层级和扫读性。"
    orientation: Qt.Vertical

    Card {
        width: parent ? parent.width : control._panelWidth
        autoHeight: true
        cardType: Enums.card.type_default

        Column {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.l

            Flow {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.l

                LineEdit {
                    width: control._controlWidth
                    text: "Focused search"
                    Component.onCompleted: forceActiveFocus()
                }

                ComboBox {
                    width: Enums.controlSize.inputDefaultWidth - Enums.spacing.xxxl
                    model: ["Overlay", "Table", "Input"]
                    currentIndex: 0
                }

                Button {
                    style: Enums.button.style_primary
                    text: "Focus"
                }
            }

            Flow {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.l

                InfoBar {
                    title: "Warning"
                    content: "Semantic color"
                    severity: "warning"
                    width: 280
                    duration: Enums.duration.persistent
                }

                InfoBar {
                    title: "Error"
                    content: "Border visible"
                    severity: "error"
                    width: 280
                    duration: Enums.duration.persistent
                }
            }

            Flow {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.l

                TableWidget {
                    width: 430
                    height: 170
                    currentRow: 1
                    selectedRows: [1]
                    columns: [
                        { "text": "Audit Item", "role": "name", "width": 190 },
                        { "text": "State", "role": "state", "width": 110 },
                        { "text": "Layer", "role": "level", "width": 110 }
                    ]
                    tableData: [
                        { "name": "dialog overlay", "state": "visible", "level": "overlay" },
                        { "name": "table row", "state": "selected", "level": "surface" },
                        { "name": "input focus", "state": "focused", "level": "raised" }
                    ]
                }

                ShadowedRectangle {
                    width: control._overlayWidth
                    height: 170
                    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.large
                    color: Enums.dialogColor
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.dialogBorder
                    shadowLevel: Enums.shadow.level8

                    Column {
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.l
                        spacing: Enums.spacing.m

                        Label {
                            type: Enums.label.type_body_strong
                            text: "Overlay surface"
                            color: Enums.textColor.primary
                        }

                        Label {
                            width: parent.width
                            type: Enums.label.type_caption
                            text: "Popup, tooltip and menu layers stay separated from dense content."
                            color: Enums.textColor.secondary
                            wrapMode: Text.Wrap
                        }

                        MenuDelegate {
                            width: parent.width
                            text: "Focused command"
                            icon: "Sparkle"
                            selected: true
                        }
                    }
                }
            }
        }
    }
}
