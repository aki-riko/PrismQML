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

    // Glow 泛光（正交维度，可与任意 style / shape / feature 叠加）
    // Glow is not a fill style: it paints a bloom behind whatever face the style
    // already resolves, so it composes with every style instead of replacing one.
    // 泛光不是填充风格: 它在样式已解析出的按钮面背后绘制光晕, 因此与所有样式叠加
    // 而不是取代其中一种。
    readonly property int glow_none: 0              // No bloom 无泛光
    readonly property int glow_accent: 1            // Face-following bloom 跟随按钮面的泛光
    
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
    // Glow is an orthogonal visual layer, not a fill style: it rings whatever face
    // the current style already resolves, so any style, shape, and feature can be
    // combined with it. The bloom is one RectangularShadow: Qt 6.9+ renders it from
    // a signed-distance field with no offscreen layer, which is the repo's mandated
    // first choice for rectangular surfaces (AGENTS.md 6.2) and the only variant
    // with a genuinely smooth falloff on a real display.
    // 泛光是正交视觉层而不是填充风格: 它在当前 style 已解析出的按钮面外圈绘制,
    // 因此可与任意样式、形状与功能组合。光晕由单个 RectangularShadow 绘制:
    // Qt 6.9+ 用有符号距离场渲染且无离屏图层, 这是仓库对矩形表面规定的首选方案
    // (AGENTS.md 6.2), 也是真实显示器上唯一真正平滑的变体。
    //
    // The bloom is sized as a ratio of the button height, not in absolute pixels: a
    // fixed spread that looks right on a 46 px button swallows a 32 px one. Measured
    // on a real D3D11 window, this ratio puts the visible band at about a quarter of
    // the face height with a peak tint of ~25/255, which reads as a soft rim instead
    // of a halo the size of the button itself.
    // 泛光按按钮高度的比例而不是绝对像素来定尺: 在 46 像素按钮上合适的固定外扩会把
    // 32 像素按钮整个吞掉。真实 D3D11 窗口实测显示, 该比例让可见带约为面高的四分之一,
    // 峰值着色约 25/255, 读作柔和描边而不是一个和按钮一样大的光团。
    readonly property real glowBlurRatio: 0.45       // Falloff width as a share of the button height 衰减宽度占按钮高度的比例
    readonly property real glowSpreadRatio: 0.10     // Outward growth as a share of the button height 外扩占按钮高度的比例
    // Every skin that forbids soft elevation reports zero, so the halo is not built
    // at all: ticket paper is square and shadowless by design.
    // 任何禁止柔和悬浮的皮肤都报零, 因此光晕根本不会被创建: 票据纸面按设计是直角无阴影。
    readonly property real glowSpread: isTicket ? 0 : glowSpreadRatio
    readonly property real glowBlur: isTicket ? 0 : glowBlurRatio
    // Resting halo alpha. Hover opens it, press pulls it in, disabled keeps an ember;
    // all three are multipliers on this single token.
    // 静息光晕 alpha。悬浮发散, 按压收敛, 禁用保留余辉; 三者都是对该令牌的倍数。
    readonly property real glowHaloAlpha: isTicket ? 0 : 0.26
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
