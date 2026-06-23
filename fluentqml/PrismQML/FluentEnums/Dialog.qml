// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Dialog - Dialog dimension constants 对话框尺寸常量
QtObject {
    // Fluent Design MessageBox/Dialog dimensions Fluent Design 对话框尺寸
    readonly property int buttonWidth: 130       // Dialog button width 对话框按钮宽度
    readonly property int buttonHeight: 32       // Dialog button height 对话框按钮高度
    readonly property int actionsRowHeight: 80  // Actions row height 动作按钮区高度 (8px 网格对齐)
    readonly property int minWidth: 288          // Minimum dialog width 最小对话框宽度 (8px 网格对齐)
    readonly property int contentPadding: 48     // Content area padding 内容区域内边距
}
