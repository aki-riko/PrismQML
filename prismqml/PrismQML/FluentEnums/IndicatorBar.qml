// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// IndicatorBar - Indicator bar enum constants 指示器条枚举常量
// For: IndicatorBar component 适用于 IndicatorBar 组件
QtObject {
    // ==================== Color Style 颜色样式 ====================
    readonly property int style_solid: 0       // Solid color 纯色
    readonly property int style_gradient: 1    // Gradient 渐变

    // ==================== Animation Type 动画类型 ====================
    readonly property int animation_normal: 0  // Smooth easing (OutCubic) 平滑缓动
    readonly property int animation_bounce: 1  // Elastic back (OutBack) 弹性回弹

    // ==================== Orientation 方向 ====================
    readonly property int orientation_vertical: 0    // Vertical 竖向
    readonly property int orientation_horizontal: 1  // Horizontal 横向
}
