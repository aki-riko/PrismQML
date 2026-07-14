// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// PrismStateWall - Prism Design state evidence wall Prism Design状态证据墙
ExampleCard {
    id: control

    // ==================== Internal Props 内部属性 ====================
    readonly property string stateEvidenceKeys: "normal|hover|pressed|focused|disabled|selected|error|success|loading"
    readonly property int _sampleWidth: Enums.controlSize.inputDefaultWidth
    readonly property int _compactWidth: Enums.controlSize.inputDefaultWidth - Enums.spacing.xl
    readonly property int _swatchWidth: Enums.controlSize.inputDefaultWidth - Enums.spacing.xxxl
    readonly property int _swatchHeight: Enums.controlSize.inputHeight

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : 0

    // ==================== Content 内容 ====================
    title: "State Wall"
    description: "真实控件与状态层并排覆盖 normal、hover、pressed、focused、disabled、selected、error、success、loading。"
    orientation: Qt.Vertical

    component StateSwatch: Rectangle {
        id: swatch

        // ==================== Public Props 公开属性 ====================
        property string label: ""
        property color fillColor: Enums.cardColor
        property color strokeColor: Enums.borderColor
        property int strokeWidth: Enums.border.thin
        property color textColor: Enums.textColor.primary

        // ==================== Size 尺寸 ====================
        width: control._swatchWidth
        height: control._swatchHeight
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
        color: fillColor
        border.width: strokeWidth
        border.color: strokeColor

        // ==================== Content 内容 ====================
        Label {
            anchors.centerIn: parent
            type: Enums.label.type_caption
            text: swatch.label
            color: swatch.textColor
        }
    }

    Column {
        width: parent ? parent.width : 0
        spacing: Enums.spacing.l

        Flow {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.l

            ComponentCard { label: "normal"; Button { text: "Default" } }
            ComponentCard { label: "primary"; Button { style: Enums.button.style_primary; text: "Primary" } }
            ComponentCard { label: "disabled"; Button { text: "Disabled"; enabled: false } }
            ComponentCard { label: "loading"; Button { text: "Deploy"; loading: true; loadingText: "Working" } }

            ComponentCard {
                label: "focused"

                LineEdit {
                    width: control._sampleWidth
                    text: "Focused input"
                    Component.onCompleted: forceActiveFocus()
                }
            }

            ComponentCard {
                label: "selected"

                SegmentedControl {
                    items: ["Normal", "Selected", "Next"]
                    currentIndex: 1
                }
            }
        }

        Flow {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.l

            ComponentCard {
                label: "menu selected"

                Column {
                    width: control._sampleWidth
                    spacing: Enums.spacing.xxs

                    MenuDelegate {
                        width: parent.width
                        text: "Selected item"
                        icon: "Checkmark"
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
                label: "semantic"

                Row {
                    spacing: Enums.spacing.s
                    Tag { text: "Success"; status: Enums.statusLevel.success }
                    Tag { text: "Error"; status: Enums.statusLevel.error }
                }
            }

            ComponentCard {
                label: "feedback"

                InfoBar {
                    width: control._sampleWidth + Enums.spacing.xxl
                    title: "Error"
                    content: "Action required"
                    severity: "error"
                    duration: Enums.duration.persistent
                }
            }
        }

        Flow {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.l

            StateSwatch { label: "hover"; fillColor: Enums.stateColor.hover }
            StateSwatch { label: "pressed"; fillColor: Enums.stateColor.pressed }
            StateSwatch { label: "selected"; fillColor: Enums.stateColor.selected }
            StateSwatch { label: "focused"; fillColor: Enums.transparent; strokeColor: Enums.borderStrongColor; strokeWidth: Enums.prismDesign.focusBorderWidth }
            StateSwatch { label: "disabled"; fillColor: Enums.disabledColor; textColor: Enums.textColor.disabled }
            StateSwatch { label: "error"; fillColor: Enums.statusLevel.getBgColor("error"); textColor: Enums.statusLevel.getColor("error") }
        }
    }
}
