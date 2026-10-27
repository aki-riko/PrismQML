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
    // bloom. The bloom is stacked translucent rounded rectangles, not a shader
    // blur: on a real D3D11 window both RectangularShadow and MultiEffect blur drew
    // nothing for this surface, while the layered discs are visible. StepperHalo
    // already uses the same technique.
    // 泛光按钮沿用 style_primary 的主色填充，并在外圈加一层柔和泛光。泛光由多层
    // 半透明圆角矩形叠加，而不是着色器模糊：真实 D3D11 窗口上该表面上的
    // RectangularShadow 与 MultiEffect 模糊均无绘制，而分层圆盘可见。
    // StepperHalo 已采用同一技术。
    readonly property int glowLayerCount: 12        // Stacked halo discs 叠加光晕层数
    // Ticket paper has zero elevation by design, so the bloom collapses there and
    // the style degrades to its accent face. 票据纸面按设计零悬浮, 因此泛光在票据
    // 皮肤下收敛为纯主色面。
    readonly property real glowSpread: isTicket ? 0 : 20  // Outermost growth beyond the face 超出按钮面的最外层外扩量
    // Calibrated on a real D3D11 window by measuring the painted horizontal falloff
    // of five candidate parameter sets (peak contrast, maximum per-pixel step and
    // step mean): this set spread the bloom widest (20 px) with the smallest mean
    // step (3.4 levels), so the banding StepperHalo avoided does not reappear here.
    // 在真实 D3D11 窗口上量测五组候选参数的实际横向衰减(峰值对比度、逐像素最大步进
    // 与平均步进): 该组外扩最宽(20 像素)且平均步进最小(3.4 级), 因此 StepperHalo
    // 曾规避的可见色带不会在这里复现。
    readonly property real glowLayerOpacity: isTicket ? 0 : 0.05  // Single disc opacity at rest 单层圆盘静息不透明度
    readonly property real glowLayerFalloff: 0.08   // Per-layer opacity decay outwards 由内向外逐层不透明度衰减
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
