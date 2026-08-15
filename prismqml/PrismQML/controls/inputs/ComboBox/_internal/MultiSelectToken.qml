// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../buttons"
import "../../../data"

// MultiSelectToken - Reusable token tag for multi-select components 多选组件复用的标签
// Used by ComboBoxMulti and ComboBoxMultiTree 被ComboBoxMulti和ComboBoxMultiTree使用
Rectangle {
    id: token
    
    // ==================== Required Props 必需属性 ====================
    required property string text
    required property int tokenIndex

    // ==================== Public Props 公开属性 ====================
    // Per-token outline override. Empty/transparent → keep default accent border. 描边覆盖,空则走默认强调色边框
    // Only TagLineEdit passes this; ComboBoxMulti/Tree leave it unset (zero impact). 仅TagLineEdit传入,ComboBox不传零影响
    property string borderColorOverride: ""
    property bool selected: false  // Keyboard selection state 键盘选中状态

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _outlined: borderColorOverride !== "" && borderColorOverride !== "transparent"
    readonly property color _tokenBackgroundColor: selected
        ? Enums.stateColor.selected
        : (_outlined ? Enums.transparent : Enums.stateColor.accentLight)
    readonly property color _tokenBorderColor: selected
        ? Enums.accentColor
        : (_outlined ? borderColorOverride : Enums.stateColor.accentBorder)

    // ==================== Signals 信号 ====================
    signal removeClicked(int tokenIndex)

    // ==================== Size 尺寸 ====================
    height: Enums.spacing.xxxl
    width: contentRow.implicitWidth + Enums.spacing.m * 2

    // Visual style 视觉样式
    radius: Enums.surfaceRadius(Enums.radius.small)
    color: token._tokenBackgroundColor
    border.width: Enums.border.thin
    border.color: token._tokenBorderColor

    // ==================== Content 内容 ====================
    Row {
        id: contentRow

        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.xs

        // Text 文本
        Label {
            id: tagText
            type: Enums.label.type_caption
            text: token.text
            color: Enums.accentColor
            anchors.verticalCenter: parent.verticalCenter
        }

        // Remove button 删除按钮
        CloseButton {
            size: Enums.typography.body
            iconSizeValue: Enums.iconSize.tiny
            normalIconColor: Enums.accentColor
            hoverIconColor: Enums.accentColor
            hoverBgColor: Enums.stateColor.chipCloseHover
            pressedBgColor: Enums.stateColor.chipClosePressed
            anchors.verticalCenter: parent.verticalCenter
            onClicked: token.removeClicked(token.tokenIndex)
        }
    }
}
