// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../data/Label"

// ToggleSubtitleContent - Subtitle content (title + subtitle) 副标题内容
// Internal module for Toggle Toggle内部模块
Column {
    id: content

    // ==================== Props 属性 ====================
    property string text: ""
    property string subtitle: ""
    property color textColor: Enums.foregroundColor

    // ==================== Layout 布局 ====================
    spacing: Enums.spacing.xxs

    // Title 标题
    Label {
        type: Enums.label.type_body
        text: content.text
        color: content.textColor
        visible: content.text !== ""
    }

    // Subtitle 副标题
    Label {
        type: Enums.label.type_caption
        text: content.subtitle
        visible: content.subtitle !== ""
    }
}
