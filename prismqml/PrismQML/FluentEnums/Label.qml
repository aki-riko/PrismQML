// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Label - Label type enum constants 标签类型枚举常量
// For: Label component 适用于统一标签组件
QtObject {
    // Types 类型
    readonly property int type_body: 0           // Body text 正文 (14px)
    readonly property int type_body_strong: 1    // Strong body text 加粗正文 (14px bold)
    readonly property int type_body_small: 2     // Small body text 小正文 (13px)
    readonly property int type_caption: 3        // Caption text 说明文本 (12px)
    readonly property int type_subtitle: 4       // Subtitle 副标题 (16px)
    readonly property int type_title: 5          // Title 标题 (18px)
    readonly property int type_title_large: 6    // Large title 大标题 (20px)
    readonly property int type_display: 7        // Display text 展示文本 (24px)
    readonly property int type_hyperlink: 8      // Hyperlink 超链接
}
