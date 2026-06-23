// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../../data/Label"

// KeyTag - Single key tag for ShortcutEditor 快捷键标签组件
// Extracted from ShortcutEditor for modularity 从ShortcutEditor提取以模块化
Rectangle {
    id: keyTag
    
    // ==================== Required Props 必需属性 ====================
    required property string keyText  // Key text 按键文本
    
    width: tagText.implicitWidth + Enums.spacing.l * 2
    height: 26
    radius: Enums.radius.small
    color: Enums.stateColor.accentLight
    border.width: Enums.border.thin
    border.color: Enums.stateColor.accentBorder
    
    Label {
        id: tagText
        type: Enums.label.type_caption
        anchors.centerIn: parent
        text: keyTag.keyText
        font.weight: Font.Medium
        color: Enums.accentColor
    }
}
