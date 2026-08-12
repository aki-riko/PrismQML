// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../../effects"
import "../data"

// PinInput - Fluent Design PIN input PIN码输入框
// Features: hover state, focus line, current cell highlight 悬浮状态/聚焦线/当前格高亮
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int length: Enums.input.pinDefaultLength
    property string value: ""
    property bool password: true

    // ==================== Readonly State 只读状态 ====================
    readonly property bool focused: pinInput.activeFocus
    readonly property int _cellRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property int _cellBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)

    // ==================== Signals 信号 ====================
    signal completed(string pin)
    signal valueModified(string pin)

    // ==================== Public Methods 公开方法 ====================
    function clear() {
        pinInput.text = ""
        control.value = ""
    }

    function setFocus() {
        pinInput.forceActiveFocus()
    }

    function text() { return value }

    // Set echo mode (password) 设置回显模式
    function setEchoMode(mode) { password = (mode !== Enums.input.pinEchoModeNormal) }

    function isEnabled() { return enabled }

    // ==================== Size 尺寸 ====================
    implicitWidth: length * Enums.controlSize.pinBoxCellSize + (length - 1) * Enums.spacing.m
    implicitHeight: Enums.controlSize.pinBoxCellSize

    // ==================== Content 内容 ====================
    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.m

        Repeater {
            model: control.length

            Item {
                id: cellItem
                // Cell state 单元格状态
                property bool hasValue: index < control.value.length
                property bool isCurrentCell: control.focused && index === control.value.length
                property bool hovered: cellMouseArea.containsMouse

                width: Enums.controlSize.pinBoxCellSize
                height: Enums.controlSize.pinBoxCellSize

                // Shadow 阴影
                // Fluent: 模糊阴影; neo: 硬阴影
                RectangularShadow {
                    anchors.fill: pinCell
                    radius: pinCell.radius
                    color: Enums.shadow.level2.color
                    blur: Enums.shadow.level2.blur
                    offset.x: Enums.spacing.none
                    offset.y: Enums.shadow.level2.offset
                    visible: Enums.usesSoftElevation
                }

                NeoShadow {
                    target: pinCell
                    visible: Enums.isNeobrutalism
                    z: pinCell.z - 1
                }

                Rectangle {
                    id: pinCell
                    anchors.fill: parent
                    radius: control._cellRadius

                    // Fluent Design: default/hover/current cell states 默认/悬浮/当前格状态
                    color: {
                        if (!control.enabled) return Enums.stateColor.controlBgDisabled
                        if (cellItem.isCurrentCell) return Enums.cardColor
                        if (cellItem.hovered) return Enums.stateColor.controlBgHover
                        return Enums.stateColor.controlBg
                    }

                    border.width: control._cellBorderWidth
                    border.color: {
                        if (Enums.hasOutlinedSurfaces) return cellItem.isCurrentCell ? Enums.accentColor : Enums.stateColor.border
                        if (!control.enabled) return Enums.stateColor.borderLight
                        if (cellItem.hovered) return Enums.stateColor.borderStrong
                        return Enums.stateColor.inputBorderNormal
                    }

                    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    Behavior on border.color { ColorAnimation { duration: Enums.duration.fast } }

                    // Display content 显示内容
                    Label {
                        anchors.centerIn: parent
                        type: control.password ? Enums.label.type_title : Enums.label.type_subtitle
                        text: cellItem.hasValue ? (control.password ? Enums.input.pinMaskCharacter : control.value.charAt(index)) : ""
                        color: control.enabled ? Enums.textColor.primary : Enums.textColor.disabled
                    }

                    // Cursor (only in current cell) 光标（仅当前格）
                    Rectangle {
                        id: cursor
                        anchors.centerIn: parent
                        width: Enums.border.medium
                        height: Enums.spacing.xxl
                        color: Enums.accentColor
                        visible: cellItem.isCurrentCell
                        opacity: Enums.opacityLevel.visible

                        SequentialAnimation on opacity {
                            running: cellItem.isCurrentCell
                            loops: Animation.Infinite
                            NumberAnimation { to: Enums.opacityLevel.invisible; duration: Enums.duration.slower }
                            NumberAnimation { to: Enums.opacityLevel.visible; duration: Enums.duration.slower }
                        }
                    }

                    // Focus line (Fluent Design) 聚焦底线
                    FocusLine {
                        showLine: cellItem.isCurrentCell
                        parentRadius: pinCell.radius
                    }
                }

                // Per-cell hover detection 单元格悬浮检测
                MouseArea {
                    id: cellMouseArea
                    anchors.fill: parent
                    hoverEnabled: control.enabled
                    onClicked: pinInput.forceActiveFocus()
                }
            }
        }
    }

    // Hidden input 隐藏输入框
    TextInput {
        id: pinInput
        width: Enums.border.thin
        height: Enums.border.thin
        opacity: Enums.opacityLevel.invisible
        maximumLength: control.length
        inputMethodHints: Qt.ImhDigitsOnly
        enabled: control.enabled

        onTextChanged: {
            control.value = text
            control.valueModified(text)
            if (text.length === control.length) {
                control.completed(text)
            }
        }
    }
}
