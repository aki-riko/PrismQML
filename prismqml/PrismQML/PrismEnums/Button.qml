// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Button - Button enum constants 按钮枚举常量
// For: Button 适用于
// Note: type is auto-detected by icon/text content 类型根据图标/文本自动识别
QtObject {
    property bool isTicket: false

    // Styles 样式风格
    readonly property int style_default: 0
    readonly property int style_primary: 1
    readonly property int style_transparent: 2
    readonly property int style_filled: 3
    readonly property int style_text: 4
    readonly property int style_hyperlink: 5
    readonly property int style_gradient: 6
    readonly property int style_glow: 7
    
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
    readonly property real gradientLighten: isTicket ? 1.0 : 1.2 // Gradient lighten factor 渐变变亮系数
    
    // Color factors 颜色系数
    readonly property real hoverLighten: 1.3        // Hover state lighten factor 悬浮状态变亮系数

    // Bloom glow tokens 泛光令牌
    // A glow button keeps the accent fill of style_primary and rings it with a soft
    // bloom drawn by one RectangularShadow: Qt 6.9+ renders it from a signed-distance
    // field with no offscreen layer, which is the repo's mandated first choice for
    // rectangular surfaces (AGENTS.md 6.2) and the only variant with a genuinely
    // smooth falloff on a real display.
    // 泛光按钮沿用 style_primary 的主色填充，外圈由单个 RectangularShadow 绘制柔和
    // 泛光：Qt 6.9+ 用有符号距离场渲染且无离屏图层，这是仓库对矩形表面规定的首选方案
    // （AGENTS.md 6.2），也是真实显示器上唯一真正平滑的变体。
    // Ticket paper has zero elevation by design, so the bloom collapses there and
    // the style degrades to its accent face. 票据纸面按设计零悬浮, 因此泛光在票据
    // 皮肤下收敛为纯主色面。
    readonly property real glowSpread: isTicket ? 0 : 8   // Outermost growth beyond the face 超出按钮面的最外层外扩量
    readonly property real glowBlur: isTicket ? 0 : 24    // SDF falloff width 光晕衰减宽度
    // Resting halo alpha. Hover opens it, press pulls it in, disabled keeps an ember;
    // all three are multipliers on this single token.
    // 静息光晕 alpha。悬浮发散, 按压收敛, 禁用保留余辉; 三者都是对该令牌的倍数。
    readonly property real glowHaloAlpha: isTicket ? 0 : 0.38
    readonly property real glowPulseMin: 0.72       // Breathing floor 呼吸下限
    readonly property real glowPulseMax: 1.0        // Breathing ceiling 呼吸上限
    readonly property int glowBreatheDuration: 1700 // Half-cycle duration 呼吸半程时长
    readonly property real glowHoverStrength: 1.3   // Hover multiplier 悬浮强度倍数
    readonly property real glowPressedStrength: 0.85 // Press multiplier 按压强度倍数
    // A disabled or loading face keeps a faint static bloom instead of dropping to
    // nothing, so state changes read as the light dimming rather than the halo
    // popping in and out. 禁用或加载中的按钮面保留微弱静态泛光而不是完全消失, 使状态
    // 切换读作"灯光变暗"而非光晕突兀闪现。
    readonly property real glowDisabledStrength: 0.3 // Disabled/loading multiplier 禁用与加载强度倍数

    // Hyperlink visited state 超链接已访问态
    // Only consumed while a hyperlink button is marked visited; the unvisited
    // path keeps using the accent color unchanged.
    // 仅在超链接按钮被标记为已访问时消费；未访问路径继续使用主题强调色，行为不变。
    readonly property color hyperlinkVisitedLight: "#8b2fa0"  // Visited link (light) 已访问链接(浅色)
    readonly property color hyperlinkVisitedDark: "#c586c0"   // Visited link (dark) 已访问链接(深色)
}
