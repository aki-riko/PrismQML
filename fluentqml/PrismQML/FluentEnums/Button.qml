// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Button - Button enum constants 按钮枚举常量
// For: Button 适用于
// Note: type is auto-detected by icon/text content 类型根据图标/文本自动识别
QtObject {
    // Styles 样式风格
    readonly property int style_default: 0
    readonly property int style_primary: 1
    readonly property int style_transparent: 2
    readonly property int style_filled: 3
    readonly property int style_text: 4
    readonly property int style_hyperlink: 5
    readonly property int style_gradient: 6
    
    // Shapes 外观形状
    readonly property int shape_default: 0
    readonly property int shape_pill: 1
    
    // Features 功能扩展
    readonly property int feature_none: 0
    readonly property int feature_progress_bar: 1
    readonly property int feature_progress_ring: 2
    readonly property int feature_indeterminate_bar: 3
    readonly property int feature_indeterminate_ring: 4
    readonly property int feature_toggle: 5
    readonly property int feature_dropdown: 6
    readonly property int feature_split: 7
    readonly property int feature_countdown: 8
    
    // Content alignment 内容对齐
    readonly property int align_center: 0           // Center alignment 居中对齐
    readonly property int align_left: 1             // Left alignment 左对齐
    readonly property int align_right: 2            // Right alignment 右对齐
    
    // Countdown defaults 倒计时默认值
    readonly property int countdownDefault: 60      // Default countdown seconds 默认倒计时秒数
    readonly property string countdownSuffix: "s"   // Countdown suffix text 倒计时后缀文本
    
    // Gradient positions 渐变位置
    readonly property real gradientStart: 0.0       // Gradient start position 渐变起始位置
    readonly property real gradientEnd: 1.0         // Gradient end position 渐变结束位置
    readonly property real gradientLighten: 1.2     // Gradient lighten factor 渐变变亮系数
    
    // Color factors 颜色系数
    readonly property real hoverLighten: 1.3        // Hover state lighten factor 悬浮状态变亮系数
}
