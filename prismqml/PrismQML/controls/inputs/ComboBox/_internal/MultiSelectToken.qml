// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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

    // ==================== Optional Props 可选属性 ====================
    // Per-token tint override. Empty/transparent → keep default accent look. 着色覆盖,空则走默认强调色
    // Only TagLineEdit passes this; ComboBoxMulti/Tree leave it unset (zero impact). 仅TagLineEdit传入,ComboBox不传零影响
    property string bgColorOverride: ""
    readonly property bool _tinted: bgColorOverride !== "" && bgColorOverride !== "transparent"
    // Foreground picked for contrast against the tint 文字色按对比度选黑/白
    readonly property color _tintFg: _tinted ? (Qt.color(bgColorOverride).hslLightness > 0.6 ? "#000000" : "#ffffff")
                                              : Enums.accentColor

    // ==================== Signals 信号 ====================
    signal removeClicked(int tokenIndex)

    // ==================== Size 尺寸 ====================
    height: Enums.spacing.xxxl
    width: tagText.implicitWidth + Enums.spacing.xxxl

    // ==================== Style 样式 ====================
    radius: Enums.radius.small
    color: token._tinted ? token.bgColorOverride : Enums.stateColor.accentLight
    border.width: Enums.border.thin
    border.color: token._tinted ? Qt.darker(token.bgColorOverride, 1.2) : Enums.stateColor.accentBorder

    // ==================== Content 内容 ====================
    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.xs

        // Text 文本
        Label {
            id: tagText
            type: Enums.label.type_caption
            text: token.text
            color: token._tintFg
            anchors.verticalCenter: parent.verticalCenter
        }

        // Remove button 删除按钮
        CloseButton {
            size: Enums.typography.body
            iconSizeValue: Enums.iconSize.tiny
            normalIconColor: token._tintFg
            hoverIconColor: token._tintFg
            hoverBgColor: Enums.stateColor.chipCloseHover
            pressedBgColor: Enums.stateColor.chipClosePressed
            anchors.verticalCenter: parent.verticalCenter
            onClicked: token.removeClicked(token.tokenIndex)
        }
    }
}
