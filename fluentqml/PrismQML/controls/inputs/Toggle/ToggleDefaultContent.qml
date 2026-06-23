// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data/Label"

// ToggleDefaultContent - Default content (icon + text) 默认内容
// Internal module for Toggle Toggle内部模块
Row {
    id: content

    // ==================== Props 属性 ====================
    property string text: ""
    property string icon: ""
    property int iconSize: Enums.iconSize.m
    property color textColor: Enums.foregroundColor
    property bool showIcon: true

    // ==================== Layout 布局 ====================
    spacing: icon !== "" && showIcon ? Enums.spacing.s : 0

    // Icon 图标
    Loader {
        active: content.icon !== "" && content.showIcon
        anchors.verticalCenter: parent.verticalCenter
        sourceComponent: Icon {
            icon: content.icon
            iconSize: content.iconSize
            color: content.textColor
        }
    }

    // Text 文本
    Label {
        type: Enums.label.type_body
        text: content.text
        color: content.textColor
        anchors.verticalCenter: parent.verticalCenter
        visible: content.text !== ""
    }
}
