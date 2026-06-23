// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Input - Input field type enums 输入框类型枚举
QtObject {
    // Style 样式
    readonly property int style_default: 0
    readonly property int style_filled: 1
    readonly property int style_borderless: 2
    // Type 类型
    readonly property int type_normal: 0
    readonly property int type_password: 1
    readonly property int type_search: 2
    readonly property int type_tag: 3
    readonly property int type_label: 4
    readonly property int type_date: 5
    readonly property int type_time: 6
    readonly property int type_datetime: 7
    // Multiline 多行
    readonly property int multiline_plain: 0     // Plain text editable 纯文本可编辑
    readonly property int multiline_browser: 1   // Read-only rich text browser 只读富文本浏览器
    // SpinBox types SpinBox类型
    readonly property int spinbox_normal: 10
    readonly property int spinbox_double: 11
    readonly property int spinbox_compact: 12
    readonly property int spinbox_compact_double: 13
}
