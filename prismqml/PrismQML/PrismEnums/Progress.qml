// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Progress - Progress type enums 进度条类型枚举
QtObject {
    readonly property int type_bar: 0           // Bar 条形进度条
    readonly property int type_bar_filled: 1    // Filled bar with text 填充条形（带百分比）
    readonly property int type_ring: 2          // Ring 环形进度条

    readonly property int indeterminate_style_pulse: 0     // Pulsing arc 伸缩圆弧
    readonly property int indeterminate_style_fixed_arc: 1 // Fixed rotating arc 固定旋转圆弧
    readonly property int indeterminate_style_orbit_dot: 2 // Orbiting dot 绕圈圆点
}
