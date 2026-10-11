// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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

    // ==================== AppBar Display State 应用栏显示状态 ====================
    // WinUI AppBar semantics shared by RibbonBar and the AppBar button family.
    // WinUI 应用栏语义, 由功能区与 AppBar 按钮族共用。
    // No local choice: follow the nearest display-state host 未指定: 跟随最近的显示状态宿主
    readonly property int appBar_inherit: 0
    // Pinned open: labels stay visible even when the host bar collapses 固定展开: 宿主折叠时标签仍常显
    readonly property int appBar_sticky: 1
    // Icon-only presentation 紧凑: 只呈现图标
    readonly property int appBar_compact: 2
    // Labels visible, may collapse 展开: 标签可见, 允许折叠
    readonly property int appBar_expanded: 3
}
