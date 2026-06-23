// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// CommandBar - Command bar enums 命令栏枚举
QtObject {
    id: root
    
    // ==================== Type 类型 ====================
    readonly property int type_default: 0    // Default transparent style 默认透明样式
    readonly property int type_view: 1       // Card view style with shadow 卡片视图样式（带阴影）
    
    // ==================== ButtonStyle 按钮样式 ====================
    readonly property int style_icon_only: 0       // Icon only 仅图标
    readonly property int style_text_beside: 1     // Text beside icon 文字在图标旁
    readonly property int style_text_under: 2      // Text under icon 文字在图标下
}
