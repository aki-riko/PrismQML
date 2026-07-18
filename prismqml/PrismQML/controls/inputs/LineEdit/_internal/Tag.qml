// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../ComboBox/_internal"

// Tag - Tag component for TagLineEdit 标签组件
// Wrapper around MultiSelectToken for TagLineEdit specific logic 包装MultiSelectToken用于TagLineEdit特定逻辑
MultiSelectToken {
    id: tag

    // ==================== Required Props 必需属性 ====================
    required property int index        // Tag index 标签索引
    required property var modelData    // Tag text 标签文本
    required property var tagControl   // Parent TagLineEdit 父控件

    // ==================== Public Props 公开属性 ====================
    property string tagColor: ""       // Per-tag outline color, empty = default accent border 按标签描边,空=默认强调色边框

    // Bind to MultiSelectToken 绑定到 MultiSelectToken
    text: modelData
    tokenIndex: index
    borderColorOverride: tagColor      // Forward outline to token 透传描边颜色

    // Handle token removal 处理标签删除
    onRemoveClicked: (idx) => {
        var ctrl = tag.tagControl
        if (!ctrl || !ctrl.tags) return
        var removed = ctrl.tags[idx]
        var newTags = ctrl.tags.slice()
        newTags.splice(idx, 1)
        ctrl.tags = newTags
        ctrl.tagsModified(ctrl.tags)
        ctrl.tagRemoved(idx, removed)
    }
}
