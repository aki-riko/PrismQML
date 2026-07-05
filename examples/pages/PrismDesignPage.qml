// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// PrismDesignPage - Prism Design gallery evidence Prism Design图库验收页
Item {
    id: root

    // ==================== Internal Props 内部属性 ====================
    readonly property var surfaceTokens: [
        { "name": "background", "value": Enums.backgroundColor },
        { "name": "surface", "value": Enums.surfaceColor },
        { "name": "raised", "value": Enums.cardColor },
        { "name": "overlay", "value": Enums.dialogColor },
        { "name": "header", "value": Enums.headerColor },
        { "name": "table", "value": Enums.tableBgColor }
    ]
    readonly property var stateTokens: [
        { "name": "hover", "value": Enums.hoverColor },
        { "name": "pressed", "value": Enums.pressedColor },
        { "name": "selected", "value": Enums.selectedColor },
        { "name": "border", "value": Enums.borderColor },
        { "name": "divider", "value": Enums.dividerColor },
        { "name": "accent", "value": Enums.accentColor }
    ]
    readonly property var chartTokens: Enums.chartColors.palette
    readonly property string galleryEvidenceViewKeys: "Token Board|State Wall|Component Matrix|Three Skin Compare|Real App Surface|Dark Audit"

    // ==================== Internal Methods 内部方法 ====================
    function setSkin(value) { if (ThemeManager) ThemeManager.setSkinFromQml(value) }
    function setTheme(value) { if (ThemeManager) ThemeManager.setThemeFromQml(value) }

    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.xxl

            // ==================== Header 头部 ====================
            Column {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.xs

                Text {
                    text: "Prism Design"
                    font.pixelSize: Enums.typography.displayLarge
                    font.bold: true
                    color: Enums.textColor.primary
                    font.family: Enums.fontFamily
                }

                Text {
                    text: "prismqml.skin.prism_design"
                    font.pixelSize: Enums.typography.caption
                    color: Enums.textColor.tertiary
                    font.family: Enums.fontFamily
                }
            }

            // ==================== Skin Switch 皮肤切换 ====================
            ExampleCard {
                title: "Three Skin Compare"
                description: "同一场景由脚本真实渲染为三套 skin 的 light/dark 截图，运行时切换用于继续审计当前页面。"
                orientation: Qt.Vertical

                PrismSkinComparePanel {
                    width: parent ? parent.width : 0
                    onSkinRequested: function(value) { root.setSkin(value) }
                    onThemeRequested: function(value) { root.setTheme(value) }
                }
            }

            // ==================== Token Board Token看板 ====================
            ExampleCard {
                title: "Token Board"
                description: "Surface、state、chart token 均来自 Enums，不在控件里散写色值。"
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.l

                    Text {
                        text: "Surfaces"
                        font.pixelSize: Enums.typography.subtitle
                        font.bold: true
                        color: Enums.textColor.primary
                        font.family: Enums.fontFamily
                    }

                    Flow {
                        width: parent ? parent.width : 0
                        spacing: Enums.spacing.l

                        Repeater {
                            model: root.surfaceTokens

                            Rectangle {
                                width: 150
                                height: 74
                                radius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.large
                                color: modelData.value
                                border.width: Enums.border.thin
                                border.color: Enums.borderColor

                                Column {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.bottom: parent.bottom
                                    anchors.margins: Enums.spacing.m
                                    spacing: Enums.spacing.xxs

                                    Text {
                                        text: modelData.name
                                        font.pixelSize: Enums.typography.body
                                        font.bold: true
                                        color: Enums.textColor.primary
                                        font.family: Enums.fontFamily
                                    }

                                    Text {
                                        text: modelData.value.toString().toUpperCase()
                                        font.pixelSize: Enums.typography.caption
                                        color: Enums.textColor.secondary
                                        font.family: Enums.fontFamily
                                    }
                                }
                            }
                        }
                    }

                    Text {
                        text: "States"
                        font.pixelSize: Enums.typography.subtitle
                        font.bold: true
                        color: Enums.textColor.primary
                        font.family: Enums.fontFamily
                    }

                    Flow {
                        width: parent ? parent.width : 0
                        spacing: Enums.spacing.l

                        Repeater {
                            model: root.stateTokens

                            Rectangle {
                                width: 150
                                height: 54
                                radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
                                color: modelData.value
                                border.width: Enums.border.thin
                                border.color: Enums.borderColor

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.name
                                    font.pixelSize: Enums.typography.body
                                    font.bold: true
                                    color: Enums.textColor.primary
                                    font.family: Enums.fontFamily
                                }
                            }
                        }
                    }

                    Text {
                        text: "Chart Palette"
                        font.pixelSize: Enums.typography.subtitle
                        font.bold: true
                        color: Enums.textColor.primary
                        font.family: Enums.fontFamily
                    }

                    Row {
                        spacing: Enums.spacing.s

                        Repeater {
                            model: root.chartTokens

                            Rectangle {
                                width: 34
                                height: 34
                                radius: Enums.radius.small
                                color: modelData
                                border.width: Enums.border.thin
                                border.color: Enums.borderColor
                            }
                        }
                    }
                }
            }

            // ==================== State Wall 状态墙 ====================
            ExampleCard {
                title: "State Wall"
                description: "按钮、输入、分段控件、语义反馈在同一 surface 上覆盖常见状态。"

                Flow {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.l

                    ComponentCard { label: "default"; Button { text: "Default" } }
                    ComponentCard { label: "primary"; Button { style: Enums.button.style_primary; text: "Primary" } }
                    ComponentCard { label: "text"; Button { style: Enums.button.style_text; text: "Text" } }
                    ComponentCard { label: "disabled"; Button { text: "Disabled"; enabled: false } }
                    ComponentCard { label: "line edit"; LineEdit { width: 180; text: "PrismQML" } }
                    ComponentCard { label: "disabled input"; LineEdit { width: 180; placeholderText: "Disabled"; enabled: false } }
                    ComponentCard {
                        label: "segmented"
                        SegmentedControl {
                            items: ["Tokens", "States", "App"]
                            currentIndex: 1
                        }
                    }
                }
            }

            // ==================== Component Matrix 组件矩阵 ====================
            PrismComponentMatrix {
                width: parent ? parent.width : 0
            }

            // ==================== Special Components 特殊组件 ====================
            ExampleCard {
                title: "Special Components"
                description: "Chat、Code、ColorPicker、Chart 等非基础控件同样接入 Prism 几何和层级。"
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Enums.spacing.l

                    Row {
                        spacing: Enums.spacing.l

                        ComponentCard {
                            label: "chat"
                            ChatBubble {
                                width: 280
                                role: "assistant"
                                content: "Prism keeps dense tools readable."
                                timestamp: "12:24"
                            }
                        }

                        ComponentCard {
                            label: "code"
                            CodeBlock {
                                width: 260
                                language: "qml"
                                code: "Button {\\n    style: Enums.button.style_primary\\n}"
                            }
                        }
                    }

                    Row {
                        spacing: Enums.spacing.l

                        ComponentCard {
                            label: "color"
                            ColorPicker {
                                type: Enums.colorPicker.type_picker
                            }
                        }

                        ComponentCard {
                            label: "chart"
                            ChartView {
                                width: 260
                                height: 180
                                title: "Throughput"
                                chartData: [{ "label": "UI", "value": 42 }, { "label": "QML", "value": 68 }, { "label": "Docs", "value": 34 }]
                                series: [{ "name": "Build", "values": [42, 68, 34] }, { "name": "Audit", "values": [24, 52, 46] }]
                                showLegend: true
                                dataZoomEnabled: true
                            }
                        }
                    }
                }
            }

            // ==================== Dark Audit 深色审计 ====================
            ExampleCard {
                title: "Dark Audit"
                description: "表格、输入、弹层和语义反馈在深色模式下必须仍有边界和层级。"
                orientation: Qt.Vertical

                Card {
                    width: parent ? parent.width : 760
                    autoHeight: true
                    cardType: Enums.card.type_default

                    Column {
                        width: parent ? parent.width : 0
                        spacing: Enums.spacing.l

                        Row {
                            spacing: Enums.spacing.l

                            LineEdit {
                                width: 220
                                placeholderText: "Search dark audit"
                            }

                            ComboBox {
                                width: 160
                                model: ["Overlay", "Table", "Input"]
                                currentIndex: 0
                            }

                            Button {
                                style: Enums.button.style_primary
                                text: "Focus"
                            }
                        }

                        Row {
                            spacing: Enums.spacing.l
                            InfoBar { title: "Warning"; content: "Semantic color"; severity: "warning"; width: 280; duration: 0 }
                            InfoBar { title: "Error"; content: "Border visible"; severity: "error"; width: 280; duration: 0 }
                        }

                        Column {
                            width: parent.width
                            spacing: 0

                            Repeater {
                                model: [
                                    { "name": "dialog overlay", "state": "visible", "level": "overlay" },
                                    { "name": "table row", "state": "selected", "level": "surface" },
                                    { "name": "input focus", "state": "focused", "level": "raised" }
                                ]

                                Rectangle {
                                    width: parent.width
                                    height: 42
                                    color: index % 2 === 0 ? Enums.tableBgColor : Enums.alternateRowColor
                                    border.width: index === 1 ? Enums.border.thin : 0
                                    border.color: Enums.borderColor

                                    Row {
                                        anchors.fill: parent
                                        anchors.leftMargin: Enums.spacing.l
                                        anchors.rightMargin: Enums.spacing.l
                                        spacing: Enums.spacing.l

                                        Text {
                                            width: 180
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.name
                                            font.pixelSize: Enums.typography.body
                                            color: Enums.textColor.primary
                                            font.family: Enums.fontFamily
                                        }

                                        Text {
                                            width: 120
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.state
                                            font.pixelSize: Enums.typography.caption
                                            color: Enums.accentColor
                                            font.family: Enums.fontFamily
                                        }

                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.level
                                            font.pixelSize: Enums.typography.caption
                                            color: Enums.textColor.secondary
                                            font.family: Enums.fontFamily
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ==================== Real App Surface 真实应用界面 ====================
            ExampleCard {
                title: "Real App Surface"
                description: "接近真实桌面工具的密度、层级、表格与操作栏。"
                orientation: Qt.Vertical

                Card {
                    width: parent ? parent.width : 760
                    autoHeight: true
                    cardType: Enums.card.type_header
                    title: "Build Monitor"

                    Column {
                        width: parent ? parent.width : 0
                        spacing: Enums.spacing.l

                        Row {
                            spacing: Enums.spacing.l
                            Button { style: Enums.button.style_primary; text: "Deploy" }
                            Button { text: "Preview" }
                            LineEdit { width: 220; placeholderText: "Filter runs" }
                            ComboBox { width: 160; model: ["All states", "Success", "Warning", "Failed"]; currentIndex: 0 }
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: Enums.dividerColor
                        }

                        Column {
                            width: parent.width
                            spacing: 0

                            Repeater {
                                model: [
                                    { "name": "windows-wheel", "state": "success", "progress": 100 },
                                    { "name": "linux-wheel", "state": "processing", "progress": 72 },
                                    { "name": "macos-wheel", "state": "warning", "progress": 44 },
                                    { "name": "docs", "state": "success", "progress": 100 }
                                ]

                                Rectangle {
                                    width: parent.width
                                    height: 48
                                    color: index % 2 === 0 ? Enums.tableBgColor : Enums.alternateRowColor

                                    Row {
                                        anchors.fill: parent
                                        anchors.leftMargin: Enums.spacing.l
                                        anchors.rightMargin: Enums.spacing.l
                                        spacing: Enums.spacing.l

                                        Text {
                                            width: 180
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.name
                                            font.pixelSize: Enums.typography.body
                                            color: Enums.textColor.primary
                                            font.family: Enums.fontFamily
                                        }

                                        Text {
                                            width: 90
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.state
                                            font.pixelSize: Enums.typography.caption
                                            color: Enums.statusLevel.getColor(modelData.state)
                                            font.family: Enums.fontFamily
                                        }

                                        Progress {
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: 180
                                            type: Enums.progress.type_bar
                                            value: modelData.progress
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
