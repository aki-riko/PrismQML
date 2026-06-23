// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// ColorPicker - Color picker type enums 颜色选择器类型枚举
QtObject {
    // Type 类型
    readonly property int type_dialog: 0       // Full dialog 完整对话框模式 完整对话框
    readonly property int type_palette: 1      // Theme/standard color grid 主题/标准色网格
    readonly property int type_picker: 2       // Full picker dropdown 完整选择器下拉
    readonly property int type_circle: 3       // Circle color buttons 圆形颜色按钮
    readonly property int type_screen: 4       // Screen eyedropper 屏幕取色器
    // Color mode 颜色模式
    readonly property int mode_rgb: 0          // RGB mode RGB模式
    readonly property int mode_hsv: 1          // HSV mode HSV模式
    readonly property int mode_hsl: 2          // HSL mode HSL模式
}
