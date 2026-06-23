// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Flyout - Flyout animation type enums 弹出层动画类型枚举
QtObject {
    readonly property int none: 0        // No animation 无动画(默认)
    readonly property int fadeIn: 1      // Fade in 淡入
    readonly property int pullUp: 2      // Pull up 上拉
    readonly property int dropDown: 3    // Drop down 下拉
    readonly property int slideLeft: 4   // Slide left 左滑
    readonly property int slideRight: 5  // Slide right 右滑
}
