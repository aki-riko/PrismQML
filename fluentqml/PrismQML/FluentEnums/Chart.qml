// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Chart - Chart type and orientation enums 图表类型和方向枚举
QtObject {
    // ==================== Chart Types 图表类型 ====================
    readonly property int type_bar: 0
    readonly property int type_line: 1
    readonly property int type_pie: 2
    readonly property int type_scatter: 3
    readonly property int type_radar: 4
    readonly property int type_boxplot: 5    // Boxplot 箱线图
    
    // ==================== Bar Orientation 柱状图方向 ====================
    readonly property int orientation_vertical: 0    // Vertical bars 垂直柱状图
    readonly property int orientation_horizontal: 1  // Horizontal bars 水平柱状图
}
